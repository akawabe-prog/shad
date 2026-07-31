#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 容量（サイズ）をカスタムジャパンAPIから取得
=============================================================================
商品マスターCSVの「容量」欄は空のことがあるため、EC本体のAPIから
正式な容量表記を取得して site/data/catalog/api_sizes.json に保存します。
build_catalog.py がこのファイルを読み、容量欄が空の商品を補完します。

■ 使い方
    python3 tools/fetch_api_sizes.py          # 全モデルを取得
    python3 tools/fetch_api_sizes.py SH38X    # モデルコードを指定して取得

■ 認証（社内ドキュメント準拠）
    1) GET  https://api-i.customjapan.net/api/v1/init
       → guid / authorization / cid が Cookie にセットされる（Cache-Control: no-cache 必須）
    2) POST https://api-e.customjapan.net/api/v1/items  {"ids":[品番,...]}
       → 1) の Cookie を付けて実行

■ 取得する値
    size.main.values … 例 ["23-32L/23-32L"]（片側の可変容量を左右分）
    size.sub         … 例 "合計：46-64L"
    どちらもそのまま保存し、表示側で使い分けます。
=============================================================================
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "site", "data", "catalog", "products.json")
OUT_PATH = os.path.join(ROOT, "site", "data", "catalog", "api_sizes.json")
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
    if data.get("result") != "success":
        raise RuntimeError("items API failed: " + out[:200])
    return data.get("data") or []


def main():
    products = json.load(open(CATALOG, encoding="utf-8"))
    want = [c.upper() for c in sys.argv[1:] if not c.startswith("-")]
    codes = [c for c in products if not want or c.upper() in want]

    id_to_code = {}
    for code in codes:
        for v in products[code]["variants"]:
            if v.get("cjCode"):
                id_to_code[str(v["cjCode"])] = code

    cookie_file = os.path.join(tempfile.gettempdir(), "shad-cj-api.cookies")
    state = init_session(cookie_file)
    print("init OK（ログイン状態: %s）" % ("あり" if state.get("isLoggedIn") else "なし"))

    ids = list(id_to_code)
    items = []
    for i in range(0, len(ids), BATCH):
        items += fetch_items(cookie_file, ids[i:i + BATCH])
        print("  %d/%d 件取得" % (min(i + BATCH, len(ids)), len(ids)))

    # 既存の内容を引き継いで、取得できた品番だけ更新する
    out = {}
    if os.path.exists(OUT_PATH):
        out = json.load(open(OUT_PATH, encoding="utf-8")).get("byCjCode", {})

    for it in items:
        cj = str(it.get("id") or "")
        size = it.get("size") or {}
        main = (size.get("main") or {}).get("values") or []
        out[cj] = {
            "code": id_to_code.get(cj, ""),
            "name": it.get("name") or "",
            "sizeMain": main,
            "sizeSub": size.get("sub") or "",
            "unit": it.get("unit") or "",
        }

    payload = {
        "source": "GET %s → POST %s" % (INIT_URL, ITEMS_URL),
        "count": len(out),
        "byCjCode": dict(sorted(out.items())),
    }
    json.dump(payload, open(OUT_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("\n出力: site/data/catalog/api_sizes.json（%d品番）\n" % len(out))
    print("%-8s %-10s %-20s %-16s %s" % ("CODE", "品番", "サイズ(main)", "合計(sub)", "単位"))
    print("-" * 82)
    for cj, v in sorted(out.items(), key=lambda kv: kv[1]["code"]):
        if want and v["code"].upper() not in want:
            continue
        print("%-8s %-10s %-20s %-16s %s"
              % (v["code"], cj, "/".join(v["sizeMain"])[:20], v["sizeSub"][:16], v["unit"]))


if __name__ == "__main__":
    main()
