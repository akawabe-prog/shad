# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 商品マスター（products.json）から商品ページの「マスター由来ブロック」を作る共通部品
=============================================================================
スペック表・Notes（注意事項）・保証文は、ページに手で書かず必ずここから生成します。
（build_product_max.py／apply_master_to_pages.py／audit_master.py が共通で使う）

    from master_spec import load_products, spec_rows, spec_table_html, notes_html, warranty_html

■ ルール
    ・値はバリエーション（カラー等）ごとに比較し、全部同じなら1行、違えば「色名：値」を並べる
      例：質量  ブラック：約3.8kg／アルミパネル：約4.1kg
    ・マスターの値が実物と違うときは tools/master_overrides.json で上書きする（ページを直接直さない）
    ・備考（remarks）が無い商品の保証文は、ロット番号シールの一文を外した汎用文
=============================================================================
"""
import json, os, re, html
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
PRODUCTS_JSON = os.path.join(SITE, "data", "catalog", "products.json")

SPEC_FIELDS = [("容量", "capacitySpec"), ("カラー・仕様", None), ("質量", "weight"), ("材質", "material"),
               ("サイズ", "dimensions"), ("仕様", "spec"), ("セット内容・付属品", "included")]
GENERIC_WARRANTY = "保証期間：1年。商品の不具合に関するお問い合わせの際は、製品ロット番号と納品書をご用意のうえ、ご連絡ください。"

_cache = {}
def load_products():
    if "p" not in _cache:
        _cache["p"] = json.load(open(PRODUCTS_JSON, encoding="utf-8"))
    return _cache["p"]

def esc(t):
    return html.escape((t or "").strip(), quote=False)

def br(t):
    return esc(t).replace("\n", "<br>")

def variants(code):
    return (load_products().get(code) or {}).get("variants") or []

def _label(v):
    return (v.get("color") or "").strip() or v.get("name", "")

def merged_value(vs, key):
    """バリエーションで値が同じなら1つ、違えば『色名：値』を改行で並べる（空は '—'）"""
    vals = [(_label(v), (v.get(key) or "").strip()) for v in vs]
    if not vals:
        return ""
    distinct = list(OrderedDict.fromkeys(val for _, val in vals))
    if len(distinct) == 1:
        return distinct[0]
    groups = OrderedDict()
    for lb, val in vals:
        groups.setdefault(val, []).append(lb)
    return "\n".join("／".join(lbs) + "：" + (val if val else "—") for val, lbs in groups.items())

def spec_rows(code):
    """[(見出し, 値テキスト), …]（値は改行入りのプレーンテキスト。空の項目は含めない）"""
    vs = variants(code)
    if not vs:
        return []
    rows = []
    for label, key in SPEC_FIELDS:
        if key is None:
            raw = [(v.get("color") or "").strip() for v in vs if (v.get("color") or "").strip()]
            lr = any(re.search(r"[左右]用", c) for c in raw)
            colors = list(OrderedDict.fromkeys(re.sub(r"\s*[左右]用", "", c) for c in raw))
            if colors and len(colors) <= 4:
                rows.append((label, "／".join(colors) + ("（左用・右用）" if lr else "")))
            continue
        val = merged_value(vs, key) if key != "capacitySpec" else (merged_value(vs, "capacitySpec") or merged_value(vs, "capacity"))
        if val.strip() and val.strip() != "—":
            rows.append((label, val))
    return rows

def spec_table_html(code, style):
    """style: 'max'（MAXテンプレート <table class="pd-spec">）／'legacy'（従来テンプレート）"""
    out = []
    for label, val in spec_rows(code):
        if style == "max":
            out.append("<tr><th>%s</th><td>%s</td></tr>" % (label, br(val)))
        else:
            out.append('<tr class="border-b border-black/10"><th class="text-left align-top py-3 pr-6 font-medium text-neutral-500 w-[140px] whitespace-nowrap">%s</th>'
                       '<td class="py-3 text-[14px] leading-relaxed">%s</td></tr>' % (label, br(val)))
    return "".join(out)

def note_text(code):
    vs = variants(code)
    return (vs[0].get("note") or "").strip() if vs else ""

def notes_html(code, style):
    t = note_text(code)
    if not t:
        return ""
    if style == "max":
        return '<div class="pd-notes"><h3 class="pd-notes-h">Notes</h3><p>%s</p></div>' % br(t)
    return '<h2 class="sec-ttl sec-ttl-quiet mt-10">Notes</h2><p class="text-[12.5px] leading-[1.95] text-neutral-500 mt-5">%s</p>' % br(t)

def warranty_html(code):
    vs = variants(code)
    r = (vs[0].get("remarks") or "").strip() if vs else ""
    if not r:
        return GENERIC_WARRANTY
    lines = [esc(x) for x in r.split("\n") if x.strip()]
    if lines[0].startswith("保証期間") and len(lines) > 1 and not lines[0].endswith("。"):
        lines = [lines[0] + "。" + lines[1]] + lines[2:]
    return "<br>".join(lines)
