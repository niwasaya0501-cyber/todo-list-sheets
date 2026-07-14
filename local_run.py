"""ローカルで動作確認するための起動スクリプト。

`vercel dev` を使わずに素早く手元で確認したいとき用。
使い方: .env を用意した上で `python local_run.py`
"""
from dotenv import load_dotenv

load_dotenv()

from api.index import app

if __name__ == "__main__":
    app.run(debug=True, port=5000)
