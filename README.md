# Todoリストアプリ

Googleスプレッドシートを使用してデータを保存するTodoリストWebアプリケーションです。

## 機能

- ✅ Todoの登録・編集・削除
- ✅ タイトル・内容・期日の設定
- ✅ Googleスプレッドシートでのデータ保存
- ✅ レスポンシブデザイン
- ✅ 完了ボタンと完了状態の色分け表示
- ✅ 持越し機能（次の日にTodoを移動）
- ✅ 昨日/今日/明日のタブ切り替え
- ✅ カレンダーによる日付選択機能
- ✅ 過去・未来のTodo確認機能
- ✅ 未来のTodoを別シートに自動保存
- ✅ 操作方法ガイドモーダル

## プロジェクト進捗状況

### 実装済み機能

#### 1. 基本的なTodo機能
- ✅ Todoの追加・編集・削除
- ✅ タイトル、内容、期日の設定
- ✅ 期日から自動的に曜日を計算
- ✅ 作成日時の自動記録

#### 2. スプレッドシート連携
- ✅ Googleスプレッドシートへの自動保存
- ✅ スプレッドシートの列構成：
  - ID, タイトル, 内容, 曜日, 期日, 作成日時, 完了日時, 状態, 対象日
- ✅ 過去・今日・昨日・明日のTodo → 1枚目「Todos」シートに保存
- ✅ 明日以降の未来のTodo → 2枚目「Todos_Future」シートに自動保存
- ✅ 空白の1枚目シートの自動削除機能

#### 3. 完了・持越し機能
- ✅ 完了ボタン（今日の画面で表示）
- ✅ 完了済みTodoの色分け表示（緑色、取り消し線）
- ✅ 完了日時の自動記録
- ✅ 持越しボタン（今日の画面で表示）
- ✅ 持越し機能で次の日にTodoを移動

#### 4. 日付管理機能
- ✅ 昨日/今日/明日のタブ切り替え
- ✅ カレンダーによる日付選択
- ✅ 過去・未来の任意の日付でのTodo表示
- ✅ カレンダーでの日付選択時に該当日のTodoを自動表示

#### 5. 操作方法ガイド
- ✅ 操作方法モーダルウィンドウ
- ✅ 基本的な使い方の説明
- ✅ 各機能の詳細説明
- ✅ スプレッドシートの構成説明

#### 6. モバイル対応
- ✅ レスポンシブデザイン
- ✅ モバイル用ハンバーガーメニューボタン（左上に三本線ボタン）
- ✅ モバイルメニューからの機能切り替え
- ✅ モバイル表示時の初期表示をTodoリストのみに設定
- ✅ 操作方法モーダル表示時のハンバーガーメニューボタンの非表示処理
- ✅ モーダルヘッダーのパディング調整（タイトルとハンバーガーメニューの被り防止）

### 最近の修正内容

#### 最新の修正（2024年）

##### モバイル表示の改善
- ✅ モバイル表示時のカレンダー表示処理の改善
  - `showCalendarOnly()`関数の改善
  - `setProperty('display', 'block', 'important')`を使用して確実にカレンダーを表示
  - CSSクラス`.calendar-sidebar.show`に`!important`を追加
- ✅ 操作方法モーダルのヘッダー改善
  - ハンバーガーメニューボタンとタイトルの被りを解消
  - モーダル表示時にハンバーガーメニューボタンを非表示に設定
  - モーダルヘッダーに左側パディング（50px）を追加
- ✅ モバイル表示時の初期表示をTodoリストのみに設定
  - カレンダーは非表示で、Todoリストのみを表示
  - ハンバーガーメニューから選択した機能のみを表示

##### バグ修正
- ✅ 未来のTodo編集時のバグ修正
  - 編集時に新しいTodoが追加される問題を修正
  - ターゲット日付変更時のシート移動処理を実装
  - `update_todo`メソッドの改善

### 次回やること

#### バグ修正
- ⏳ モバイル版のハンバーガーメニューからカレンダーを選択しても表示されないエラーの修正
  - カレンダーが表示されず、Todoリスト画面に戻ってしまう問題を解決
  - モバイルメニューからのカレンダー表示処理の見直しが必要

## セットアップ

### 1. Google Cloud Consoleでの設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」から「Google Sheets API」と「Google Drive API」を有効化
4. 「認証情報」→「認証情報を作成」→「サービスアカウント」を選択
5. サービスアカウントを作成し、JSONキーをダウンロード
6. ダウンロードしたJSONファイルを`credentials.json`としてプロジェクトルートに配置

**スコープ設定について**: サービスアカウントを使用する場合、Google Cloud Consoleでのスコープ設定は**不要**です。アプリケーションのコード内（`sheets_api.py`）で必要なスコープを自動的に指定しているため、追加の設定は必要ありません。

