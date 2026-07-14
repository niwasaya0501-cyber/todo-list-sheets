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


@app.route("/")
def index():
    error = None
    todos = []
    try:
        todos = sheets.list_todos()
    except Exception as exc:  # 認証未設定などの場合でも一覧ページ自体は表示する
        error = str(exc)
    return render_template("index.html", todos=todos, error=error)


@app.route("/new", methods=["GET", "POST"])
def new_todo():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        due_date = request.form.get("due_date", "").strip()

        if not title:
            return render_template(
                "form.html",
                mode="new",
                todo={"title": title, "content": content, "due_date": due_date},
                error="タイトルは必須です。",
            )

        try:
            sheets.add_todo(title, content, due_date)
        except Exception as exc:
            return render_template(
                "form.html",
                mode="new",
                todo={"title": title, "content": content, "due_date": due_date},
                error=f"登録に失敗しました: {exc}",
            )
        return redirect(url_for("index"))

    return render_template("form.html", mode="new", todo={}, error=None)


@app.route("/edit/<todo_id>", methods=["GET", "POST"])
def edit_todo(todo_id):
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        due_date = request.form.get("due_date", "").strip()

        if not title:
            return render_template(
                "form.html",
                mode="edit",
                todo_id=todo_id,
                todo={"title": title, "content": content, "due_date": due_date},
                error="タイトルは必須です。",
            )

        try:
            updated = sheets.update_todo(todo_id, title, content, due_date)
        except Exception as exc:
            return render_template(
                "form.html",
                mode="edit",
                todo_id=todo_id,
                todo={"title": title, "content": content, "due_date": due_date},
                error=f"更新に失敗しました: {exc}",
            )
        if not updated:
            return render_template(
                "form.html",
                mode="edit",
                todo_id=todo_id,
                todo={"title": title, "content": content, "due_date": due_date},
                error="対象のやることが見つかりませんでした。",
            )
        return redirect(url_for("index"))

    try:
        todo = sheets.get_todo(todo_id)
    except Exception as exc:
        return render_template("form.html", mode="edit", todo_id=todo_id, todo={}, error=str(exc))

    if todo is None:
        return redirect(url_for("index"))

    return render_template("form.html", mode="edit", todo_id=todo_id, todo=todo, error=None)


@app.route("/delete/<todo_id>", methods=["POST"])
def delete_todo(todo_id):
    try:
        sheets.delete_todo(todo_id)
    except Exception:
        pass
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
