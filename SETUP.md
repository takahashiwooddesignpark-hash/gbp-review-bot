# GBP口コミ監視Bot セットアップガイド

## ファイル構成

```
gbp_review_bot/
├── main.py                  # エントリーポイント
├── gbp_client.py            # Google Business Profile API
├── lineworks_client.py      # LINE WORKS Bot API
├── storage.py               # 既読レビューIDの永続化
├── requirements.txt
├── .env                     # 認証情報（要作成）
├── .env.example             # テンプレート
├── token.json               # GCP OAuthトークン（初回認証後に自動生成）
├── lineworks_private_key.pem # LINE WORKSの秘密鍵（要配置）
└── seen_reviews.json        # 既読レビューID（自動生成）
```

---

## Step 1: Google Cloud Platform の設定

### 1-1. GCPプロジェクト作成・APIの有効化

1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクトを作成（または既存プロジェクトを選択）
3. 左メニュー「APIとサービス」→「ライブラリ」を開く
4. 以下のAPIを検索して **有効化**:
   - `My Business Reviews API`
   - `My Business Account Management API`

### 1-2. OAuth 2.0 クライアントIDの作成

1. 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuthクライアントID」
2. アプリケーションの種類: **デスクトップアプリ**
3. 作成後に表示される `クライアントID` と `クライアントシークレット` をメモ

### 1-3. ビジネスロケーションIDの確認

1. https://business.google.com/ にアクセス
2. 対象ビジネスを開き、URLから確認するか、以下の方法で取得:

```bash
# アカウント一覧を取得
curl -H "Authorization: Bearer <access_token>" \
  https://mybusinessaccountmanagement.googleapis.com/v1/accounts

# ロケーション一覧を取得
curl -H "Authorization: Bearer <access_token>" \
  https://mybusinessbusinessinformation.googleapis.com/v1/accounts/<ACCOUNT_ID>/locations
```

`GBP_LOCATION_NAME` の形式: `accounts/123456789/locations/987654321`

---

## Step 2: LINE WORKS Bot の設定

### 2-1. LINE WORKS Developer Console でBotを作成

1. https://dev.worksmobile.com/ にアクセス（管理者アカウント必須）
2. 「API」→「Bot」→「追加」
3. Bot名・説明を入力して保存
4. **Bot ID** をメモ

### 2-2. アプリを作成してサービスアカウント認証情報を取得

1. 「API」→「アプリ」→「追加」
2. OAuth Scopeで `bot` にチェック
3. 「サービスアカウント & 認証鍵」タブ:
   - **Client ID** をメモ
   - **Client Secret** をメモ
   - **Service Account** をメモ（例: `xxxx@xxxx`）
   - 「認証鍵登録」→秘密鍵（PEMファイル）をダウンロード

4. ダウンロードした秘密鍵を `lineworks_private_key.pem` としてプロジェクトフォルダに配置

### 2-3. BotをチャンネルまたはグループトークTに追加してChannel IDを取得

1. LINE WORKSアプリでBotをトークルームに招待
2. Channel IDはDeveloper Consoleの「Bot」→対象Bot→「チャンネル」から確認

---

## Step 3: 環境設定

```bash
# .envファイルを作成
cp .env.example .env
```

`.env` を編集して各値を設定:

```env
GCP_CLIENT_ID=1234567890-xxxx.apps.googleusercontent.com
GCP_CLIENT_SECRET=GOCSPX-xxxxxxxx
GBP_LOCATION_NAME=accounts/123456789/locations/987654321

LW_CLIENT_ID=xxxxxxxxxxxxxxxx
LW_CLIENT_SECRET=xxxxxxxxxxxxxxxx
LW_SERVICE_ACCOUNT=xxxxxx@xxxxxx
LW_PRIVATE_KEY_PATH=./lineworks_private_key.pem
LW_BOT_ID=12345678
LW_CHANNEL_ID=xxxxxxxxxxxxxxxx
```

---

## Step 4: インストール・初回実行

```bash
# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 初回実行（ブラウザでGoogle認証が開く）
python main.py
```

初回はブラウザが開くので、対象のGoogleアカウントでログインして許可してください。
認証後 `token.json` が自動生成され、以降は自動でトークンが更新されます。

---

## Step 5: 定期実行の設定

### cron（推奨）

```bash
crontab -e
```

以下を追記（5分おきに実行）:

```cron
*/5 * * * * cd /Users/yuyatakahashi/gbp_review_bot && /Users/yuyatakahashi/gbp_review_bot/venv/bin/python main.py >> /tmp/gbp_bot.log 2>&1
```

### ポーリングモード（常駐プロセス）

```bash
python main.py --loop
```

---

## 通知フォーマット例

```
【新しい口コミが届きました】
日時: 2024-05-21
投稿者: 山田 太郎
評価: ★★★★☆
コメント:
スタッフの対応がとても丁寧でした。また利用したいと思います。
```
