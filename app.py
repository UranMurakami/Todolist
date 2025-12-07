from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sheets_api import SheetsAPI

# .envファイルから環境変数を読み込む
load_dotenv()

app = Flask(__name__)

# Google Sheets APIの初期化
try:
    sheets_api = SheetsAPI()
except Exception as e:
    print(f"エラー: Google Sheets APIの初期化に失敗しました: {e}")
    print("以下を確認してください:")
    print("1. .envファイルにSPREADSHEET_IDが正しく設定されているか")
    print("2. credentials.jsonファイルがプロジェクトルートに存在するか")
    print("3. スプレッドシートの共有設定でサービスアカウントに編集権限が付与されているか")
    sheets_api = None

@app.route('/')
def index():
    """今日のTodo一覧ページ"""
    return redirect(url_for('today'))

@app.route('/today')
def today():
    """今日のTodo一覧ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。ターミナルのエラーメッセージを確認してください。", 500
    today = datetime.now().date()
    # デバッグ用: 今日の日付を出力
    print(f"DEBUG: Today's date: {today} (ISO format: {today.strftime('%Y-%m-%d')})")
    todos = sheets_api.get_all_todos(target_date=today)
    print(f"DEBUG: Found {len(todos)} todos for today")
    return render_template('index.html', todos=todos, current_date=today, view_type='today')

@app.route('/yesterday')
def yesterday():
    """昨日のTodo一覧ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    yesterday = (datetime.now() - timedelta(days=1)).date()
    todos = sheets_api.get_all_todos(target_date=yesterday)
    return render_template('index.html', todos=todos, current_date=yesterday, view_type='yesterday')

@app.route('/tomorrow')
def tomorrow():
    """明日のTodo一覧ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    tomorrow_date = (datetime.now() + timedelta(days=1)).date()
    todos = sheets_api.get_all_todos(target_date=tomorrow_date)
    return render_template('index.html', todos=todos, current_date=tomorrow_date, view_type='tomorrow')

@app.route('/date/<date_str>')
def date_view(date_str):
    """指定日付のTodo一覧ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        todos = sheets_api.get_all_todos(target_date=selected_date)
        
        # 今日との比較でview_typeを決定
        today = datetime.now().date()
        if selected_date == today:
            view_type = 'today'
        elif selected_date == today - timedelta(days=1):
            view_type = 'yesterday'
        elif selected_date == today + timedelta(days=1):
            view_type = 'tomorrow'
        else:
            view_type = 'custom'
        
        return render_template('index.html', todos=todos, current_date=selected_date, view_type=view_type)
    except ValueError:
        return redirect(url_for('today'))

