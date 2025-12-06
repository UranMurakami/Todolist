#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
プロジェクトのセットアップ状況を確認するスクリプト
"""

import os
import sys

print("=" * 50)
print("プロジェクトセットアップ状況の確認")
print("=" * 50)

# 1. 必要なファイルの確認
print("\n【1. ファイルの存在確認】")
required_files = {
    'app.py': 'Flaskアプリケーション',
    'sheets_api.py': 'Google Sheets API統合',
    'requirements.txt': '依存関係リスト',
    '.env': '環境変数設定ファイル',
    'credentials.json': 'Google認証情報',
    '.gitignore': 'Git除外設定',
    'Procfile': 'Render用設定',
    'templates/index.html': 'HTMLテンプレート（一覧）',
    'templates/edit.html': 'HTMLテンプレート（編集）',
    'static/style.css': 'スタイルシート'
}

all_files_exist = True
for file_path, description in required_files.items():
    exists = os.path.exists(file_path)
    status = "[OK]" if exists else "[NG]"
    print(f"  {status} {file_path:<30} - {description}")
    if not exists and file_path in ['.env', 'credentials.json']:
        all_files_exist = False

# 2. .envファイルの内容確認
print("\n【2. .envファイルの設定確認】")
if os.path.exists('.env'):
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
            if 'SPREADSHEET_ID=' in env_content:
                for line in env_content.split('\n'):
                    if 'SPREADSHEET_ID=' in line and not line.strip().startswith('#'):
                        value = line.split('=', 1)[1].strip()
                        if value == 'your_spreadsheet_id_here' or not value:
                            print("  [NG] SPREADSHEET_IDが設定されていません")
                            print("    → .envファイルでSPREADSHEET_IDを実際のIDに変更してください")
                        else:
                            print(f"  [OK] SPREADSHEET_IDが設定されています: {value[:20]}...")
            else:
                print("  [NG] SPREADSHEET_IDが見つかりません")
    except Exception as e:
        print(f"  [NG] .envファイルの読み込みエラー: {e}")
else:
    print("  [NG] .envファイルが見つかりません")

# 3. credentials.jsonの確認
print("\n【3. credentials.jsonの確認】")
if os.path.exists('credentials.json'):
    try:
        import json
        with open('credentials.json', 'r', encoding='utf-8') as f:
            creds = json.load(f)
            if 'client_email' in creds:
                print(f"  [OK] credentials.jsonが正しく設定されています")
                print(f"    サービスアカウント: {creds['client_email']}")
                print("    → このメールアドレスをスプレッドシートの共有設定に追加してください")
            else:
                print("  [NG] credentials.jsonの形式が正しくありません")
    except json.JSONDecodeError:
        print("  [NG] credentials.jsonがJSON形式ではありません")
    except Exception as e:
        print(f"  [NG] credentials.jsonの読み込みエラー: {e}")
else:
    print("  [NG] credentials.jsonファイルが見つかりません")
    print("    → Google Cloud ConsoleからJSONキーをダウンロードして配置してください")

# 4. 依存関係の確認
print("\n【4. Pythonパッケージの確認】")
required_packages = ['flask', 'gspread', 'google.auth', 'dotenv']
for package in required_packages:
    try:
        if package == 'google.auth':
            import google.auth
        else:
            __import__(package.replace('.', '_') if '.' in package else package)
        print(f"  [OK] {package} がインストールされています")
    except ImportError:
        print(f"  [NG] {package} がインストールされていません")
        print(f"    → pip install -r requirements.txt を実行してください")

# 5. まとめ
print("\n" + "=" * 50)
print("【まとめ】")

issues = []
if not os.path.exists('.env'):
    issues.append(".envファイルを作成する必要があります")
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        if 'SPREADSHEET_ID=your_spreadsheet_id_here' in f.read():
            issues.append(".envファイルでSPREADSHEET_IDを実際のIDに設定してください")
if not os.path.exists('credentials.json'):
    issues.append("credentials.jsonファイルを配置してください")

if issues:
    print("以下の問題があります：")
    for issue in issues:
        print(f"  • {issue}")
    print("\nこれらの問題を解決してから、python app.py でアプリを起動してください。")
else:
    print("[OK] 基本的な設定は完了しています！")
    print("  python app.py でアプリを起動できます。")

print("=" * 50)

