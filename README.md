# やることリスト (Todo List)

Python (Flask) 製のシンプルなTodoリストWebアプリです。データの保存先はGoogleスプレッドシートで、Vercelで公開できます。

## 機能

- やること（タイトル・内容・期日）の登録
- 登録したやることの編集
- 一覧ページでの確認（期日の昇順で表示）

## 事前準備: Googleスプレッドシートの用意

このアプリは「サービスアカウント」という、ブラウザログイン不要で使えるGoogleの認証方式でスプレッドシートに読み書きします。

### 1. GCPプロジェクトの作成とAPI有効化

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセスし、プロジェクトを作成（または既存のものを利用）
2. 「APIとサービス」→「ライブラリ」から以下の2つを有効化する
   - **Google Sheets API**
   - **Google Drive API**

### 2. サービスアカウントの作成とJSON鍵の発行

1. 「APIとサービス」→「認証情報」→「認証情報を作成」→「サービスアカウント」
2. 適当な名前をつけて作成（ロールの設定は不要でOK）
3. 作成したサービスアカウントの詳細画面→「キー」タブ→「鍵を追加」→「新しい鍵を作成」→ JSON を選択してダウンロード
4. ダウンロードしたJSONファイルの中に `"client_email": "xxxx@xxxx.iam.gserviceaccount.com"` という行があるので、このメールアドレスを控えておく

### 3. スプレッドシートの作成と共有

1. Google スプレッドシートで新しいシートを作成する（シート名やタブ名は何でもOK。アプリが自動で `todos` という名前のタブを作成・使用します）
2. スプレッドシートの「共有」から、手順2で控えたサービスアカウントのメールアドレスを **編集者** 権限で追加する
   - **これを忘れると `PERMISSION_DENIED` エラーになります**
3. スプレッドシートのURLから、`/d/` と `/edit` の間の文字列（スプレッドシートID）を控えておく
   ```
   https://docs.google.com/spreadsheets/d/【ここがスプレッドシートID】/edit
   ```

## ローカルでの動作確認

```bash
pip install -r requirements.txt
cp .env.example .env
```

`.env` を開いて以下を設定する:

- `GOOGLE_SERVICE_ACCOUNT_JSON`: ダウンロードしたJSON鍵の中身をそのまま1行の文字列として貼り付け
- `GOOGLE_SHEET_ID`: 控えておいたスプレッドシートID

```bash
python local_run.py
```

ブラウザで http://localhost:5000 を開いて確認する。

## Vercelへのデプロイ

Vercel CLIが未インストールの場合は先にインストールする:

```bash
npm i -g vercel
```

デプロイ手順:

```bash
vercel login
vercel link
vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production
vercel env add GOOGLE_SHEET_ID production
vercel --prod
```

`vercel env add` を実行すると値の入力を求められるので、`.env` に設定したものと同じ値を貼り付ける（`GOOGLE_SERVICE_ACCOUNT_JSON` はJSON全体を1行でそのまま貼り付ければOK）。

## ディレクトリ構成

```
.
├── api/
│   ├── index.py      # Flaskアプリ本体（ルーティング）
│   └── sheets.py      # スプレッドシート読み書き
├── templates/          # HTMLテンプレート
├── static/style.css
├── vercel.json         # Vercelのルーティング・関数設定
├── requirements.txt
├── local_run.py         # ローカル確認用の起動スクリプト
└── .env.example
```

## 今回実装していない機能

- 削除機能・完了チェック機能は今回のご要望（登録・編集・一覧）に含まれていなかったため未実装です。必要であれば追加できます。