### 2. Googleスプレッドシートの準備

1. 新しいGoogleスプレッドシートを作成
2. スプレッドシートのURLからスプレッドシートIDを取得
   - 例: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
3. 作成したサービスアカウントのメールアドレスをスプレッドシートの共有設定に追加（編集権限）

### 3. ローカル環境での実行

#### ステップ1: JSONキーファイルの配置

1. Google Cloud ConsoleからダウンロードしたJSONキーファイルを確認します
   - ファイル名は通常 `プロジェクト名-xxxxx.json` のような形式です
2. このファイルを **プロジェクトのルートフォルダ**（`webapri`フォルダ）に配置します
3. ファイル名を `credentials.json` に変更します

**プロジェクトフォルダの構成例**:
```
webapri/
├── credentials.json    ← ここに配置（ファイル名を変更）
├── app.py
├── sheets_api.py
└── ...
```

#### ステップ2: .envファイルの設定（推奨方法）

この方法を使うと、毎回環境変数を設定する必要がなくなり、より簡単にアプリを起動できます。

1. **スプレッドシートIDを取得**:
   - Googleスプレッドシートを開く
   - URLを確認: `https://docs.google.com/spreadsheets/d/【ここがID】/edit`
   - 例: URLが `https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit` の場合
   - IDは `1a2b3c4d5e6f7g8h9i0j` です

2. **`.env`ファイルを編集**:
   - プロジェクトルートにある`.env`ファイルをテキストエディタで開く（UTF-8エンコーディングで開いてください）
   - `SPREADSHEET_ID=your_spreadsheet_id_here` の行を以下のように変更:
   ```
   SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j
   ```
   - `your_spreadsheet_id_here`を実際のスプレッドシートIDに置き換えてください
   - ファイルを保存（UTF-8エンコーディングで保存してください）

3. **アプリの起動**:
```bash
# 仮想環境の作成（初回のみ）
python -m venv venv

# 仮想環境の有効化（Windows）
venv\Scripts\activate

# 依存関係のインストール（初回のみ、またはrequirements.txtが変更された場合）
pip install -r requirements.txt

# アプリの起動
python app.py
```

**`.env`ファイルの例**:
```
# Environment Variables
# Set your Spreadsheet ID (get it from Google Spreadsheet URL)
# Example: If URL is https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit
#          Then SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j
SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j

# Credentials file path (usually no need to change)
GOOGLE_CREDENTIALS_FILE=credentials.json
```

**注意**: `.env`ファイルを編集する際は、UTF-8エンコーディングで開いて保存してください。文字化けが発生する場合は、エディタの設定でエンコーディングを確認してください。

**注意**: 
- `.env`ファイルは自動的に`.gitignore`に含まれているため、GitHubにアップロードされることはありません
- `.env`ファイルを編集したら、アプリを再起動してください

#### 代替方法: PowerShellで環境変数を設定する場合

`.env`ファイルを使わず、PowerShellで直接環境変数を設定する場合：

```bash
# 仮想環境の有効化
venv\Scripts\activate

# 環境変数の設定（PowerShell）
$env:SPREADSHEET_ID="あなたのスプレッドシートID"
# 例: $env:SPREADSHEET_ID="1a2b3c4d5e6f7g8h9i0j"

# アプリの起動
python app.py
```

**注意**: PowerShellを閉じると環境変数が消えるため、毎回アプリを起動する前に環境変数を設定する必要があります。

ブラウザで `http://localhost:5000` にアクセスしてください。

## Renderでのデプロイ

### 1. GitHubにコードをプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin あなたのリポジトリURL
git push -u origin main
```

### 2. Renderでの設定

1. [Render](https://render.com/)にログイン
2. 「New +」→「Web Service」を選択
3. GitHubリポジトリを接続
4. 以下の設定を行う：
   - **Name**: 任意の名前（例: `todo-app`）
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment Variables**（重要）:
     - `SPREADSHEET_ID`: あなたのスプレッドシートID
     - `GOOGLE_CREDENTIALS_JSON`: サービスアカウントのJSONキーの内容

### 3. Renderでの環境変数の設定方法

Renderにデプロイする場合は、以下の環境変数を設定する必要があります。

#### ステップ1: SPREADSHEET_IDの設定

1. Renderのダッシュボードで、作成したWebサービスを開く
2. 左側のメニューから「Environment」をクリック
3. 「Add Environment Variable」をクリック
4. 以下のように入力:
   - **Key**: `SPREADSHEET_ID`
   - **Value**: スプレッドシートID（URLから取得したIDのみ）
   
**スプレッドシートIDの取得方法**:
- GoogleスプレッドシートのURL: `https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit`
- この場合のIDは: `1a2b3c4d5e6f7g8h9i0j`（`/d/`と`/edit`の間の部分）

#### ステップ2: GOOGLE_CREDENTIALS_JSONの設定

1. **JSONキーファイルを開く**:
   - プロジェクトフォルダの`credentials.json`ファイルをメモ帳やテキストエディタで開く
   
2. **ファイル全体をコピー**:
   - `Ctrl + A` で全選択
   - `Ctrl + C` でコピー
   
3. **Renderに貼り付け**:
   - Renderの環境変数設定画面で「Add Environment Variable」をクリック
   - **Key**: `GOOGLE_CREDENTIALS_JSON`
   - **Value**: コピーしたJSONの内容をそのまま貼り付け（`Ctrl + V`）
   
4. 「Save Changes」をクリック

**JSONファイルの例**:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  ...
}
```

