#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 商品ページの <title>／meta description を商品マスターから作り直す（SEO）
=============================================================================
    python3 tools/apply_seo_meta.py            # site/product/*.html を更新（何度実行しても同じ結果）
    python3 tools/apply_seo_meta.py --dry      # 変更内容を表示だけ

・title       : 品番｜シリーズ＋カテゴリ 容量（一般名：バイク用リアボックス 等）— SHAD JAPAN
・description : 品番は容量・重量の素材製バイク用カテゴリ。ヘルメット収納・特長。定価（税込）。…（70〜120文字）
  「商品名で探す人」だけでなく「リアボックス」「パニアケース」「サドルバッグ」のような一般名で探す人にも
  検索結果で内容が伝わるようにするのが目的。本文（商品説明）は変更しない。
・データ源：site/data/catalog/products.json（マスター由来）、cards.json（ヘルメット数）、tools/product_tags.json
・build_product_max.py は head を引き継ぐので、後から実行しても上書きされない。
=============================================================================
"""
import os, re, sys, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
P = json.load(open(os.path.join(SITE, "data/catalog/products.json"), encoding="utf-8"))
C = json.load(open(os.path.join(SITE, "data/catalog/cards.json"), encoding="utf-8"))
T = json.load(open(os.path.join(ROOT, "tools/product_tags.json"), encoding="utf-8"))["products"]

# マスターのカテゴリ → 一般名（検索で使われる言い方）
GENERIC = [   # (マスターのカテゴリ/商品名に含まれる語, サイトでの呼び方, 検索で使われる別名)
    ("クラッシュバー", "クラッシュバーバッグ", ""),
    ("トップケース", "トップケース", "リアボックス"),
    ("サイドケース", "サイドケース", "パニアケース"),
    ("サイドバッグ", "サイドバッグ", "サドルバッグ"),
    ("タンクバッグ", "タンクバッグ", ""),
    ("シートバッグ", "シートバッグ", "ツーリングバッグ"),
    ("ダッフル", "防水ダッフルバッグ", ""),
    ("ロック", "ハンドルロック", ""),
    ("スクーター", "スクーターバッグ", ""),
    ("シート", "コンフォートシート", ""),
]
MATERIAL = {"alu": "アルミ", "pp": "PP（樹脂）", "abs": "ABS樹脂", "soft": ""}

def generic(code, v):
    cat = (v.get("category") or "") + " " + (v.get("name") or "")
    for key, jp, gen in GENERIC:
        if key in cat:
            return jp, gen
    return "バイク用ラゲッジ", ""

def helmet_text(code, v):
    card = C.get(code) or {}
    n = next((f["val"] for f in card.get("features", []) if f.get("label") == "ヘルメット"), None)
    spec = (v.get("spec") or "")
    m = re.search(r"([^\n。]*ヘルメット[^\n。]*)", spec)
    if m and len(m.group(1)) < 60:
        return m.group(1).strip("※ ").replace("収納可能", "収納可") 
    if n:
        return "ヘルメット%s個収納" % n.replace("×", "")
    return ""

def feature_text(code):
    tags = T.get(code, [])
    out = []
    if "terralock" in tags: out.append("TERRA Lock")
    if "smartlock" in tags: out.append("スマートロック")
    if "expandable" in tags: out.append("可変容量")
    if "waterproof" in tags: out.append("防水")
    if "click" in tags: out.append("クリックシステム1秒脱着")
    return "・".join(out)

def build(code):
    e = P[code]; v = e["variants"][0]
    jp, gen = generic(code, v)
    series = (v.get("series") or "").strip()
    series = "" if series in ("", "トップケース", "サイドケース", "バッグ") else series
    cap = v.get("capacity") or ""
    cap_s = cap if cap and not cap.startswith("64L") and not cap.startswith("60L") else cap.split("(")[0]
    card_jp = (C.get(code) or {}).get("jp") or (series + " " + jp).strip()
    # title
    title = "%s｜%s%s%s — SHAD JAPAN" % (code if code != "SH40CG" else "SH40 CARGO", card_jp, (" " + cap_s) if cap_s else "", ("（%s）" % gen) if gen else "")
    # description
    mat = MATERIAL.get(next((t for t in T.get(code, []) if t in MATERIAL), ""), "")
    w = re.sub(r"^(本体|質量|重量)[：:]\s*", "", (v.get("weight") or "").strip())
    w = re.sub(r"(\d)\.(\d)\.kg", r"\1.\2kg", w)
    parts = []
    head = code + "は"
    head += ("%s・" % cap_s if cap_s else "") + ("%sの" % w if w else "")
    head += (mat + "製" if mat else "") + "バイク用" + jp
    if gen:
        head += "（%s）" % gen
    parts.append(head + "。")
    h = helmet_text(code, v)
    if h: parts.append(h + "。")
    f = feature_text(code)
    if f: parts.append(f + "。")
    price = e.get("priceMin")
    if price: parts.append("定価¥%s（税込）。" % format(price, ","))
    parts.append("SHAD日本総代理店カスタムジャパンの公式サイト。")
    desc = "".join(parts)
    if len(desc) > 125:
        desc = desc.replace("SHAD日本総代理店カスタムジャパンの公式サイト。", "SHAD公式。")
    return title, desc

def apply(path, title, desc, dry):
    s = open(path, encoding="utf-8").read()
    t, d = html.escape(title, quote=True), html.escape(desc, quote=True)
    n = s
    n = re.sub(r"<title>.*?</title>", "<title>%s</title>" % t, n, count=1, flags=re.S)
    n = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + d + m.group(2), n, count=1)
    n = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + t + m.group(2), n, count=1)
    n = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + d + m.group(2), n, count=1)
    n = re.sub(r'(<meta name="twitter:title" content=")[^"]*(")', lambda m: m.group(1) + t + m.group(2), n, count=1)
    n = re.sub(r'(<meta name="twitter:description" content=")[^"]*(")', lambda m: m.group(1) + d + m.group(2), n, count=1)
    if n != s and not dry:
        open(path, "w", encoding="utf-8").write(n)
    return n != s

def main():
    dry = "--dry" in sys.argv
    changed = 0
    for code in P:
        path = os.path.join(SITE, "product", code.lower() + ".html")
        if not os.path.exists(path):
            continue
        title, desc = build(code)
        if apply(path, title, desc, dry):
            changed += 1
        if dry:
            print(code, "|", title, "|", desc, "(%d字)" % len(desc))
    print("商品ページの title/description 更新：%d ページ%s" % (changed, "（dry）" if dry else ""))

if __name__ == "__main__":
    main()
