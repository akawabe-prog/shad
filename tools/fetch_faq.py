#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD — FAQ を CustomJapan のAPIから取得
=============================================================================
FAQの原本はCJ側のAPIです。ブランドサイトは静的サイトなので、ここで取得して
JSONに落とし、`tools/build_faq.py` が商品ページへ書き出します。

    出力: site/data/faq/faq.json

■ 使い方
    python3 tools/fetch_faq.py            # 取得してJSONを更新
    python3 tools/fetch_faq.py --dry-run  # 取得して内容を表示するだけ

■ 認証（他のCJ APIと同じ手順）
    1) GET  https://api-i.customjapan.net/api/v1/init （Cache-Control: no-cache）
    2) GET  https://api-f.customjapan.net/api/v1/faq?slug=shad

    ※ブラウザから直接叩けません。CORSの許可オリジンが moto.customjapan.net だけで、
      セッションクッキーが無いと 500 が返ります。そのためビルド時に取得しています。
      将来 www.shad-japan.com が許可オリジンに追加されれば、fetch に切り替え可能です。

■ slug の使い分け（実データで確認済み）
    slug=shad          … ブランド全体（商品別も含めて全件返る）
    slug=shad-<code>   … その商品だけ（例 shad-sh40）

■ answer のHTMLについて
    CJ側は <span style="..."> で囲まれた状態で返ってきます。サイトのタイポグラフィに
    合わせるため、span と style を外し、<br> と <a> だけ残しています。
    EC商品ページへのリンクは自サイトの商品ページへ、旧サイトのパスは現行パスへ
    読み替えます（LINK_REWRITE。書き換えた件数は実行時に表示）。
=============================================================================
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
CARDS = os.path.join(SITE, "data", "catalog", "cards.json")
PRODUCTS = os.path.join(SITE, "data", "catalog", "products.json")
OUT_PATH = os.path.join(SITE, "data", "faq", "faq.json")

INIT_URL = "https://api-i.customjapan.net/api/v1/init"
FAQ_URL = "https://api-f.customjapan.net/api/v1/faq?slug=shad"
ORIGIN = "https://moto.customjapan.net"

# 旧サイト・EC のURL → 現行ブランドサイトのパス
LINK_REWRITE = {
    "https://www.shad-japan.com/shad_base/": "/store-locator",
    "http://www.shad-japan.com/shad_base/": "/store-locator",
}
# 読み替え後のリンク文字（元の文字が生URLのときだけ差し替える）
LINK_LABEL = {
    "/store-locator": "取扱店・SHAD BASEを探す",
}


