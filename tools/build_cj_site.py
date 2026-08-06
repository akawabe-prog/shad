#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
カスタムジャパン版サイト（shad.customjapan.net）のビルド
=============================================================================
ブランドサイト `site/`（www.shad-japan.com）を原本に、toC向けの販売サイトを
`dist/cj/` に生成します。**site/ は一切変更しません。**

■ ブランドサイトとの違い（このスクリプトが行う変換）
    1. 正規URL       www.shad-japan.com → shad.customjapan.net（og:url / canonical）
    2. 販売表示       cj_shop.js を全ページに読み込み
                     → 販売価格（税込）・定価・割引率・在庫・購入ボタンを表示
    3. ヘッダー       カートアイコン（EC）を追加
    4. 文言           「ご購入は日本総代理店…」→ カスタムジャパンで購入できる案内
    5. フッター       ショッピングガイド（送料・支払い・返品）への導線を追加

■ 使い方
    python3 tools/fetch_api_prices.py     # 価格・在庫を最新化（先に実行）
    python3 tools/build_cj_site.py        # dist/cj/ を生成

■ アップロード
    dist/cj/ の中身を shad.customjapan.net のドキュメントルート直下へ。
=============================================================================
"""

import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "dist", "cj")

BRAND_URL = "https://www.shad-japan.com"
SHOP_URL = "https://shad.customjapan.net"
EC_TOP = "https://moto.customjapan.net"

# ショッピングガイド（カスタムジャパン通販サイトの既存ページ）
GUIDE_LINKS = [
    ("ご利用ガイド", EC_TOP + "/h/guide"),
    ("送料・お支払い方法", EC_TOP + "/h/guide"),
    ("返品・交換について", EC_TOP + "/h/guide"),
]

CART_BTN = (
    '<a href="' + EC_TOP + '/cart" target="_blank" rel="noopener" aria-label="カートを見る"'
    ' class="text-white/80 hover:text-white transition">'
    '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 24 24"'
    ' fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"'
    ' stroke-linejoin="round" aria-hidden="true"><path d="M6 19m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/>'
    '<path d="M17 19m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"/>'
    '<path d="M17 17h-11v-14h-2"/><path d="M6 5l14 1l-1 7h-13"/></svg></a>'
)


def rewrite_html(s):
    # ① 正規URL
    s = s.replace(BRAND_URL, SHOP_URL)

    # ② 販売表示スクリプト（purchase.js のあとに読む）
    if "/js/cj_shop.js" not in s:
        if "/js/purchase.js" in s:
            s = s.replace('<script src="/js/purchase.js"></script>',
                          '<script src="/js/purchase.js"></script>\n'
                          '<script src="/js/cj_shop.js"></script>', 1)
        else:
            # nav.js は属性付き（data-lp-autoplay など）のページもあるので正規表現で探す
            m = re.search(r'<script src="/js/nav\.js"[^>]*></script>', s)
            if m:
                s = s.replace(m.group(0),
                              '<script src="/js/cj_shop.js"></script>\n' + m.group(0), 1)
            else:
                s = s.replace("</body>", '<script src="/js/cj_shop.js"></script>\n</body>', 1)

    # ③ ヘッダーにカートアイコン（検索ボタンの隣）
    m = re.search(r'<button aria-label="検索"[\s\S]*?</button>', s)
    if m and 'aria-label="カートを見る"' not in s:
        s = s.replace(m.group(0), m.group(0) + CART_BTN, 1)

    # ④ 「購入は代理店へ」系の文言を、ここで買える案内に
    s = s.replace("※ご購入は日本総代理店 株式会社カスタムジャパンにて承ります。",
                  "※価格は税込・カスタムジャパン販売価格です。")
    s = s.replace("ご購入は日本総代理店 株式会社カスタムジャパンにて承ります。",
                  "カスタムジャパン通販サイトでご購入いただけます。")
    s = s.replace("※ご購入は日本総代理店のカスタムジャパンにて承ります。",
                  "※価格は税込・カスタムジャパン販売価格です。")

    # ⑤ フッターにショッピングガイド
    anchor = '<a href="/faq" class="hover:text-white transition">FAQ・取扱説明書</a>'
    if anchor in s and "ご利用ガイド" not in s:
        links = "".join(
            '<li><a href="%s" target="_blank" rel="noopener" class="hover:text-white transition">%s</a></li>'
            % (url, label) for label, url in GUIDE_LINKS)
        s = s.replace("<li>" + anchor + "</li>", "<li>" + anchor + "</li>" + links, 1)

    return s


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SITE, OUT, ignore=shutil.ignore_patterns(".DS_Store"))

    changed = 0
    for dirpath, _dirs, files in os.walk(OUT):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(dirpath, name)
            src = open(path, encoding="utf-8").read()
            new = rewrite_html(src)
            if new != src:
                open(path, "w", encoding="utf-8").write(new)
                changed += 1

    prices = os.path.join(OUT, "data", "ec", "api_prices.json")
    have_prices = os.path.exists(prices)

    print("=" * 62)
    print("カスタムジャパン版を生成: dist/cj/")
    print("=" * 62)
    print("書き換えたページ : %d" % changed)
    print("正規URL          : %s" % SHOP_URL)
    print("購入導線          : %s/i/<品番>（cj_shop.js の ITEM_URL）" % EC_TOP)
    print("価格・在庫データ  : %s" % ("あり" if have_prices else "**なし** → tools/fetch_api_prices.py を実行"))
    if have_prices:
        import json
        d = json.load(open(prices, encoding="utf-8"))
        rows = d.get("byCjCode", {})
        priced = [v for v in rows.values() if v.get("saleTaxIn")]
        print("                   %d品番 / 販売価格あり %d件" % (len(rows), len(priced)))
    print("\nアップロード      : dist/cj/ の中身を shad.customjapan.net の直下へ")


if __name__ == "__main__":
    main()
