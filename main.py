import base64
import os
import cv2
import yt_dlp
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# --- 1. YouTubeから「指定範囲」の複数画像を切り出す関数 ---
def capture_youtube_frames_range(youtube_url, start_sec, end_sec, interval_sec=2):
    print("YouTubeの動画情報を取得中...")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android']
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=False)
        video_url = info_dict.get("url", None)

    if not video_url:
        raise Exception("動画のデータURLが取得できませんでした。")

    print(f"動画の {start_sec} 秒から {end_sec} 秒までの範囲を解析中...")
    cap = cv2.VideoCapture(video_url)

    captured_paths = []
    # 指定された範囲を指定秒刻みで切り出す
    for t in range(start_sec, end_sec + 1, interval_sec):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ret, frame = cap.read()
        if ret:
            path = f"frame_{t}s.jpg"
            cv2.imwrite(path, frame)
            captured_paths.append(path)
            print(f"画像を保存しました: {path}")
        else:
            print(f"{t}秒地点の画像抽出に失敗、または動画終了位置です。")
            break

    cap.release()
    if not captured_paths:
        raise Exception("画像の切り出しに1枚も成功しませんでした。")
    return captured_paths

# --- 2. 画像をbase64にエンコードする関数 ---
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# --- メイン処理 ---
YOUTUBE_URL = "https://www.youtube.com/watch?v=DtzIyXc56f4"

START_TIME_SEC = 5480
END_TIME_SEC = 5490

try:
    # 1. 指定範囲の連続画像を切り出す
    image_paths = capture_youtube_frames_range(YOUTUBE_URL, START_TIME_SEC, END_TIME_SEC, interval_sec=2)

    # 2. すべての画像をbase64にエンコードし、API送信用リストに変換
    image_contents = []
    for path in image_paths:
        base64_img = encode_image(path)
        image_contents.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
        })

    # 3. OpenAI APIクライアント初期化（環境変数から自動読み込み）
    # 3. OpenAI APIクライアント初期化
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception(".envファイルからOPENAI_API_KEYが読み込めていません。キーを確認してください。")
    client = OpenAI(api_key=api_key)

    print("OpenAIに実況・解説をリクエスト中...")

    # 4. プロンプト
    prompt_text = (
        "# 指示\n"
        "あなたは戦術分析に定評があり、ピッチ全体を完全に俯瞰（引きの視点）して両チームのシステム配置や守備ブロック、ポジショニングの噛み合わせを論理的に説明するプロのサッカー解説者（戦術アナリスト）です。\n"
        "提供される複数枚の画像は、指定された時間範囲内における「連続した一連の流れ（動画のコマ）」を捉えたものです。\n"
        "これらの連続した視覚情報とメンバーリストから、ピッチ全体の『フォーメーションの構造的噛み合わせ』『陣形全体のコンパクトさやライン設定』『攻守の切り替え（トランジション）に伴う全体配置のズレ』を正確に読み取り、論理的で臨場感のある戦術解説を出力してください。\n \n"
        "# 重要ルール：時間表現の変換\n"
        "入力された経過時間（秒・分）を、解説の中でそのまま数字として読み上げることは【厳禁】です。\n"
        "代わりに、試合の局面や戦術的な時間帯に合わせた自然なフレーズに変換して解説に織り込んでください。\n\n"
        "# 厳格な戦術分析ルール（引きの視点・俯瞰戦術の義務化）\n"
        "1. 【フォーメーションの噛み合わせと変化の描写】:\n"
        "   後半から日本が選手交代（堂安などの投入）を経て、配置をどう変更したか（基本システム3-4-3、守備時5-4-1）を解説のベースにしてください。\n"
        "2. 【コンパクトさとラインの押し引き】:\n"
        "   日本がマークの受け渡しを行ってファーストディフェンダーがプレスを発動した際、中盤やDFラインがどう連動してコンパクトさを維持しているかに焦点を当ててください。\n"
        "3. 【2段構えのトランジションの全貌】:\n"
        "   クリアボールの競り合いからこぼれ球を回収し、ポジショニングのズレへと繋がったプロセスを論理的に整理してください。\n"
        "4. 【ハルシネーションの排除】:\n"
        "   システムは日本の5-4-1（3-4-3）を基本とし、勝手なシステム変更を名乗らないこと。\n \n"
        "# 出力ルール\n"
        "ピッチ全体を俯瞰した論理的な戦術解説を **3〜4文程度** で出力してください。\n \n"
        "# 前提情報\n"
        "対象試合：2022年 FIFAワールドカップ グループE 「日本 対 スペイン」\n"
    )

    messages_content = [{"type": "text", "text": prompt_text}] + image_contents

    # 5. チャットの応答を生成
    response = client.chat.completions.create(
        model="gpt-4o",  
        messages=[
            {
                "role": "user",
                "content": messages_content,
            }
        ],
        max_tokens=1000,
    )

    print("\n=== 連続画像分析による戦術解説 ===")
    print(response.choices[0].message.content)

    # クリーンアップ
    for path in image_paths:
        if os.path.exists(path):
            os.remove(path)

except Exception as e:
    print(f"\nエラーが発生しました: {e}")