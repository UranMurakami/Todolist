import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime, timedelta
import pytz

# 日本時間（JST）のタイムゾーン
JST = pytz.timezone('Asia/Tokyo')

def get_jst_now():
    """現在の日本時間を取得"""
    return datetime.now(JST)

def get_jst_today():
    """今日の日付を日本時間で取得"""
    return get_jst_now().date()

class SheetsAPI:
    def __init__(self):
        """Google Sheets APIの初期化"""
        # 環境変数から設定を取得
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # JSONキーのパス（環境変数またはデフォルト）
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            # 環境変数からJSON文字列を取得して認証情報を作成（Render用）
            import json
            try:
                creds_dict = json.loads(creds_json)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            except json.JSONDecodeError as e:
                raise ValueError(f"GOOGLE_CREDENTIALS_JSONの形式が正しくありません: {e}")
        else:
            # ローカル開発用：credentials.jsonファイルを使用
            creds_file = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
            if not os.path.exists(creds_file):
                raise FileNotFoundError(f"認証情報ファイルが見つかりません: {creds_file}")
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
        
        self.client = gspread.authorize(creds)
        
        # スプレッドシートID（環境変数から取得）
        spreadsheet_id = os.environ.get('SPREADSHEET_ID')
        if not spreadsheet_id:
            raise ValueError("SPREADSHEET_ID環境変数が設定されていません")
        
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        self._cleanup_sheets()  # 空白の1枚目を削除
        self.worksheet = self._get_or_create_worksheet()
        self.future_worksheet = self._get_or_create_future_worksheet()
        self._ensure_headers()
        self._ensure_future_headers()
    
    def _cleanup_sheets(self):
        """空白の1枚目のシートを削除（必要に応じて）"""
        try:
            worksheets = self.spreadsheet.worksheets()
            if len(worksheets) > 0:
                first_sheet = worksheets[0]
                # 1枚目のシートが空かどうか確認
                all_values = first_sheet.get_all_values()
                if not all_values or (len(all_values) == 1 and not any(first_sheet.row_values(1))):
                    # 空白のシートなので削除
                    self.spreadsheet.del_worksheet(first_sheet)
                    print(f"空白のシート '{first_sheet.title}' を削除しました")
        except Exception as e:
            print(f"シートのクリーンアップ中にエラーが発生しました: {e}")
    
    def _get_or_create_worksheet(self):
        """通常のワークシートを取得または作成（過去・今日・昨日用）"""
        try:
            worksheet = self.spreadsheet.worksheet('Todos')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title='Todos', rows=1000, cols=10)
        return worksheet
    
    def _get_or_create_future_worksheet(self):
        """未来のTodo用ワークシートを取得または作成"""
        try:
            worksheet = self.spreadsheet.worksheet('Todos_Future')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title='Todos_Future', rows=1000, cols=10)
        return worksheet
    
    def _get_worksheet_by_due_date(self, due_date):
        """期日に応じて適切なワークシートを返す"""
        if due_date:
            today = get_jst_today()
            if isinstance(due_date, str):
                try:
                    due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                except:
                    return self.worksheet
            
            # 明日以降（未来）の期日なら未来用シート
            if due_date > today + timedelta(days=1):
                return self.future_worksheet
        
        # それ以外は通常のシート
        return self.worksheet
    
    def _ensure_headers(self):
        """通常のワークシートのヘッダー行が存在することを確認"""
        try:
            headers = self.worksheet.row_values(1)
            expected_headers = ['ID', 'タイトル', '内容', '曜日', '期日', '作成日時', '完了日時', '状態', '対象日']
            if not headers or headers[0] != 'ID' or len(headers) < len(expected_headers):
                # 既存のヘッダーを更新
                self.worksheet.update('A1:I1', [expected_headers])
        except:
            self.worksheet.insert_row(['ID', 'タイトル', '内容', '曜日', '期日', '作成日時', '完了日時', '状態', '対象日'], 1)
    
    def _ensure_future_headers(self):
        """未来用ワークシートのヘッダー行が存在することを確認"""
        try:
            headers = self.future_worksheet.row_values(1)
            expected_headers = ['ID', 'タイトル', '内容', '曜日', '期日', '作成日時', '完了日時', '状態', '対象日']
            if not headers or headers[0] != 'ID' or len(headers) < len(expected_headers):
                # 既存のヘッダーを更新
                self.future_worksheet.update('A1:I1', [expected_headers])
        except:
            self.future_worksheet.insert_row(['ID', 'タイトル', '内容', '曜日', '期日', '作成日時', '完了日時', '状態', '対象日'], 1)
    
    def _get_next_id(self, worksheet):
        """次のIDを取得（指定されたワークシートから）"""
        all_values = worksheet.get_all_values()
        if len(all_values) <= 1:
            return 1
        
        ids = []
        for row in all_values[1:]:  # ヘッダーをスキップ
            if row and row[0].isdigit():
                ids.append(int(row[0]))
        
        return max(ids) + 1 if ids else 1
    
    def get_all_todos(self, due_date_filter=None):
        """すべてのTodoを取得（期日でフィルタリング可能）"""
        # due_date_filterを正規化
        if due_date_filter:
            if hasattr(due_date_filter, 'strftime'):
                due_date_filter_obj = due_date_filter
                due_date_filter_str = due_date_filter.strftime('%Y-%m-%d')
            elif isinstance(due_date_filter, str):
                try:
                    due_date_filter_obj = datetime.strptime(due_date_filter, '%Y-%m-%d').date()
                    due_date_filter_str = due_date_filter_obj.strftime('%Y-%m-%d')
                except:
                    due_date_filter_obj = None
                    due_date_filter_str = due_date_filter.strip()
            else:
                due_date_filter_obj = None
                due_date_filter_str = str(due_date_filter)
        else:
            due_date_filter_obj = None
            due_date_filter_str = None
        
        # 両方のワークシートから取得（フィルタリングは後で行う）
        all_todos = []
        for worksheet in [self.worksheet, self.future_worksheet]:
            all_values = worksheet.get_all_values()
            
            if len(all_values) > 1:
                for row in all_values[1:]:  # ヘッダーをスキップ
                    if row and row[0].isdigit():
                        todo = {
                            'id': int(row[0]),
                            'title': row[1] if len(row) > 1 else '',
                            'content': row[2] if len(row) > 2 else '',
                            'day_of_week': row[3] if len(row) > 3 else '',
                            'due_date': row[4] if len(row) > 4 else '',
                            'created_at': row[5] if len(row) > 5 else '',
                            'completed_at': row[6] if len(row) > 6 else '',
                            'status': row[7] if len(row) > 7 else '未完了',
                            'target_date': row[8] if len(row) > 8 else ''  # 互換性のため保持
                        }
                        all_todos.append(todo)
        
        # 期日でフィルタリング
        if due_date_filter_str:
            todos = []
            print(f"DEBUG: Filtering todos by due_date='{due_date_filter_str}'")
            for todo in all_todos:
                todo_due_date = todo['due_date'].strip() if todo['due_date'] else ''
                if len(todos) < 3:  # 最初の数件のみデバッグ出力
                    print(f"DEBUG: Comparing filter='{due_date_filter_str}' with todo_due_date='{todo_due_date}' (Title: {todo.get('title', 'N/A')})")
                if todo_due_date == due_date_filter_str:
                    todos.append(todo)
            print(f"DEBUG: Found {len(todos)} todos matching due_date='{due_date_filter_str}'")
        else:
            todos = all_todos
        
        # 期限順にソート（期限がないものは最後に配置）
        def sort_key(todo):
            due_date = todo.get('due_date', '').strip()
            if not due_date:
                # 期限がないものは最後に表示するため、非常に大きい値を返す
                return '9999-12-31'
            return due_date
        
        todos.sort(key=sort_key)
        return todos
    
    def get_overdue_todos(self):
        """期日が過ぎている未完了のTodoを取得"""
        today = get_jst_today()
        overdue_todos = []
        
        # 両方のワークシートを確認
        for worksheet in [self.worksheet, self.future_worksheet]:
            all_values = worksheet.get_all_values()
            if len(all_values) <= 1:
                continue
            
            for row in all_values[1:]:  # ヘッダーをスキップ
                if row and row[0].isdigit():
                    status = row[7] if len(row) > 7 else '未完了'
                    due_date_str = row[4] if len(row) > 4 else ''
                    
                    # 未完了かつ期日が設定されているTodoのみをチェック
                    if status != '完了' and due_date_str:
                        try:
                            # 期日を日付オブジェクトに変換
                            due_date = datetime.strptime(due_date_str.strip(), '%Y-%m-%d').date()
                            
                            # 期日が今日より前（過ぎている）場合
                            if due_date < today:
                                todo = {
                                    'id': int(row[0]),
                                    'title': row[1] if len(row) > 1 else '',
                                    'content': row[2] if len(row) > 2 else '',
                                    'day_of_week': row[3] if len(row) > 3 else '',
                                    'due_date': due_date_str.strip(),
                                    'created_at': row[5] if len(row) > 5 else '',
                                    'completed_at': row[6] if len(row) > 6 else '',
                                    'status': status,
                                    'target_date': row[8] if len(row) > 8 else ''
                                }
                                overdue_todos.append(todo)
                        except (ValueError, AttributeError):
                            # 期日の形式が正しくない場合はスキップ
                            continue
        
        # 期日でソート（古い順）
        overdue_todos.sort(key=lambda x: x['due_date'])
        return overdue_todos
    
    def get_todo_by_id(self, todo_id):
        """IDでTodoを取得"""
        # 両方のワークシートを検索
        for worksheet in [self.worksheet, self.future_worksheet]:
            all_values = worksheet.get_all_values()
            for row in all_values[1:]:  # ヘッダーをスキップ
                if row and row[0] == str(todo_id):
                    return {
                        'id': int(row[0]),
                        'title': row[1] if len(row) > 1 else '',
                        'content': row[2] if len(row) > 2 else '',
                        'day_of_week': row[3] if len(row) > 3 else '',
                        'due_date': row[4] if len(row) > 4 else '',
                        'created_at': row[5] if len(row) > 5 else '',
                        'completed_at': row[6] if len(row) > 6 else '',
                        'status': row[7] if len(row) > 7 else '未完了',
                        'target_date': row[8] if len(row) > 8 else ''  # 互換性のため保持
                    }
        return None
    
    def add_todo(self, title, content, due_date):
        """Todoを追加"""
        # 期日から適切なワークシートを選択
        worksheet = self._get_worksheet_by_due_date(due_date)
        
        todo_id = self._get_next_id(worksheet)
        created_at = get_jst_now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 期日から曜日を計算
        day_of_week = ''
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
                weekday_names = ['月', '火', '水', '木', '金', '土', '日']
                day_of_week = weekday_names[due_date_obj.weekday()]
            except:
                pass
        
        # 対象日は空文字列にする（互換性のため列は保持）
        target_date_str = ''
        row = [todo_id, title, content, day_of_week, due_date, created_at, '', '未完了', target_date_str]
        worksheet.append_row(row)
        return todo_id
    
    def update_todo(self, todo_id, title, content, due_date):
        """Todoを更新"""
        # まず、既存のTodoを検索してワークシートを特定
        found_worksheet = None
        found_row_index = None
        found_row = None
        
        for worksheet in [self.worksheet, self.future_worksheet]:
            all_values = worksheet.get_all_values()
            for i, row in enumerate(all_values[1:], start=2):  # ヘッダーを考慮して行番号を調整
                if row and row[0] == str(todo_id):
                    found_worksheet = worksheet
                    found_row_index = i
                    found_row = row
                    break
            if found_worksheet:
                break
        
        if not found_worksheet or not found_row:
            return False
        
        # 期日から曜日を計算
        day_of_week = ''
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
                weekday_names = ['月', '火', '水', '木', '金', '土', '日']
                day_of_week = weekday_names[due_date_obj.weekday()]
            except:
                pass
        
        # 既存の状態と完了日時を保持
        current_status = found_row[7] if len(found_row) > 7 else '未完了'
        completed_at = found_row[6] if len(found_row) > 6 else ''
        
        # 期日から適切なワークシートを選択
        target_worksheet = self._get_worksheet_by_due_date(due_date)
        
        # 対象日は空文字列にする（互換性のため列は保持）
        target_date_str = ''
        
        # ワークシートが変更された場合のみ移動
        if target_worksheet.id != found_worksheet.id:
            # 新しいワークシートに追加
            new_todo_id = self._get_next_id(target_worksheet)
            row_data = [new_todo_id, title, content, day_of_week, due_date, found_row[5] if len(found_row) > 5 else '', completed_at, current_status, target_date_str]
            target_worksheet.append_row(row_data)
            # 古いワークシートから削除
            found_worksheet.delete_rows(found_row_index)
        else:
            # 同じワークシート内で更新（IDも含めて更新）
            found_worksheet.update(f'A{found_row_index}:I{found_row_index}', [[todo_id, title, content, day_of_week, due_date, found_row[5] if len(found_row) > 5 else '', completed_at, current_status, target_date_str]])
        return True
    
    def complete_todo(self, todo_id):
        """Todoを完了にする"""
        # 両方のワークシートを検索
        for worksheet in [self.worksheet, self.future_worksheet]:
            all_values = worksheet.get_all_values()
            for i, row in enumerate(all_values[1:], start=2):
                if row and row[0] == str(todo_id):
                    completed_at = get_jst_now().strftime('%Y-%m-%d %H:%M:%S')
                    worksheet.update(f'H{i}', [['完了']])
                    worksheet.update(f'G{i}', [[completed_at]])
                    return True
        return False
    
    def carryover_todo(self, todo_id, new_due_date):
        """Todoを次の日に持越す（期日を更新）"""
        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return False
        
        # 期日を更新して新しいワークシートに移動する場合があるため、update_todoを使用
        return self.update_todo(todo_id, todo['title'], todo['content'], new_due_date)
    
    def delete_todo(self, todo_id):
        """Todoを削除"""
        # 両方のワークシートを検索
        for worksheet in [self.worksheet, self.future_worksheet]:
            all_values = worksheet.get_all_values()
            for i, row in enumerate(all_values[1:], start=2):  # ヘッダーを考慮して行番号を調整
                if row and row[0] == str(todo_id):
                    worksheet.delete_rows(i)
                    return True
        return False