def curl(args):
    res = subprocess.run(["curl", "-sS", "--max-time", "60"] + args,
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("curl failed: " + (res.stderr or "").strip())
    return res.stdout


def fetch_faq():
    cookie_file = os.path.join(tempfile.gettempdir(), "shad-cj-faq.cookies")
    head = ["-H", "Origin: " + ORIGIN, "-H", "Referer: " + ORIGIN + "/"]
    out = curl(["-c", cookie_file, INIT_URL, "-H", "Cache-Control: no-cache"] + head)
    if json.loads(out).get("result") != "success":
        raise RuntimeError("init API failed: " + out[:200])
    out = curl(["-b", cookie_file, FAQ_URL] + head)
    if not out.lstrip().startswith("["):
        raise RuntimeError("faq API がJSONを返しませんでした: " + out[:160])
    return json.loads(out)


def load_code_maps():
    """モデルコード集合と、品番 → モデルコードの対応"""
    codes = set(json.load(open(CARDS, encoding="utf-8")))
    cj_to_code = {}
    products = json.load(open(PRODUCTS, encoding="utf-8"))
    for code, entry in products.items():
        for v in entry.get("variants", []):
            if v.get("cjCode"):
                cj_to_code[str(v["cjCode"])] = code
    return codes, cj_to_code


def clean_answer(html, codes, stats):
    """span/style を外し、<br> と <a> だけ残す。リンクは自サイト向けに読み替える。"""
    s = html or ""
    s = re.sub(r"</?span[^>]*>", "", s)              # 装飾用の span を外す
    s = re.sub(r"\s*style\s*=\s*\"[^\"]*\"", "", s)  # 残った style 属性を外す
    s = re.sub(r"\s*style\s*=\s*'[^']*'", "", s)

    def fix_link(m):
        url, text = m.group(1), m.group(2)
        to, label = None, None
        if url in LINK_REWRITE:
            to, label = LINK_REWRITE[url], LINK_LABEL.get(LINK_REWRITE[url])
        else:
            # EC商品ページ（/i/CODE または /i/品番）は自サイトの商品ページへ
            m2 = re.match(r"https?://moto\.customjapan\.net/i/([A-Za-z0-9]+)/?$", url)
            if m2 and m2.group(1).upper() in codes:
                to = "/product/" + m2.group(1).lower()
                label = m2.group(1).upper() + "の商品ページ"
        if not to:
            # 外部リンクはそのまま別タブで開く
            if url.startswith("http"):
                return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (url, text)
            return m.group(0)
        stats.setdefault("rewritten", []).append((url, to))
        # リンク文字が生のURLのままだと旧サイトのURLが表示されてしまうので言い換える
        if label and re.match(r"^\s*https?://", re.sub(r"<[^>]+>", "", text)):
            text = label
        return '<a href="%s">%s</a>' % (to, text)

    s = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', fix_link, s, flags=re.S)
    s = re.sub(r"(<br\s*/?>\s*)+$", "", s.strip())   # 末尾の空行を落とす
    return s


def entry_codes(item, codes, cj_to_code):
    """このFAQが特定商品に紐づくなら、そのモデルコード一覧を返す"""
    found = []
    m = re.match(r"^shad-(.+)$", item.get("slug") or "")
    if m and m.group(1).upper() in codes:
        found.append(m.group(1).upper())
    for tok in (item.get("relItems") or "").split("_"):
        tok = tok.strip()
        if not tok:
            continue
        if tok.upper() in codes:
            found.append(tok.upper())
        elif tok in cj_to_code:
            found.append(cj_to_code[tok])
    seen, out = set(), []
    for c in found:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def main():
    dry = "--dry-run" in sys.argv
    codes, cj_to_code = load_code_maps()
    raw = fetch_faq()
    stats = {}

    items = []
    for it in raw:
        items.append({
            "id": str(it.get("id") or ""),
            "category": (it.get("classS") or "").strip(),   # 全般 / トップケース …
            "tags": [t for t in re.split(r"[,\s]+", it.get("tags") or "") if t],
            "question": (it.get("question") or "").strip(),
            "answer": clean_answer(it.get("answer"), codes, stats),
            "slug": it.get("slug") or "",
            "codes": entry_codes(it, codes, cj_to_code),
        })
    items.sort(key=lambda x: (x["category"] != "全般", x["category"], int(x["id"] or 0)))

    jst = timezone(timedelta(hours=9))
    payload = {
        "source": FAQ_URL,
        "fetchedAt": datetime.now(jst).replace(microsecond=0).isoformat(),
        "count": len(items),
        "items": items,
    }

    print("取得: %d件" % len(items))
    cats = {}
    for x in items:
        cats[x["category"]] = cats.get(x["category"], 0) + 1
    for k, v in sorted(cats.items(), key=lambda x: -x[1]):
        print("  %-12s %d件" % (k or "(カテゴリ無し)", v))
    linked = [x for x in items if x["codes"]]
    print("商品に紐づくFAQ: %d件" % len(linked))
    for x in linked:
        print("  %-10s %s" % ("/".join(x["codes"]), x["question"][:44]))
    if stats.get("rewritten"):
        print("リンクの読み替え:")
        for a, b in sorted(set(stats["rewritten"])):
            print("  %s → %s" % (a, b))

    if dry:
        print("\n--dry-run のためファイルは書き出していません")
        return
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("\n出力: site/data/faq/faq.json")


if __name__ == "__main__":
    main()
