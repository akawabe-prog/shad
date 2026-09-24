#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 商品ページ／一覧カード と 商品マスター（products.json）の食い違いチェック
=============================================================================
公開前に走らせて、ページに書かれている数値・表記がマスターとズレていないかを一覧します。
（ページの文言は手で書いた部分が多く、マスター更新で自動では直らないため）

    python3 tools/check_master_consistency.py            # 全商品
    python3 tools/check_master_consistency.py TR48 SH44  # 型番を絞る

■ チェック項目
    weight   : ページのスペック「質量」とマスターの weight（バリエーション違いは全部並べて比較）
    warranty : 保証文（1年保証の中身）がマスターの remarks と一致するか（黄色／青色シール等）
    notes    : Notes（注意事項）ブロックがあるか、マスターに注意事項があるのに載っていないか
    helmet   : ヘルメットアイコン（一覧・詳細）と、マスターの仕様欄「ヘルメットを収納することはできません」等の矛盾
    icons    : 一覧カード（PRODUCTS）と詳細ページのアイコン内容（ヘルメット個数）が一致するか
    colors   : 一覧カードの colors とマスターの色バリエーション数（サイズ・車種違いは対象外として警告のみ）
    words    : ページ本文に出てくる kg 表記のうち、マスターに無い数値（3.7kg など古い数値の残り）

終了コードは常に 0（レポート用途）。結果は目で確認して、直すべきものだけ直してください。
=============================================================================
"""
import json, os, re, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
P = json.load(open(os.path.join(SITE, "data", "catalog", "products.json"), encoding="utf-8"))
s = open(os.path.join(SITE, "products.html"), encoding="utf-8").read()
CARDS = {x["code"]: x for x in json.loads(re.search(r"var PRODUCTS=(\[.*?\]);", s, re.S).group(1))}

def text(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", h))

def norm(t): return re.sub(r"\s+", "", t or "")

def check(code):
    path = os.path.join(SITE, "product", code.lower() + ".html")
    if not os.path.exists(path):
        return [("page", "商品ページが無い")]
    page = open(path, encoding="utf-8").read()
    body = text(page)
    e = P.get(code) or {}
    vs = e.get("variants") or []
    v0 = vs[0] if vs else {}
    out = []

    # weight
    m = re.search(r"質量</th>\s*<td[^>]*>(.*?)</td>", page, re.S)
    page_w = norm(text(m.group(1))) if m else ""
    master_w = sorted({norm(v.get("weight")) for v in vs if norm(v.get("weight"))})
    if master_w and not any(w in page_w for w in master_w):
        out.append(("weight", f"ページ『{page_w or '（記載なし）'}』 / マスター {master_w}"))
    elif master_w and len(master_w) > 1 and not all(w in page_w for w in master_w):
        out.append(("weight", f"バリエーションで質量が違う：ページ『{page_w}』 / マスター {master_w}"))

    # warranty
    m = re.search(r'warranty-body">(.*?)</div>', page, re.S) or re.search(r"1年保証</p>\s*<p[^>]*>(.*?)</p>", page, re.S)
    if m and v0.get("remarks"):
        pw, mw = norm(text(m.group(1))), norm(v0["remarks"]).replace("保証期間：1年", "保証期間：1年。")
        if pw.replace("。", "") != norm(v0["remarks"]).replace("。", ""):
            hint = "黄色/青色" if ("黄色" in pw) != ("黄色" in mw) else "文言"
            out.append(("warranty", f"保証文がマスター remarks と不一致（{hint}）"))

    # notes
    has_notes = ">Notes<" in page
    if v0.get("note") and not has_notes:
        out.append(("notes", "マスターに注意事項があるのにページに Notes が無い"))
    if not v0.get("note") and not has_notes:
        out.append(("notes", "注意事項なし（マスターにも無い）"))
    if v0.get("note") and has_notes and norm(v0["note"])[:20] not in norm(body):
        out.append(("notes", "Notes の中身がマスターの注意事項と違う（先頭20文字が見つからない）"))

    # helmet
    spec_all = " ".join((v.get("spec") or "") + (v.get("descSub") or "") for v in vs)
    page_helmet = re.search(r"<b>ヘルメット</b><span>×(\d)", page)
    card_helmet = next((f.get("val") for f in (CARDS.get(code) or {}).get("features", []) if f.get("label") == "ヘルメット"), None)
    if "収納することはできません" in spec_all and (page_helmet or card_helmet):
        out.append(("helmet", "マスター仕様『ヘルメットを収納することはできません』なのにヘルメットアイコンがある"))
    if page_helmet and card_helmet and ("×" + page_helmet.group(1)) != card_helmet:
        out.append(("icons", f"ヘルメット個数：詳細 ×{page_helmet.group(1)} / 一覧 {card_helmet}"))
    elif bool(page_helmet) != bool(card_helmet):
        out.append(("icons", f"ヘルメットアイコン：詳細 {'あり' if page_helmet else 'なし'} / 一覧 {'あり' if card_helmet else 'なし'}"))

    # colors
    card = CARDS.get(code)
    if card is not None and vs:
        n = len({(v.get("color") or "") for v in vs})
        if card.get("colors") not in (n, 0) and code not in ("SEAT", "LOCK", "E48", "TR36", "TR47"):
            out.append(("colors", f"一覧 colors={card.get('colors')} / マスター色数={n}"))

    # words: kg 数値
    kgs = {k for k in re.findall(r"(\d+(?:\.\d+)?)\s*kg", body)}
    master_nums = set(re.findall(r"(\d+(?:\.\d+)?)", " ".join((v.get("weight") or "") + " " + (v.get("spec") or "") for v in vs)))
    # FAQ・関連商品・耐荷重などは除く：質量表の値と一致しない「約x.xkg」表記だけ拾う
    odd = {k for k in kgs if k not in master_nums and re.search(r"約?" + re.escape(k) + r"\s*kg", body) and not re.search(r"耐荷重[^。]{0,12}" + re.escape(k), body)}
    odd -= {"5", "6", "8", "10", "3", "2"}   # 耐荷重の定番値
    if odd:
        out.append(("words", f"マスターに無い kg 表記：{sorted(odd)}"))
    return out

codes = [c.upper() for c in sys.argv[1:]] or sorted(CARDS.keys())
total = 0
for code in codes:
    issues = check(code)
    if issues:
        total += len(issues)
        print(f"## {code}")
        for k, msg in issues:
            print(f"   [{k:8s}] {msg}")
print(f"\n{len(codes)} 商品を確認、指摘 {total} 件")
