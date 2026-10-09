#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 製品一覧の並び順用「最大容量」(capSort) を PRODUCTS に書き込む
=============================================================================
    python3 tools/apply_cap_sort.py      # 商品マスター更新（build_catalog.py）のあとに実行。何度実行しても同じ結果

並び順のルール（site/products.html の sortList）：
  TERRA（トップ→ツーリングバッグ→サイドケース→サイドバッグ→タンクバッグ）→ EXPANDABLE（トップ→サイド）
  → トップケース → サイドケース → サイドバッグ → タンクバッグ → その他。各グループ内は capSort（最大容量）の
  大きい順。「すべて」でもカテゴリ・容量・素材・機能で絞り込んだときでも、同じルールで並ぶ。

capSort の決め方（products.json の容量表記から）：
  ・左右セット品は左右合計（例：TR27 27L/27L → 54、SH36 合計72L → 72、TR40 64L(片側32L) → 64）
  ・可変容量は最大値（例：SH58X 46-58L → 58、SH38X 合計46-64L → 64）
  ・それ以外は容量の数値
=============================================================================
"""
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "site", "products.html")
P = json.load(open(os.path.join(ROOT, "site", "data", "catalog", "products.json"), encoding="utf-8"))

def nums(s):
    return [int(x) for x in re.findall(r"\d+", s or "")]

def cap_sort(code):
    e = P.get(code)
    if not e:
        return None
    best = 0
    for v in e["variants"]:
        spec = v.get("capacitySpec") or v.get("capacity") or ""
        total = v.get("capacityTotal") or ""
        per = v.get("capacityPerUnit") or []
        cand = nums(total) + nums(spec)
        # 「27L/27L」のように左右の容量だけが書かれているセット品は合計する
        for u in per:
            parts = [nums(x) for x in str(u).split("/") if nums(x)]
            if len(parts) >= 2:
                cand.append(sum(max(p) for p in parts))
        if cand:
            best = max(best, max(cand))
    return best or None

def main():
    s = open(HTML, encoding="utf-8").read()
    m = re.search(r"var PRODUCTS=(\[.*?\]);\n", s, re.S)
    prods = json.loads(m.group(1))
    for p in prods:
        cs = cap_sort(p["code"])
        if cs: p["capSort"] = cs
        else: p.pop("capSort", None)
    s = s[:m.start(1)] + json.dumps(prods, ensure_ascii=False) + s[m.end(1):]
    open(HTML, "w", encoding="utf-8").write(s)
    print("capSort を %d 商品に書き込み" % sum(1 for p in prods if p.get("capSort")))

if __name__ == "__main__":
    main()
