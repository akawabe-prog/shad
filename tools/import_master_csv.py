#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 商品マスターが CSV で届いたときの取り込み（EC 出力の文字化け復元つき）
=============================================================================
    python3 tools/import_master_csv.py ~/Downloads/ItemList_xxxx.csv

・data-source/ItemList_SHAD.csv を退避（_<日付>_backup.csv）してから新しい CSV に置き換える
・EC の CSV 出力は「～」「－」などの記号が「?」に化けることがある。
  同じ品番・同じ列で、旧 CSV の値と「? の位置以外が一致」する場合は旧 CSV の文字で復元する
  （復元できなかった「?」は一覧に出すので、手で確認する）
・xlsx で届いたときは tools/xlsx_to_master_csv.py を使う
=============================================================================
"""
import sys, os, csv, shutil, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data-source", "ItemList_SHAD.csv")

def restore(new, old):
    """new の '?' を old の同じ位置の文字で埋める（長さが同じで、? 以外が一致するときだけ）"""
    if "?" not in new or not old or len(new) != len(old):
        return new, False
    out = []
    for a, b in zip(new, old):
        if a == "?":
            if b == "?" or ord(b) < 128:
                return new, False
            out.append(b)
        elif a != b:
            return new, False
        else:
            out.append(a)
    return "".join(out), True

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    new_rows = list(csv.DictReader(open(src, encoding="cp932", newline="")))
    old_rows = list(csv.DictReader(open(OUT, encoding="cp932", newline=""))) if os.path.exists(OUT) else []
    old = {r["品番"]: r for r in old_rows}
    fixed, left = 0, []
    for r in new_rows:
        o = old.get(r["品番"])
        for k, v in r.items():
            if "?" in (v or ""):
                nv, ok = restore(v, (o or {}).get(k, ""))
                if ok:
                    r[k] = nv; fixed += 1
                elif o is not None and k not in ("商品名前", "商品名元"):
                    left.append((r["品番"], k, v[:50].replace("\n", " ")))
    if os.path.exists(OUT):
        bk = OUT.replace(".csv", "_%s_backup.csv" % datetime.date.today().strftime("%y%m%d"))
        shutil.copy(OUT, bk); print("退避:", os.path.relpath(bk, ROOT))
    with open(OUT, "w", encoding="cp932", newline="", errors="replace") as f:
        w = csv.DictWriter(f, fieldnames=list(new_rows[0].keys()))
        w.writeheader(); w.writerows(new_rows)
    print("取り込み: %d 行 / '?' を旧CSVから復元: %d セル / 復元できなかった '?': %d セル" % (len(new_rows), fixed, len(left)))
    for cj, k, v in left[:20]:
        print("  要確認 %s [%s] %s" % (cj, k, v))

if __name__ == "__main__":
    main()
