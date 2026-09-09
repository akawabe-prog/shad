#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD — 商品ページのコピー（キャッチ・本文）を書き出す
=============================================================================
各商品の文言を1行1商品でCSVに書き出します。スプレッドシートの
「ProductCatchcopy」シートにそのまま貼り付け／インポートして使えます。

    出力: data-source/product_catchcopy.csv（UTF-8 BOM付き＝Excel/Sheetsで文字化けしない）

■ 使い方
    python3 tools/export_product_copy.py

■ 書き出す項目
    型番 / 表示名 / シリーズ / カテゴリ名 / 容量 / URL
    キャッチコピー（一覧カード・商品ページのリード。原本は products.html の PRODUCTS）
    ストーリー見出し1〜3・本文1〜3（商品ページの帯。原本は各 product/*.html）
    Description（商品説明。マスターCSV由来）
    注記（ベースプレート別売などの但し書き）
=============================================================================
"""

import csv
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
CARDS = os.path.join(SITE, "data", "catalog", "cards.json")
PRODUCTS = os.path.join(SITE, "data", "catalog", "products.json")
PRODUCT_DIR = os.path.join(SITE, "product")
OUT = os.path.join(ROOT, "data-source", "product_catchcopy.csv")
SITE_URL = "https://www.shad-japan.com"


def text(html):
    """タグを外して1行に整える"""
    s = re.sub(r"<br\s*/?>", " ", html or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))
    return re.sub(r"[ \t]+", " ", s).strip()


def blocks(page):
    """商品ページの帯（kick / 見出し / 本文）を出てくる順に返す"""
    out = []
    for m in re.finditer(r'class="lp-block-tx"(.*?)</div>', page, re.S):
        seg = m.group(1)
        def pick(cls):
            mm = re.search(r'class="[^"]*%s[^"]*"[^>]*>(.*?)</\w+>' % cls, seg, re.S)
            return text(mm.group(1)) if mm else ""
        out.append((pick("lp-block-kick"), pick("lp-block-h"), pick("lp-block-p")))
    return out


def section(page, title):
    """<h2>Description</h2> などの直後にある本文をまとめて返す"""
    m = re.search(r'>%s</h2>(.*?)(?:<h2|</section>)' % re.escape(title), page, re.S)
    if not m:
        return ""
    parts = re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S)
    return "\n".join(t for t in (text(p) for p in parts) if t)


def notes_section(page):
    """Description が無いページ（後から追加した商品）は「Notes」に但し書きが入る"""
    return section(page, "Notes")


def master_copy():
    """商品マスター由来の全文（一覧カードのコピーは表示用に切り詰めてあるため）"""
    if not os.path.exists(PRODUCTS):
        return {}
    out = {}
    for code, e in json.load(open(PRODUCTS, encoding="utf-8")).items():
        v = (e.get("variants") or [{}])[0]
        out[code] = {
            "正式名称": v.get("name") or e.get("name") or "",
            "キャッチ全文": v.get("catch") or "",
            "仕様": v.get("spec") or "",
            "付属品": v.get("included") or "",
            "注意事項": v.get("note") or "",
            "備考": v.get("remarks") or "",
        }
    return out


def main():
    cards = json.load(open(CARDS, encoding="utf-8"))
    master = master_copy()
    rows = []
    for code in sorted(cards, key=lambda c: (cards[c].get("series") or "", c)):
        c = cards[code]
        path = os.path.join(PRODUCT_DIR, code.lower() + ".html")
        page = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        bs = blocks(page)
        desc = section(page, "Description") or notes_section(page)
        # 但し書き（Descriptionの後半にある「・」始まりの行）は分けて持たせる
        body, notes = [], []
        for line in desc.split("\n"):
            (notes if line.startswith("・") or line.startswith("※") else body).append(line)
        m = master.get(code, {})
        row = {
            "型番": code,
            "表示名": c.get("label") or code,
            "正式名称": m.get("正式名称", ""),
            "シリーズ": c.get("series") or "",
            "カテゴリ名": c.get("jp") or "",
            "容量": c.get("cap") or "",
            "キャッチコピー（全文）": m.get("キャッチ全文") or c.get("copy") or "",
            "一覧カードのコピー": c.get("copy") or "",
            "商品説明": " ".join(body).strip(),
            "注記": " ".join(notes).strip(),
            "仕様": m.get("仕様", "").replace("\n", " / "),
            "付属品": m.get("付属品", "").replace("\n", " / "),
            "注意事項（マスター）": m.get("注意事項", "").replace("\n", " / "),
            "URL": "%s/product/%s" % (SITE_URL, code.lower()),
            "ページ有無": "あり" if page else "なし",
        }
        for i in range(3):
            k, h, p = bs[i] if i < len(bs) else ("", "", "")
            row["ストーリー%d ラベル" % (i + 1)] = k
            row["ストーリー%d 見出し" % (i + 1)] = h
            row["ストーリー%d 本文" % (i + 1)] = p
        rows.append(row)

    cols = ["型番", "表示名", "正式名称", "シリーズ", "カテゴリ名", "容量",
            "キャッチコピー（全文）", "一覧カードのコピー",
            "ストーリー1 ラベル", "ストーリー1 見出し", "ストーリー1 本文",
            "ストーリー2 ラベル", "ストーリー2 見出し", "ストーリー2 本文",
            "ストーリー3 ラベル", "ストーリー3 見出し", "ストーリー3 本文",
            "商品説明", "注記", "仕様", "付属品", "注意事項（マスター）", "URL", "ページ有無"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print("出力: data-source/product_catchcopy.csv（%d商品）" % len(rows))
    nostory = [r["型番"] for r in rows if not r["ストーリー1 見出し"]]
    nocatch = [r["型番"] for r in rows if not r["キャッチコピー（全文）"]]
    print("  キャッチが空の商品    : %d件 %s" % (len(nocatch), " ".join(nocatch)))
    nodesc = [r["型番"] for r in rows if not r["商品説明"]]
    print("  ストーリーの帯が無い商品: %d件 %s" % (len(nostory), " ".join(nostory)))
    print("  商品説明が空の商品    : %d件 %s" % (len(nodesc), " ".join(nodesc)))


if __name__ == "__main__":
    main()
