#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD（カスタムジャパン版）— 販売価格・在庫をECのAPIから取得
=============================================================================
カスタムジャパン版サイト（shad.customjapan.net）は、定価ではなく
**実際の販売価格と在庫**を出します。値はECのAPIから取得します。

    出力: site/data/ec/api_prices.json
      { "byCjCode": { "27705902": {
            "code": "TR55",              モデルコード（本体商品のみ）
            "name": "TR55 TERRA トップケース 55L",
            "listTaxIn": 88000,          定価（税込）
            "saleTaxIn": 57178,          販売価格（税込）
            "statusCd": "SE",            在庫コード
            "statusTxt": "◯在庫あり",
            "maxQuantity": 0,
            "notForSale": false, "outlet": false
      } } }

■ 使い方
    python3 tools/fetch_api_prices.py              # 本体＋アクセサリー
    python3 tools/fetch_api_prices.py --fitting    # フィッティングキットも含める
    python3 tools/fetch_api_prices.py TR55         # モデル指定

■ 認証（社内ドキュメント準拠 / fetch_api_sizes.py と同じ）
    1) GET  https://api-i.customjapan.net/api/v1/init （Cache-Control: no-cache）
    2) POST https://api-e.customjapan.net/api/v1/items  {"ids":[品番,...]}

■ 注意
    価格・在庫は変動します。公開前に実行して最新化してください（毎日でも可）。
=============================================================================
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
CATALOG = os.path.join(SITE, "data", "catalog", "products.json")
ACCESSORIES = os.path.join(SITE, "data", "catalog", "accessories.json")
FITTING = os.path.join(SITE, "data", "catalog", "fitting.json")
OUT_PATH = os.path.join(SITE, "data", "ec", "api_prices.json")

INIT_URL = "https://api-i.customjapan.net/api/v1/init"
ITEMS_URL = "https://api-e.customjapan.net/api/v1/items"
ORIGIN = "https://moto.customjapan.net"
BATCH = 50


def curl(args):
    res = subprocess.run(["curl", "-sS", "--max-time", "60"] + args,
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("curl failed: " + (res.stderr or "").strip())
    return res.stdout


def init_session(cookie_file):
    out = curl(["-c", cookie_file, INIT_URL,
                "-H", "Origin: " + ORIGIN, "-H", "Referer: " + ORIGIN + "/",
                "-H", "Cache-Control: no-cache"])
    data = json.loads(out)
    if data.get("result") != "success":
        raise RuntimeError("init API failed: " + out[:200])
    return data["data"]


def fetch_items(cookie_file, ids):
    out = curl(["-b", cookie_file, "-X", "POST", ITEMS_URL,
                "-H", "Origin: " + ORIGIN, "-H", "Referer: " + ORIGIN + "/",
                "-H", "Content-Type: application/json",
                "--data", json.dumps({"ids": list(ids)})])
    data = json.loads(out)
    # 一部の品番（廃番・取り寄せなど）が混ざると result は "warning" になるが、
    # 取得できた分は data に入っているのでそのまま使う。
    if data.get("result") not in ("success", "warning"):
        raise RuntimeError("items API failed: " + out[:200])
    if data.get("result") == "warning":
        print("  ※一部の品番で警告（取得できた分だけ反映します）")
    return data.get("data") or []


def collect_ids(want, with_fitting):
    """品番 → モデルコード（本体商品以外は空）"""
    id_to_code = {}
    products = json.load(open(CATALOG, encoding="utf-8"))
    for code, entry in products.items():
        if want and code.upper() not in want:
            continue
        for v in entry.get("variants", []):
            if v.get("cjCode"):
                id_to_code[str(v["cjCode"])] = code
    if want:
        return id_to_code

    for path in (ACCESSORIES, FITTING if with_fitting else None):
        if not path or not os.path.exists(path):
            continue
        rows = json.load(open(path, encoding="utf-8"))
        for it in rows if isinstance(rows, list) else []:
            if it.get("cjCode"):
                id_to_code.setdefault(str(it["cjCode"]), "")
    return id_to_code


def main():
    args = [a for a in sys.argv[1:]]
    with_fitting = "--fitting" in args
    want = [a.upper() for a in args if not a.startswith("-")]

    id_to_code = collect_ids(want, with_fitting)
    ids = list(id_to_code)
    if not ids:
        raise SystemExit("対象の品番がありません")

    cookie_file = os.path.join(tempfile.gettempdir(), "shad-cj-api.cookies")
    state = init_session(cookie_file)
    print("init OK（ログイン状態: %s）" % ("あり" if state.get("isLoggedIn") else "なし"))

    items = []
    for i in range(0, len(ids), BATCH):
        items += fetch_items(cookie_file, ids[i:i + BATCH])
        print("  %d/%d 件取得" % (min(i + BATCH, len(ids)), len(ids)))

    out = {}
    if os.path.exists(OUT_PATH):
        out = json.load(open(OUT_PATH, encoding="utf-8")).get("byCjCode", {})

    for it in items:
        cj = str(it.get("id") or "")
        price = it.get("price") or {}
        lst = (price.get("list") or {}).get("taxIn")
        sale = ((price.get("regular") or {}).get("pc") or {}).get("taxIn")
        st = it.get("status") or {}
        out[cj] = {
            "code": id_to_code.get(cj, ""),
            "name": it.get("name") or "",
            "listTaxIn": lst,
            "saleTaxIn": sale,
            "statusCd": st.get("cd") or "",
            "statusTxt": st.get("txt") or "",
            "maxQuantity": it.get("maxQuantity") or 0,
            "notForSale": bool(it.get("isNotForSale")),
            "outlet": bool(it.get("isOutlet")),
        }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    json.dump({
        "source": "GET %s → POST %s" % (INIT_URL, ITEMS_URL),
        "count": len(out),
        "byCjCode": dict(sorted(out.items())),
    }, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    got = [out[str(i)] for i in ids if str(i) in out]
    priced = [v for v in got if v.get("saleTaxIn")]
    print("\n出力: site/data/ec/api_prices.json（%d品番）" % len(out))
    print("うち販売価格あり: %d / %d" % (len(priced), len(got)))
    print("\n%-8s %-10s %-30s %10s %10s  %s"
          % ("CODE", "品番", "商品名", "定価", "販売価格", "在庫"))
    print("-" * 96)
    for v in sorted(got, key=lambda x: (x["code"] or "zz", x["name"]))[:24]:
        print("%-8s %-10s %-30s %10s %10s  %s"
              % (v["code"] or "-", "", v["name"][:30],
                 v["listTaxIn"] or "-", v["saleTaxIn"] or "-", v["statusTxt"]))


if __name__ == "__main__":
    main()
