import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime, timedelta

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
    
    def _get_worksheet_by_date(self, target_date):
        """日付に応じて適切なワークシートを返す"""
        if target_date:
            today = datetime.now().date()
            if isinstance(target_date, str):
                try:
                    target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                except:
                    target_date = today
            
            # 明日以降（未来）の日付なら未来用シート
            if target_date > today + timedelta(days=1):
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
    
    def get_all_todos(self, target_date=None):
        """すべてのTodoを取得（対象日でフィルタリング可能）"""
        # 適切なワークシートを選択
        worksheet = self._get_worksheet_by_date(target_date)
        
        all_values = worksheet.get_all_values()
        if len(all_values) <= 1:
            return []
        
        todos = []
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
                    'target_date': row[8] if len(row) > 8 else ''
                }
                # 対象日でフィルタリング
                if target_date:
                    target_date_str = target_date.strftime('%Y-%m-%d') if hasattr(target_date, 'strftime') else str(target_date)
                    if todo['target_date'] == target_date_str:
                        todos.append(todo)
                else:
                    todos.append(todo)
        
        return todos
    
    def get_todo_by_id(self, todo_id, target_date=None):
        """IDでTodoを取得"""
        # target_dateが指定されている場合、適切なワークシートを優先的に検索
        if target_date:
            # まず適切なワークシートから検索
            target_worksheet = self._get_worksheet_by_date(target_date)
            all_values = target_worksheet.get_all_values()
            for row in all_values[1:]:  # ヘッダーをスキップ
                if row and row[0] == str(todo_id):
                    todo_target_date = row[8] if len(row) > 8 else ''
                    target_date_str = target_date.strftime('%Y-%m-%d') if hasattr(target_date, 'strftime') else str(target_date)
                    # 対象日が一致する場合のみ返す
                    if todo_target_date == target_date_str:
                        return {
                            'id': int(row[0]),
                            'title': row[1] if len(row) > 1 else '',
                            'content': row[2] if len(row) > 2 else '',
                            'day_of_week': row[3] if len(row) > 3 else '',
                            'due_date': row[4] if len(row) > 4 else '',
                            'created_at': row[5] if len(row) > 5 else '',
                            'completed_at': row[6] if len(row) > 6 else '',
                            'status': row[7] if len(row) > 7 else '未完了',
                            'target_date': todo_target_date
                        }
        
        # target_dateがない場合、またはtarget_dateで見つからなかった場合、両方のワークシートを検索
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
                        'target_date': row[8] if len(row) > 8 else ''
                    }
        return None
    
    def add_todo(self, title, content, due_date, target_date=None):
        """Todoを追加"""
        # 対象日が指定されない場合は今日
        if target_date is None:
            target_date = datetime.now().date()
        elif isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except:
                target_date = datetime.now().date()
        
        # 適切なワークシートを選択
        worksheet = self._get_worksheet_by_date(target_date)
        
        todo_id = self._get_next_id(worksheet)
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 期日から曜日を計算
        day_of_week = ''
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
                weekday_names = ['月', '火', '水', '木', '金', '土', '日']
                day_of_week = weekday_names[due_date_obj.weekday()]
            except:
                pass
        
        target_date_str = target_date.strftime('%Y-%m-%d')
        row = [todo_id, title, content, day_of_week, due_date, created_at, '', '未完了', target_date_str]
        worksheet.append_row(row)
        return todo_id
    
    def update_todo(self, todo_id, title, content, due_date, target_date=None):
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
        current_target_date = found_row[8] if len(found_row) > 8 else ''
        
        # 対象日が指定されない場合は既存の値を使用
        if target_date:
            if isinstance(target_date, str):
                try:
                    target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                except:
                    target_date = None
        else:
            # target_dateが指定されていない場合、既存の対象日を使用
            if current_target_date:
                try:
                    target_date = datetime.strptime(current_target_date, '%Y-%m-%d').date()
                except:
                    target_date = datetime.now().date()
            else:
                target_date = datetime.now().date()
        
        target_date_str = target_date.strftime('%Y-%m-%d')
        
        # 対象日が変更された場合のみ、適切なワークシートに移動
        new_target_date = target_date
        target_worksheet = self._get_worksheet_by_date(new_target_date)
        
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
                    completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    worksheet.update(f'H{i}', [['完了']])
                    worksheet.update(f'G{i}', [[completed_at]])
                    return True
        return False
    
    def carryover_todo(self, todo_id, target_date):
        """Todoを次の日に持越す"""
        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return False
        
        # 適切なワークシートを選択
        worksheet = self._get_worksheet_by_date(target_date)
        
        # 新しいTodoとして追加（状態は未完了にリセット）
        new_todo_id = self._get_next_id(worksheet)
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        target_date_str = target_date.strftime('%Y-%m-%d') if hasattr(target_date, 'strftime') else str(target_date)
        
        # 期日から曜日を計算
        day_of_week = ''
        if todo.get('due_date'):
            try:
                due_date_obj = datetime.strptime(todo['due_date'], '%Y-%m-%d')
                weekday_names = ['月', '火', '水', '木', '金', '土', '日']
                day_of_week = weekday_names[due_date_obj.weekday()]
            except:
                pass
        
        row = [new_todo_id, todo['title'], todo['content'], day_of_week, todo.get('due_date', ''), 
               created_at, '', '未完了', target_date_str]
        worksheet.append_row(row)
        return new_todo_id
    
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

