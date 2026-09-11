#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品タグ（tools/product_tags.json）を products.html の PRODUCTS に反映し、cards.json を再生成する。

    python3 tools/apply_product_tags.py

・PRODUCTS の各商品に "tags": [...] を書き込む（原本は product_tags.json。ここを直したら再実行）
・タグの定義（グループ・表示名）も TAGS として products.html に埋め込み、一覧のフィルタチップが参照する
・最後に build_cards_json.py を呼び、cards.json にも tags を載せる（商品ページの関連表示が使う）
"""
import json, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "site", "products.html")
TAGS = os.path.join(ROOT, "tools", "product_tags.json")

def main():
    t = json.load(open(TAGS, encoding="utf-8"))
    html = open(SRC, encoding="utf-8").read()
    m = re.search(r"var PRODUCTS=(\[.*?\]);", html, re.S)
    products = json.loads(m.group(1))
    missing = []
    for p in products:
        tags = t["products"].get(p["code"])
        if tags is None:
            missing.append(p["code"]); tags = []
        p["tags"] = tags
    unknown = [c for c in t["products"] if c not in {p["code"] for p in products}]
    html = html[:m.start(1)] + json.dumps(products, ensure_ascii=False) + html[m.end(1):]
    defs = json.dumps({"groups": t["groups"], "tags": t["tags"]}, ensure_ascii=False)
    if re.search(r"var TAGS=\{.*?\};", html, re.S):
        html = re.sub(r"var TAGS=\{.*?\};", lambda _: "var TAGS=" + defs + ";", html, count=1, flags=re.S)
    else:
        html = html.replace("var PRODUCTS=", "var TAGS=" + defs + ";\nvar PRODUCTS=", 1)
    open(SRC, "w", encoding="utf-8").write(html)
    print("products.html に tags を反映：%d 商品" % len(products))
    if missing: print("  ⚠ タグ未定義（空で反映）:", " ".join(missing))
    if unknown: print("  ⚠ 一覧に無い品番（無視）:", " ".join(unknown))
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_cards_json.py")], check=True)

if __name__ == "__main__":
    main()
