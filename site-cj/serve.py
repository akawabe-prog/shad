#!/usr/bin/env python3
# SHAD ローカルプレビュー用サーバー（クリーンURL対応）
# 使い方: /usr/bin/python3 serve.py  → http://localhost:8130/
import os, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
PORT = 8130

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = super().translate_path(path)
        # ディレクトリなら index.html
        if os.path.isdir(p):
            idx = os.path.join(p, "index.html")
            if os.path.exists(idx):
                return idx
        # 拡張子なし & ファイルが無い → .html を試す
        if not os.path.exists(p) and not os.path.splitext(p)[1]:
            if os.path.exists(p + ".html"):
                return p + ".html"
        return p

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    httpd = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"SHAD preview: http://localhost:{PORT}/")
    httpd.serve_forever()
