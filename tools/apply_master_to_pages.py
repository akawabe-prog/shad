#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 商品マスター由来のブロックを全商品ページに反映する
=============================================================================
スペック表・Notes（注意事項）・保証文（1年保証の中身）を products.json から作り直して
site/product/*.html に書き込みます。旧テンプレート／MAXテンプレートどちらにも対応、何度実行しても同じ結果です。

    python3 tools/build_catalog.py            # ① マスター → products.json（上書きルール適用）
    python3 tools/apply_master_to_pages.py    # ② products.json → 商品ページのスペック/Notes/保証文
    python3 tools/audit_master.py             # ③ 残りの食い違い（手書きの本文・アイコン等）を監査

    python3 tools/apply_master_to_pages.py TR48 SH44   # 型番を絞る

■ 触る場所（それ以外の本文・画像・ストーリーは変更しない）
    旧テンプレート : <h2>Spec</h2> の <table>、<h2>Notes</h2> の段落、.warranty-body
    MAX           : <table class="pd-spec">、.pd-notes、.warranty-body、アコーディオン内の保証文
=============================================================================
"""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from master_spec import SITE, load_products, spec_table_html, notes_html, warranty_html, note_text

LEGACY_TABLE = re.compile(r'(<h2 class="sec-ttl sec-ttl-quiet">Spec</h2>\s*<table class="w-full mt-5 text-\[14px\] table-fixed">).*?(</table>)', re.S)
MAX_TABLE = re.compile(r'(<table class="pd-spec">).*?(</table>)', re.S)
LEGACY_NOTES = re.compile(r'(<h2 class="sec-ttl sec-ttl-quiet(?: mt-10)?">Notes</h2>\s*)<p[^>]*>.*?</p>', re.S)
MAX_NOTES = re.compile(r'<div class="pd-notes">.*?</div></div>|<div class="pd-notes"><h3 class="pd-notes-h">Notes</h3><p>.*?</p></div>', re.S)
WARRANTY_BODY = re.compile(r'(<div class="warranty-body">).*?(</div>)', re.S)
WARRANTY_ACC = re.compile(r'(1年保証</p>\s*<p[^>]*>).*?(</p>)', re.S)

def apply(path):
    code = os.path.basename(path)[:-5].upper()
    s = open(path, encoding="utf-8").read()
    if code not in load_products():
        return code, "マスターに無い（スキップ）"
    is_max = 'id="pdTop"' in s
    changed = []
    # ① スペック表
    rows = spec_table_html(code, "max" if is_max else "legacy")
    rx = MAX_TABLE if is_max else LEGACY_TABLE
    s2, k = rx.subn(lambda m: m.group(1) + rows + m.group(2), s, count=1) if rows else (s, 0)
    if k and s2 != s: changed.append("spec")
    s = s2
    # ② Notes
    nh = notes_html(code, "max" if is_max else "legacy")
    if is_max:
        s2, k = MAX_NOTES.subn(lambda m: nh, s, count=1)
        if not k and nh:
            s2, k = re.subn(r'(<p class="pd-note">.*?</p>)', lambda m: m.group(1) + nh, s, count=1, flags=re.S)
    else:
        s2, k = LEGACY_NOTES.subn(lambda m: m.group(1) + nh.split('</h2>', 1)[1], s, count=1)
        if not k and nh:   # Description 列の末尾（Spec 列の手前）に追加
            k2 = s.find('<h2 class="sec-ttl sec-ttl-quiet">Spec</h2>'); k2 = s.rfind("</div>", 0, k2) if k2 > 0 else -1
            if k2 > 0:
                s2, k = s[:k2] + nh + "\n  " + s[k2:], 1
    if k and s2 != s: changed.append("notes")
    s = s2
    # ③ 保証文（全コピー）
    w = warranty_html(code)
    s2 = WARRANTY_BODY.sub(lambda m: m.group(1) + w + m.group(2), s)
    s2 = WARRANTY_ACC.sub(lambda m: m.group(1) + w + m.group(2), s2)
    if s2 != s: changed.append("warranty")
    s = s2
    if changed:
        open(path, "w", encoding="utf-8").write(s)
    return code, "更新: " + ", ".join(changed) if changed else "変更なし"

if __name__ == "__main__":
    codes = [c.upper() for c in sys.argv[1:]]
    files = sorted(glob.glob(os.path.join(SITE, "product", "*.html")))
    n = 0
    for f in files:
        code = os.path.basename(f)[:-5].upper()
        if codes and code not in codes:
            continue
        code, msg = apply(f)
        if msg != "変更なし":
            n += 1; print("%-7s %s" % (code, msg))
    print("\n%d ページを更新" % n)
