"""Google スプレッドシートをDB代わりに使うためのデータアクセス層。

サービスアカウント方式(gspread)を使用。認証情報はJSONファイルではなく
環境変数 GOOGLE_SERVICE_ACCOUNT_JSON (JSON文字列) から読み込む。
理由: Vercel等のサーバーレス環境ではファイルを秘密裏に置きづらく、
環境変数の方が管理・デプロイの両面で安全かつ簡単なため。
"""
import json
import os
import uuid
from datetime import datetime

import gspread

SHEET_NAME = "todos"
HEADER = ["id", "title", "content", "due_date", "created_at", "updated_at", "completed"]


def _get_client():
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        raise RuntimeError(
            "環境変数 GOOGLE_SERVICE_ACCOUNT_JSON が設定されていません。"
            "サービスアカウントのJSON鍵の中身をそのまま設定してください。"
        )
    info = json.loads(creds_json)
    return gspread.service_account_from_dict(info)


def _get_worksheet():
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise RuntimeError("環境変数 GOOGLE_SHEET_ID が設定されていません。")
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)
    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=10)
        worksheet.append_row(HEADER)
        return worksheet

    # ヘッダー行が無い(新規シート)/ 列が古い場合はヘッダー行だけを上書きする
    # (insert_rowだと不一致のたびに行が増殖するため、常にA1からの上書きにする)
    first_row = worksheet.row_values(1)
    if first_row != HEADER:
        worksheet.update(values=[HEADER], range_name="A1")
    return worksheet


def list_todos():
    """期日の昇順(未設定は最後)で一覧を返す。"""
    worksheet = _get_worksheet()
    records = worksheet.get_all_records(expected_headers=HEADER)
    records.sort(key=lambda r: (r.get("due_date") == "", r.get("due_date", "")))
    return records


def get_todo(todo_id):
    worksheet = _get_worksheet()
    records = worksheet.get_all_records(expected_headers=HEADER)
    for record in records:
        if record.get("id") == todo_id:
            return record
    return None


def add_todo(title, content, due_date):
    worksheet = _get_worksheet()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    todo_id = uuid.uuid4().hex[:8]
    worksheet.append_row([todo_id, title, content, due_date, now, now, "FALSE"])
    return todo_id


def update_todo(todo_id, title, content, due_date):
    worksheet = _get_worksheet()
    cell = worksheet.find(todo_id, in_column=1)
    if cell is None:
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    created_at = worksheet.cell(cell.row, 5).value
    worksheet.update(
        values=[[todo_id, title, content, due_date, created_at, now]],
        range_name=f"A{cell.row}:F{cell.row}",
    )
    return True


def delete_todo(todo_id):
    worksheet = _get_worksheet()
    cell = worksheet.find(todo_id, in_column=1)
    if cell is None:
        return False
    worksheet.delete_rows(cell.row)
    return True


def set_completed(todo_id, completed):
    worksheet = _get_worksheet()
    cell = worksheet.find(todo_id, in_column=1)
    if cell is None:
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    completed_col = HEADER.index("completed") + 1
    updated_at_col = HEADER.index("updated_at") + 1
    worksheet.update_cell(cell.row, completed_col, "TRUE" if completed else "FALSE")
    worksheet.update_cell(cell.row, updated_at_col, now)
    return True
