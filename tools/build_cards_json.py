#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 一覧カードの表示情報を共有JSONに書き出す
=============================================================================
商品一覧（site/products.html）のカードは、型番・容量・カテゴリ名・キャッチ
コピー・特徴アイコンといった「一覧で見せる情報」を持っています。この情報は
products.html 内の `var PRODUCTS=[...]` が原本です。

適合検索の結果ページでも同じ密度で商品を見せたいので、原本をそのまま
site/data/catalog/cards.json に書き出し、fitment.js から型番で引けるように
します。原本は1か所のままなので、コピーや文言を直せば両方に反映されます。

■ 使い方
    python3 tools/build_cards_json.py
=============================================================================
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
SRC = os.path.join(SITE, "products.html")
OUT = os.path.join(SITE, "data", "catalog", "cards.json")

# 一覧カードの表示に使うキーだけを残す（重複データを増やさない）
KEEP = ("code", "label", "series", "jp", "cap", "copy", "colors",
        "img", "new", "status", "features")


def main():
    html = open(SRC, encoding="utf-8").read()
    m = re.search(r"var PRODUCTS=(\[.*?\]);", html, re.S)
    if not m:
        raise SystemExit("products.html の PRODUCTS が見つかりません")
    products = json.loads(m.group(1))

    cards = {}
    for p in products:
        cards[p["code"]] = {k: p[k] for k in KEEP if k in p and p[k] not in (None, "", [])}

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(cards, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("site/data/catalog/cards.json を出力：%d モデル / %.1f KB"
          % (len(cards), os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
