from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
from sheets_api import SheetsAPI

# 日本時間（JST）のタイムゾーン
JST = pytz.timezone('Asia/Tokyo')

def get_jst_now():
    """現在の日本時間を取得"""
    return datetime.now(JST)

def get_jst_today():
    """今日の日付を日本時間で取得"""
    return get_jst_now().date()

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
    today = get_jst_today()
    print(f"DEBUG: Today's date (JST): {today} (ISO format: {today.strftime('%Y-%m-%d')})")
    # 今日を期日とするTodoを取得
    todos = sheets_api.get_all_todos(due_date_filter=today)
    print(f"DEBUG: Found {len(todos)} todos for today")
    # 期日が過ぎている未完了のTodoを取得
    overdue_todos = sheets_api.get_overdue_todos()
    return render_template('index.html', todos=todos, current_date=today, view_type='today', overdue_todos=overdue_todos)

@app.route('/yesterday')
def yesterday():
    """昨日のTodo一覧ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    yesterday = (get_jst_today() - timedelta(days=1))
    # 昨日を期日とするTodoを取得
    todos = sheets_api.get_all_todos(due_date_filter=yesterday)
    # 期日が過ぎている未完了のTodoを取得
    overdue_todos = sheets_api.get_overdue_todos()
    return render_template('index.html', todos=todos, current_date=yesterday, view_type='yesterday', overdue_todos=overdue_todos)

@app.route('/tomorrow')
def tomorrow():
    """明日のTodo一覧ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    tomorrow_date = (get_jst_today() + timedelta(days=1))
    # 明日を期日とするTodoを取得
    todos = sheets_api.get_all_todos(due_date_filter=tomorrow_date)
    # 期日が過ぎている未完了のTodoを取得
    overdue_todos = sheets_api.get_overdue_todos()
    return render_template('index.html', todos=todos, current_date=tomorrow_date, view_type='tomorrow', overdue_todos=overdue_todos)

@app.route('/date/<date_str>')
def date_view(date_str):
    """指定日付を期日とするTodo一覧ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        # 指定日付を期日とするTodoを取得
        todos = sheets_api.get_all_todos(due_date_filter=selected_date)
        
        # 今日との比較でview_typeを決定
        today = get_jst_today()
        if selected_date == today:
            view_type = 'today'
        elif selected_date == today - timedelta(days=1):
            view_type = 'yesterday'
        elif selected_date == today + timedelta(days=1):
            view_type = 'tomorrow'
        else:
            view_type = 'custom'
        
        # 期日が過ぎている未完了のTodoを取得
        overdue_todos = sheets_api.get_overdue_todos()
        return render_template('index.html', todos=todos, current_date=selected_date, view_type=view_type, overdue_todos=overdue_todos)
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
        
        if title:
            sheets_api.add_todo(title, content, due_date)
            # 期日に応じてリダイレクト
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                    today = get_jst_today()
                    if due_date_obj == today:
                        return redirect(url_for('today'))
                    elif due_date_obj == today - timedelta(days=1):
                        return redirect(url_for('yesterday'))
                    elif due_date_obj == today + timedelta(days=1):
                        return redirect(url_for('tomorrow'))
                    else:
                        return redirect(url_for('date_view', date_str=due_date))
                except:
                    pass
            return redirect(url_for('today'))
    
    # GETリクエスト時、view_typeパラメータから期日のデフォルト値を取得
    view_type = request.args.get('view', 'today')
    due_date_default = ''
    if view_type == 'tomorrow':
        due_date_default = (get_jst_today() + timedelta(days=1)).strftime('%Y-%m-%d')
    elif view_type == 'yesterday':
        due_date_default = (get_jst_today() - timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        due_date_default = get_jst_today().strftime('%Y-%m-%d')
    
    return render_template('edit.html', todo=None, due_date_default=due_date_default, view_type=view_type)

@app.route('/edit/<int:todo_id>', methods=['GET', 'POST'])
def edit_todo(todo_id):
    """Todo編集ページ"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    
    todo = sheets_api.get_todo_by_id(todo_id)
    if not todo:
        return redirect(url_for('today'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        due_date = request.form.get('due_date', '').strip()
        
        if title:
            sheets_api.update_todo(todo_id, title, content, due_date)
            # 期日に応じてリダイレクト
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                    today = get_jst_today()
                    if due_date_obj == today:
                        return redirect(url_for('today'))
                    elif due_date_obj == today - timedelta(days=1):
                        return redirect(url_for('yesterday'))
                    elif due_date_obj == today + timedelta(days=1):
                        return redirect(url_for('tomorrow'))
                    else:
                        return redirect(url_for('date_view', date_str=due_date))
                except:
                    pass
            return redirect(url_for('today'))
    
    # view_typeを期日から決定
    view_type = 'today'
    due_date_str = todo.get('due_date', '')
    if due_date_str:
        try:
            due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            today = get_jst_today()
            if due_date_obj == today - timedelta(days=1):
                view_type = 'yesterday'
            elif due_date_obj == today + timedelta(days=1):
                view_type = 'tomorrow'
        except:
            pass
    
    return render_template('edit.html', todo=todo, view_type=view_type)

@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """Todo削除"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    # 削除前にview_typeを取得
    view_type = request.form.get('view_type', 'today')
    selected_date = request.form.get('selected_date', '')
    sheets_api.delete_todo(todo_id)
    
    # 削除後、同じページにリダイレクト
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
    """Todoを次の日に持越す（期日を明日に変更）"""
    if sheets_api is None:
        return "エラー: Google Sheets APIが初期化されていません。", 500
    tomorrow_date_str = (get_jst_today() + timedelta(days=1)).strftime('%Y-%m-%d')
    todo = sheets_api.get_todo_by_id(todo_id)
    if todo:
        sheets_api.carryover_todo(todo_id, tomorrow_date_str)
    return redirect(url_for('tomorrow'))

if __name__ == '__main__':
    if sheets_api is None:
        print("\nアプリを起動できません。上記のエラーを解決してください。\n")
        exit(1)
    
    port = int(os.environ.get('PORT', 5000))
    print(f"\nサーバーを起動しています...")
    print(f"ブラウザで http://localhost:{port} にアクセスしてください\n")
    app.run(host='127.0.0.1', port=port, debug=True)

