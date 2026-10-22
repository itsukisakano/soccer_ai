# Soccer Tactical Commentary Generator (AI-Powered)

YouTubeの試合映像から特定時間帯のフレームを抽出し、GPT-4o Vision APIを用いてフォーメーションや戦術的配置の連動を解説・実況する自動戦術解説システムです。

## 主な機能
- `yt-dlp` で動画ストリームURLを取得し、ローカルに動画全体をダウンロードすることなく指定区間のフレームを `OpenCV` で直接サンプリング。
- 抽出した連続フレームとフォーメーションの前提知識、選手情報のプロンプトを `GPT-4o` に入力し、ピッチ全体の実況・解説文を生成。
- 2秒間隔（サンプリングレート）でのコマ切り出しにより、APIコストと戦術認識精度のバランスを最適化。

## 技術スタック
- **Language**: Python 3.9+
- **Computer Vision / Stream**: OpenCV (`opencv-python`), `yt-dlp`
- **LLM / Vision API**: OpenAI API (`gpt-4o`)
- **Environment**: macOS, `python-dotenv`

## セットアップ手順

1. リポジトリのクローン
   ```bash
   git clone [https://github.com/itsukisakano/soccer-tactical-ai.git](https://github.com/itsukisakano/soccer-tactical-ai.git)
   cd soccer-tactical-ai