**重要な注意点**:
- JSONの内容は**すべて**コピーする（最初の`{`から最後の`}`まで）
- 改行も含めてそのまま貼り付けてください
- 値の前後に余分なスペースや引用符を付けないでください

## ファイル構成

```
webapri/
├── app.py                 # Flaskアプリケーション
├── sheets_api.py          # Google Sheets API統合
├── requirements.txt       # 依存関係
├── Procfile              # Render用設定
├── templates/            # HTMLテンプレート
│   ├── index.html        # 一覧ページ
│   └── edit.html         # 登録・編集ページ
└── static/               # 静的ファイル
    └── style.css         # スタイルシート
```

## トラブルシューティング

### localhost接続が拒否される場合

`http://localhost:5000`にアクセスできない場合、以下の点を確認してください：

#### 1. アプリが起動しているか確認

ターミナルで以下のコマンドを実行して、アプリが起動しているか確認してください：

```bash
# 仮想環境が有効化されているか確認
# プロンプトの前に (venv) が表示されているはずです

# アプリを起動
python app.py
```

**正常に起動している場合の表示例**:
```
サーバーを起動しています...
ブラウザで http://localhost:5000 にアクセスしてください

 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
```

このメッセージが表示されていない場合、エラーが発生しています。ターミナルのエラーメッセージを確認してください。

#### 2. よくあるエラーと解決方法

**エラー: `認証情報ファイルが見つかりません: credentials.json`**
- 解決方法: `credentials.json`ファイルがプロジェクトルート（`webapri`フォルダ）に存在するか確認してください
- ファイル名が正確に`credentials.json`になっているか確認してください（拡張子も含めて）

**エラー: `SPREADSHEET_ID環境変数が設定されていません`**
- 解決方法: `.env`ファイルに`SPREADSHEET_ID`が正しく設定されているか確認してください
- `.env`ファイルの内容例:
  ```
  SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j
  ```
- `your_spreadsheet_id_here`のままになっていないか確認してください

**エラー: `ModuleNotFoundError: No module named 'flask'` など**
- 解決方法: 仮想環境が有効化されていないか、依存関係がインストールされていない可能性があります
  ```bash
  # 仮想環境を有効化
  venv\Scripts\activate
  
  # 依存関係をインストール
  pip install -r requirements.txt
  ```

**エラー: `PermissionError` または `Access Denied`**
- 解決方法: スプレッドシートの共有設定で、サービスアカウントのメールアドレスに編集権限が付与されているか確認してください
- サービスアカウントのメールアドレスは、`credentials.json`ファイル内の`client_email`フィールドで確認できます

#### 3. 起動前のチェックリスト

アプリを起動する前に、以下を確認してください：

- [ ] `.env`ファイルがプロジェクトルートに存在する
- [ ] `.env`ファイルに`SPREADSHEET_ID`が正しく設定されている（`your_spreadsheet_id_here`ではない）
- [ ] `credentials.json`ファイルがプロジェクトルートに存在する
- [ ] 仮想環境が有効化されている（プロンプトに`(venv)`が表示されている）
- [ ] 依存関係がインストールされている（`pip install -r requirements.txt`を実行済み）
- [ ] スプレッドシートがサービスアカウントと共有されている（編集権限付き）

#### 4. ポートが既に使用されている場合

5000番ポートが既に使用されている場合、別のポートを使用できます：

```bash
# 環境変数でポートを指定
set PORT=8000
python app.py
```

または、`app.py`の`port`の値を変更してください。

## 注意事項

- `credentials.json`ファイルは絶対にGitHubにコミットしないでください
- `.env`ファイルもGitHubにコミットされないように設定されています（`.gitignore`に含まれています）
- Renderでは環境変数`GOOGLE_CREDENTIALS_JSON`を使用します
- スプレッドシートの共有設定でサービスアカウントに編集権限を付与することを忘れないでください

## ライセンス

MIT

