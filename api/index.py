import hashlib
import os

from flask import Flask, redirect, render_template, request, url_for

try:
    from . import sheets
except ImportError:  # `python api/index.py` のような直接実行時のフォールバック
    import sheets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

# CSSの内容が変わるたびに値が変わるバージョン文字列。
# ブラウザがstyle.cssを古いままキャッシュしてしまう問題を避けるため、
# テンプレート側で "?v=<この値>" をURLに付与する。
with open(os.path.join(BASE_DIR, "static", "style.css"), "rb") as _f:
    STYLE_VERSION = hashlib.md5(_f.read()).hexdigest()[:8]


@app.context_processor
def inject_style_version():
    return {"style_version": STYLE_VERSION}


@app.route("/")
def index():
    error = None
    grouped = {cat: [] for cat in sheets.CATEGORIES}
    completed_todos = []
    try:
        todos = sheets.list_todos()
        completed_todos = [t for t in todos if t.get("completed") == "TRUE"]
        completed_todos.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
        for todo in todos:
            if todo.get("completed") == "TRUE":
                continue
            category = todo.get("category") or sheets.DEFAULT_CATEGORY
            if category not in grouped:
                category = sheets.DEFAULT_CATEGORY
            grouped[category].append(todo)
    except Exception as exc:  # 認証未設定などの場合でも一覧ページ自体は表示する
        error = str(exc)
    return render_template(
        "index.html",
        categories=sheets.CATEGORIES,
        grouped=grouped,
        completed_todos=completed_todos,
        error=error,
    )


def _form_fields():
    return {
        "title": request.form.get("title", "").strip(),
        "content": request.form.get("content", "").strip(),
        "due_date": request.form.get("due_date", "").strip(),
        "category": request.form.get("category", "").strip(),
        "priority": request.form.get("priority", "").strip(),
    }


@app.route("/new", methods=["GET", "POST"])
def new_todo():
    if request.method == "POST":
        fields = _form_fields()

        if not fields["title"]:
            return render_template(
                "form.html",
                mode="new",
                categories=sheets.CATEGORIES,
                priorities=sheets.PRIORITIES,
                todo=fields,
                error="タイトルは必須です。",
            )

        try:
            sheets.add_todo(
                fields["title"], fields["content"], fields["due_date"], fields["category"], fields["priority"]
            )
        except Exception as exc:
            return render_template(
                "form.html",
                mode="new",
                categories=sheets.CATEGORIES,
                priorities=sheets.PRIORITIES,
                todo=fields,
                error=f"登録に失敗しました: {exc}",
            )
        return redirect(url_for("index"))

    return render_template(
        "form.html",
        mode="new",
        categories=sheets.CATEGORIES,
        priorities=sheets.PRIORITIES,
        todo={"category": sheets.DEFAULT_CATEGORY, "priority": sheets.DEFAULT_PRIORITY},
        error=None,
    )


@app.route("/edit/<todo_id>", methods=["GET", "POST"])
def edit_todo(todo_id):
    if request.method == "POST":
        fields = _form_fields()

        if not fields["title"]:
            return render_template(
                "form.html",
                mode="edit",
                todo_id=todo_id,
                categories=sheets.CATEGORIES,
                priorities=sheets.PRIORITIES,
                todo=fields,
                error="タイトルは必須です。",
            )

        try:
            updated = sheets.update_todo(
                todo_id,
                fields["title"],
                fields["content"],
                fields["due_date"],
                fields["category"],
                fields["priority"],
            )
        except Exception as exc:
            return render_template(
                "form.html",
                mode="edit",
                todo_id=todo_id,
                categories=sheets.CATEGORIES,
                priorities=sheets.PRIORITIES,
                todo=fields,
                error=f"更新に失敗しました: {exc}",
            )
        if not updated:
            return render_template(
                "form.html",
                mode="edit",
                todo_id=todo_id,
                categories=sheets.CATEGORIES,
                priorities=sheets.PRIORITIES,
                todo=fields,
                error="対象のやることが見つかりませんでした。",
            )
        return redirect(url_for("index"))

    try:
        todo = sheets.get_todo(todo_id)
    except Exception as exc:
        return render_template(
            "form.html",
            mode="edit",
            todo_id=todo_id,
            categories=sheets.CATEGORIES,
            priorities=sheets.PRIORITIES,
            todo={},
            error=str(exc),
        )

    if todo is None:
        return redirect(url_for("index"))

    return render_template(
        "form.html",
        mode="edit",
        todo_id=todo_id,
        categories=sheets.CATEGORIES,
        priorities=sheets.PRIORITIES,
        todo=todo,
        error=None,
    )


@app.route("/delete/<todo_id>", methods=["POST"])
def delete_todo(todo_id):
    try:
        sheets.delete_todo(todo_id)
    except Exception:
        pass
    return redirect(url_for("index"))


@app.route("/complete/<todo_id>", methods=["POST"])
def complete_todo(todo_id):
    completed = request.form.get("completed") == "1"
    try:
        sheets.set_completed(todo_id, completed)
    except Exception:
        pass
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
