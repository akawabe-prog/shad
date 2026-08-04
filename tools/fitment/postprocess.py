#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 適合検索データをブランドサイト用に変換（商品との突合）
=============================================================================
tools/fitment/dist/ に生成された適合データは、商品リンクがカスタムジャパンの
EC（moto.customjapan.net/i/品番）を指している。ブランドサイトでは自サイトの
商品ページへ送りたいので、品番からモデルコードを引いて書き換える。

■ 使い方
    python3 tools/fitment/build.py        # 適合データの生成（この工程まで含む）
    python3 tools/fitment/postprocess.py  # 変換のみ再実行

■ 変換内容
    商品（トップケース・サイドケース・サイドバッグ・タンクバッグ）
      url   → /product/<code>          （自サイトの商品ページ）
      ecUrl → 元のECリンク（購入導線として保持）
      img   → /img/products/cards/<code>.webp（無ければ元のCDN画像）
      code  → モデルコード（TR55 など）を付与
    フィッティングキット
      url は EC のまま（自サイトにキットの個別ページは無い）

■ 突合の根拠
    site/data/catalog/products.json（build_catalog.py がマスターから生成）の
    品番 → モデルコードの対応を使う。マスターが更新されれば自動で追随する。
=============================================================================
"""

import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(ROOT))
DIST = os.path.join(ROOT, "dist")
SITE = os.path.join(PROJECT, "site")
OUT_DIR = os.path.join(SITE, "data", "fitment")
CATALOG = os.path.join(SITE, "data", "catalog", "products.json")

EC_RE = re.compile(r"^https://moto\.customjapan\.net/i/(\w+)$")


def load_maps():
    """品番 → モデルコード、モデルコード → 自サイトURL/画像"""
    products = json.load(open(CATALOG, encoding="utf-8"))
    cj_to_code = {}
    for code, entry in products.items():
        for v in entry.get("variants", []):
            if v.get("cjCode"):
                cj_to_code[str(v["cjCode"])] = code

    page_of, img_of = {}, {}
    for code in products:
        low = code.lower()
        if os.path.exists(os.path.join(SITE, "product", low + ".html")):
            page_of[code] = "/product/" + low
        card = os.path.join("img", "products", "cards", low + ".webp")
        if os.path.exists(os.path.join(SITE, card)):
            img_of[code] = "/" + card
    return cj_to_code, page_of, img_of


def rewrite_product(node, cj_to_code, page_of, img_of, stats):
    """商品ノード（url/img を持つ dict）を自サイト向けに書き換える。"""
    url = node.get("url") or ""
    m = EC_RE.match(url)
    if not m:
        return node
    cj = m.group(1)
    code = cj_to_code.get(cj)
    if not code:
        stats["unmatched"].add(cj)
        return node
    node["code"] = code
    node["ecUrl"] = url
    if code in page_of:
        node["url"] = page_of[code]
        stats["linked"] += 1
    else:
        stats["no_page"].add(code)
    if code in img_of:
        node["img"] = img_of[code]
    return node


def walk_products(obj, fn):
    """商品ノードだけを辿って書き換える（キットは対象外）。"""
    if isinstance(obj, list):
        for v in obj:
            walk_products(v, fn)
    elif isinstance(obj, dict):
        # 商品ノードの目印：url と img（または name）を持つ末端
        if "url" in obj and ("img" in obj or "capacity" in obj):
            fn(obj)
        for v in obj.values():
            walk_products(v, fn)


def main():
    cj_to_code, page_of, img_of = load_maps()
    stats = {"linked": 0, "unmatched": set(), "no_page": set()}
    fn = lambda n: rewrite_product(n, cj_to_code, page_of, img_of, stats)

    os.makedirs(OUT_DIR, exist_ok=True)

    # ① 逆引き（車種 → 商品）
    #    ベースプレート単品はアクセサリー（自サイトに個別ページが無い）ので
    #    書き換え対象にせず、配下のトップケースだけを自サイトへ向ける。
    rev = json.load(open(os.path.join(DIST, "reverse_data.json"), encoding="utf-8"))
    for info in rev.get("plates", {}).values():
        walk_products(info.get("topcases"), fn)
    for key in ("sidecases", "sidebags", "tankbags"):
        walk_products(rev.get(key), fn)
    json.dump(rev, open(os.path.join(OUT_DIR, "reverse_data.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

    # ② 順引き（商品 → 車種）は reverse_data.json から導出するため、
    #    topcase_*.json / sidecase_data.json はサイトへコピーしない
    #    （sidecase_data.json は SH23/35/36/38X しか含まず、TERRAサイドケースを
    #      カバーできないため。bikes[].side[].cases を使うほうが網羅的）
    copied = []

    # ③ 商品コード → 参照すべき順引きデータの対応表（商品ページ用）
    plate_of_code = {}
    for plate, info in rev["plates"].items():
        for t in info.get("topcases", []):
            if t.get("code"):
                plate_of_code.setdefault(t["code"], plate)
    side_codes = sorted({c for lst in rev["sidecases"].values() for it in lst if (c := it.get("code"))})
    bag_codes = sorted({c for lst in rev["sidebags"].values() for it in lst if (c := it.get("code"))})
    tank_codes = sorted({it["code"] for it in rev["tankbags"] if it.get("code")})
    index = {
        "topcasePlate": plate_of_code,          # TR55 → D1B591PA
        "sidecaseCodes": side_codes,            # 3P/4Pで探すコード
        "sidebagCodes": bag_codes,
        "tankbagCodes": tank_codes,
        "generatedFrom": "tools/fitment (ItemList_SHAD.csv)",
    }
    json.dump(index, open(os.path.join(OUT_DIR, "product_index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    size = sum(os.path.getsize(os.path.join(OUT_DIR, f)) for f in os.listdir(OUT_DIR)
               if f.endswith(".json"))
    print("=" * 62)
    print("適合検索データを site/data/fitment/ に出力")
    print("=" * 62)
    print("車種             : %d 件" % len(rev["bikes"]))
    print("ベースプレート   : %d 種" % len(rev["plates"]))
    print("商品リンク書換    : %d 箇所を自サイトの商品ページへ" % stats["linked"])
    print("トップケース対応  : %d モデル" % len(plate_of_code))
    print("サイドケース      : %s" % " / ".join(side_codes))
    print("サイドバッグ      : %s" % " / ".join(bag_codes))
    print("タンクバッグ      : %d モデル" % len(tank_codes))
    print("合計サイズ        : %.1f MB" % (size / 1048576))
    if stats["unmatched"]:
        print("\n⚠ カタログと突合できなかった品番: %d 件" % len(stats["unmatched"]))
        for cj in sorted(stats["unmatched"])[:10]:
            print("    %s" % cj)
    if stats["no_page"]:
        print("\n⚠ 商品ページが無いモデル（ECリンクのまま）: %s"
              % " / ".join(sorted(stats["no_page"])))


if __name__ == "__main__":
    main()