@app.route('/add', methods=['GET', 'POST'])
def add_todo():
    """Todo追加ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        due_date = request.form.get('due_date', '').strip()
        target_date_str = request.form.get('target_date', '').strip()
        
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except:
                pass
        
        if title:
            sheets_api.add_todo(title, content, due_date, target_date)
            # 対象日に応じてリダイレクト
            if target_date:
                today = datetime.now().date()
                if target_date == today:
                    return redirect(url_for('today'))
                elif target_date == today - timedelta(days=1):
                    return redirect(url_for('yesterday'))
                elif target_date == today + timedelta(days=1):
                    return redirect(url_for('tomorrow'))
                else:
                    return redirect(url_for('date_view', date_str=target_date.strftime('%Y-%m-%d')))
            return redirect(url_for('today'))
    
    # GETリクエスト時、view_typeパラメータから対象日を取得
    view_type = request.args.get('view', 'today')
    target_date_param = request.args.get('target_date', '')
    
    if target_date_param:
        try:
            target_date = datetime.strptime(target_date_param, '%Y-%m-%d').date()
        except:
            target_date = datetime.now().date()
    else:
        target_date = datetime.now().date()
        if view_type == 'tomorrow':
            target_date = datetime.now().date() + timedelta(days=1)
        elif view_type == 'yesterday':
            target_date = datetime.now().date() - timedelta(days=1)
    
    return render_template('edit.html', todo=None, target_date=target_date.strftime('%Y-%m-%d'), view_type=view_type)

@app.route('/edit/<int:todo_id>', methods=['GET', 'POST'])
def edit_todo(todo_id):
    """Todo編集ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    # 対象日を取得（URLパラメータから）
    target_date_param = request.args.get('target_date', '')
    target_date_for_search = None
    if target_date_param:
        try:
            target_date_for_search = datetime.strptime(target_date_param, '%Y-%m-%d').date()
        except:
            pass
    
    todo = sheets_api.get_todo_by_id(todo_id, target_date_for_search)
    if not todo:
        return redirect(url_for('today'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        due_date = request.form.get('due_date', '').strip()
        target_date_str = request.form.get('target_date', '').strip()
        
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except:
                pass
        
        if title:
            sheets_api.update_todo(todo_id, title, content, due_date, target_date)
            # 対象日に応じてリダイレクト
            if target_date:
                today = datetime.now().date()
                if target_date == today:
                    return redirect(url_for('today'))
                elif target_date == today - timedelta(days=1):
                    return redirect(url_for('yesterday'))
                elif target_date == today + timedelta(days=1):
                    return redirect(url_for('tomorrow'))
                else:
                    return redirect(url_for('date_view', date_str=target_date.strftime('%Y-%m-%d')))
            return redirect(url_for('today'))
    
    # 対象日を取得
    target_date_str = todo.get('target_date', '')
    view_type = 'today'
    if target_date_str:
        try:
            target_date_obj = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            if target_date_obj == today - timedelta(days=1):
                view_type = 'yesterday'
            elif target_date_obj == today + timedelta(days=1):
                view_type = 'tomorrow'
        except:
            pass
    
    # 対象日が空の場合は今日の日付を使用
    if not target_date_str:
        target_date_str = datetime.now().date().strftime('%Y-%m-%d')
    
    return render_template('edit.html', todo=todo, target_date=target_date_str, view_type=view_type)

@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """Todo削除"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    # 削除前にview_typeを取得
    view_type = request.form.get('view_type', 'today')
    selected_date = request.form.get('selected_date', '')
    sheets_api.delete_todo(todo_id)
    
    if selected_date:
        return redirect(url_for('date_view', date_str=selected_date))
    elif view_type == 'yesterday':
        return redirect(url_for('yesterday'))
    elif view_type == 'tomorrow':
        return redirect(url_for('tomorrow'))
    return redirect(url_for('today'))

@app.route('/complete/<int:todo_id>', methods=['POST'])
def complete_todo(todo_id):
    """Todoを完了にする"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    view_type = request.form.get('view_type', 'today')
    selected_date = request.form.get('selected_date', '')
    sheets_api.complete_todo(todo_id)
    
    if selected_date:
        return redirect(url_for('date_view', date_str=selected_date))
    elif view_type == 'yesterday':
        return redirect(url_for('yesterday'))
    elif view_type == 'tomorrow':
        return redirect(url_for('tomorrow'))
    return redirect(url_for('today'))

@app.route('/carryover/<int:todo_id>', methods=['POST'])
def carryover_todo(todo_id):
    """Todoを次の日に持越す"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    tomorrow_date = datetime.now().date() + timedelta(days=1)
    sheets_api.carryover_todo(todo_id, tomorrow_date)
    return redirect(url_for('tomorrow'))

if __name__ == '__main__':
    if sheets_api is None:
        print("\nアプリを起動できません。上記のエラーを解決してください。\n")
        exit(1)
    
    port = int(os.environ.get('PORT', 5000))
    print(f"\nサーバーを起動しています...")
    print(f"ブラウザで http://localhost:{port} にアクセスしてください\n")
    app.run(host='127.0.0.1', port=port, debug=True)

