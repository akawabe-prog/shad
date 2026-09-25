#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 商品マスター監査：サイトの表示が商品マスター（products.json）と食い違っていないか
=============================================================================
マスター更新のたび・公開前に実行します。結果は docs/audit/master_audit_<日付>.md にも保存します（docs/ は非公開）。

    python3 tools/audit_master.py              # 全商品
    python3 tools/audit_master.py TR48 SH44    # 型番を絞る
    python3 tools/audit_master.py --no-file    # ファイルに書かない

■ 見る場所と重さ
  [ERROR] マスター由来ブロックがマスターと違う（apply_master_to_pages.py で直る）
          スペック表（容量/カラー/質量/材質/サイズ/仕様/セット内容）・Notes・保証文
  [WARN ] 手書き部分がマスターと矛盾している可能性（人が判断して直す）
          ・一覧カード：容量・色数・カテゴリ名・ヘルメット/防水/耐荷重アイコン
          ・詳細ページのアイコン列（ヘルメット個数・耐荷重・防水）
          ・本文中の数値（容量L・質量kg・耐荷重kg・ヘルメット個数）でマスターに無いもの
          ・要注意ワード（完全防水／最軽量／〜個収納 など）
          ・販売ステータス（マスターの廃番・販売終了とページの案内）
  [INFO ] マスター側のデータ品質（バリエーション間で仕様・注意・備考が食い違う、空欄 等）
=============================================================================
"""
import os, re, sys, json, html, glob, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from master_spec import ROOT, SITE, load_products, spec_rows, note_text, warranty_html, variants

P = load_products()
S = open(os.path.join(SITE, "products.html"), encoding="utf-8").read()
CARDS = {x["code"]: x for x in json.loads(re.search(r"var PRODUCTS=(\[.*?\]);", S, re.S).group(1))}
MASTER_CSV = os.path.join(ROOT, "data-source", "ItemList_SHAD.csv")

def text(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", h, flags=re.S)
    h = re.sub(r"<br\s*/?>", "\n", h)
    return html.unescape(re.sub(r"<[^>]+>", " ", h))

def norm(t):
    t = (t or "").replace("　", " ")
    t = re.sub(r"[\s]+", "", t)
    return t.translate(str.maketrans("（）：／，．～", "():/,.~")).replace("〜", "~").rstrip("。")

def page_spec(page):
    """ページのスペック表 → {見出し: 値}"""
    rows = {}
    for th, td in re.findall(r"<tr[^>]*>\s*<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>\s*</tr>", page, re.S):
        rows[norm(text(th))] = norm(text(td))
    return rows

def status_of(code):
    """マスターの販売ステータス（バリエーション別）"""
    out = []
    try:
        import csv
        for r in csv.DictReader(open(MASTER_CSV, encoding="cp932", newline="")):
            n = r.get("商品名", "")
            if re.match(r"^\s*" + re.escape(code) + r"(?![0-9A-Z])", n, re.I) and not r["品番"].startswith(("YY", "ZZ")):
                out.append((r["品番"], r.get("商品ステータスコード", ""), r.get("CJ廃番", ""), r.get("Web非表示", ""), r.get("詳細非表示", "")))
    except FileNotFoundError:
        pass
    return out

# ヘルメット個数：マスターの仕様・説明から推定
def expected_helmets(vs):
    t = " ".join((v.get("spec") or "") + "\n" + (v.get("descSub") or "") + "\n" + (v.get("catch") or "") for v in vs)
    if "収納することはできません" in t or "収納できません" in t:
        return 0, "収納不可"
    m = re.search(r"(フルフェイス|ヘルメット)[^。\n]{0,20}?(\d)個", t)
    if "フリップアップとジェット" in t or "フリップアップ＋ジェット" in t:
        return 2, "フルフェイス・オフロード1個／フリップアップ＋ジェット2個"
    if m:
        return int(m.group(2)), m.group(0)
    return None, ""

def expected_maxload(vs):
    m = re.search(r"最大耐荷重[：:]\s*(\d+(?:\.\d+)?)\s*kg", " ".join(v.get("spec") or "" for v in vs))
    return m.group(1) if m else None

WATCH = ["完全防水", "最軽量", "世界最軽量", "最強", "唯一", "取付穴をあらかじめ"]

def audit(code):
    path = os.path.join(SITE, "product", code.lower() + ".html")
    E, W, I = [], [], []
    if not os.path.exists(path):
        return [("ERROR", "page", "商品ページが無い")]
    page = open(path, encoding="utf-8").read()
    body = text(page)
    vs = variants(code)
    if not vs:
        return [("ERROR", "master", "マスター（products.json）に無い")]
    v0 = vs[0]

    # ---- ERROR: マスター由来ブロック ----
    ps = page_spec(page)
    for label, val in spec_rows(code):
        pv = ps.get(norm(label))
        if pv is None:
            E.append(("spec", f"スペック表に「{label}」が無い（マスター：{val[:40]}）"))
        elif pv != norm(val):
            E.append(("spec", f"スペック「{label}」 ページ『{pv[:50]}』 ≠ マスター『{norm(val)[:50]}』"))
    exp_labels = {norm(l) for l, _ in spec_rows(code)}
    for l in ps:
        if l not in exp_labels:
            W.append(("spec", f"スペック表にマスターに無い行「{l}」：『{ps[l][:50]}』"))
    nt = note_text(code)
    m = re.search(r">Notes<.*?<p[^>]*>(.*?)</p>", page, re.S)
    if nt and not m:
        E.append(("notes", "Notes ブロックが無い"))
    elif nt and norm(text(m.group(1))) != norm(nt):
        E.append(("notes", "Notes がマスターの注意事項と違う"))
    elif not nt:
        I.append(("notes", "マスターに注意事項が無い（Notes 非表示）"))
    wm = re.findall(r'warranty-body">(.*?)</div>|1年保証</p>\s*<p[^>]*>(.*?)</p>', page, re.S)
    for a, b in wm:
        if norm(text(a or b)) != norm(text(warranty_html(code))):
            E.append(("warranty", "保証文がマスターの備考と違う")); break

    # ---- WARN: 一覧カード ----
    card = CARDS.get(code)
    if card:
        caps = {norm(v.get("capacitySpec") or v.get("capacity") or "") for v in vs} - {""}
        cap = norm(card.get("cap") or "")
        if cap and caps and not any(cap in c or c in cap for c in caps):
            W.append(("card", f"一覧の容量『{card.get('cap')}』がマスター {sorted(caps)} と合わない"))
        colors = {re.sub(r"\s*[左右]用", "", (v.get("color") or "")) for v in vs} - {""}
        if card.get("colors") not in (0, len(colors)) and len(vs) <= 4:
            W.append(("card", f"一覧の色数 {card.get('colors')} ≠ マスターの色 {sorted(colors)}"))
        TYPES = ["トップケース", "サイドケース", "サイドバッグ", "タンクバッグ", "シートバッグ", "ダッフルバッグ", "クラッシュバーバッグ",
                 "ツーリングバッグ", "スクーターバッグ", "ハンドルバーロック", "コンフォートシート"]
        jp = card.get("jp") or ""
        mt = [t for t in TYPES if t in v0.get("name", "")] or [t for t in TYPES if t in (v0.get("category") or "")]
        jt = [t for t in TYPES if t in jp]
        if mt and jt and mt[0] != jt[0]:
            W.append(("card", f"一覧の種別『{jp}』がマスターの商品名『{v0.get('name','')[:30]}』と違う"))
        feats = {f["label"]: f.get("val") for f in card.get("features", [])}
        exp_n, why = expected_helmets(vs)
        if "ヘルメット" in feats and exp_n == 0:
            W.append(("card", f"一覧にヘルメットアイコンがあるがマスターは『{why}』"))
        if "ヘルメット" in feats and exp_n and feats["ヘルメット"] and feats["ヘルメット"] != f"×{exp_n}":
            W.append(("card", f"一覧のヘルメット {feats['ヘルメット']} ≠ マスター推定 ×{exp_n}（{why[:30]}）"))
        ml = expected_maxload(vs)
        if "耐荷重" in feats and ml and feats["耐荷重"] and feats["耐荷重"].replace("kg", "") != ml:
            W.append(("card", f"一覧の耐荷重 {feats['耐荷重']} ≠ マスター {ml}kg"))
        for f in card.get("features", []):
            if f["label"] == "防水" and f.get("val") and f["val"] not in " ".join(v.get("spec") or "" for v in vs):
                W.append(("card", f"一覧の防水 {f['val']} がマスターの仕様に無い"))

    # ---- WARN: 詳細ページのアイコン列 ----
    cells = re.findall(r'<div class="feat-cell">.*?<b>([^<]*)</b>(?:<span>([^<]*)</span>)?', page, re.S)
    icons = {b: v for b, v in cells}
    exp_n, why = expected_helmets(vs)
    if "ヘルメット" in icons and exp_n == 0:
        W.append(("icon", f"詳細にヘルメットアイコンがあるがマスターは『{why}』"))
    if "ヘルメット" in icons and exp_n and icons["ヘルメット"] and icons["ヘルメット"] != f"×{exp_n}":
        W.append(("icon", f"詳細のヘルメット {icons['ヘルメット']} ≠ マスター推定 ×{exp_n}（{why[:30]}）"))
    if card and ("ヘルメット" in icons) != ("ヘルメット" in {f["label"] for f in card.get("features", [])}):
        W.append(("icon", "ヘルメットアイコンの有無が一覧と詳細で違う"))
    ml = expected_maxload(vs)
    if "耐荷重" in icons and ml and icons["耐荷重"] and icons["耐荷重"].replace("kg", "") != ml:
        W.append(("icon", f"詳細の耐荷重 {icons['耐荷重']} ≠ マスター {ml}kg"))

    # ---- WARN: 本文の数値（マスター由来ブロックと FAQ・関連商品欄は除く）----
    # 関連商品（Same Series / related）・フルパニア構成（setup：他商品の容量が並ぶ）・適合・FAQ・表・Notes・保証文は対象外
    prose = re.sub(r'<section id="fitment".*?</section>|<section id="related".*?</section>|<section id="setup".*?</section>|'
                   r'<section class="bg-mist py-12 mt-8"><div class="max-w-site mx-auto px-7"><h2 class="sec-ttl sec-ttl-quiet">Same Series</h2>.*?</section>|'
                   r'<section[^>]*>(?:(?!</section>).)*?(?:Waterproof Series|Same Series)</h2>.*?</section>|'
                   r'<!-- FAQ:START.*?<!-- FAQ:END -->|<table.*?</table>|<div class="pd-notes">.*?</div></div>|'
                   r'<div class="warranty-body">.*?</div>|<details class="pd-acc">.*?</details>|<script.*?</script>', "", page, flags=re.S)
    prose_t = text(prose)
    mnums = set(re.findall(r"\d+(?:\.\d+)?", " ".join((v.get("weight") or "") + " " + (v.get("spec") or "") + " " + (v.get("capacitySpec") or "") + " " + (v.get("capacity") or "") + " " + (v.get("name") or "") + " " + (v.get("dimensions") or "") for v in vs)))
    for n_, unit in re.findall(r"約?(\d+(?:\.\d+)?)\s*(kg|L)\b", prose_t):
        if n_ not in mnums and not re.search(r"(耐荷重|最大)[^。]{0,10}" + re.escape(n_), prose_t):
            snippet = re.search(r".{0,30}" + re.escape(n_) + unit + r".{0,20}", prose_t, re.S)
            W.append(("copy", f"本文の『{n_}{unit}』がマスターに無い：…{re.sub(r'\\s+',' ',snippet.group(0)) if snippet else ''}…"))
    for m in re.finditer(r"(フルフェイス|ヘルメット)[^。\n]{0,12}?(\d)個", prose_t):
        if exp_n is not None and int(m.group(2)) > (exp_n or 0):
            W.append(("copy", f"本文『{m.group(0)}』がマスター推定（{why or '個数不明'}）と合わない"))
    for w in WATCH:
        if w in prose_t and not (w == "完全防水" and "完全防水ではありません" in prose_t and prose_t.count("完全防水") == prose_t.count("完全防水ではありません")):
            snippet = re.search(r".{0,25}" + re.escape(w) + r".{0,25}", prose_t, re.S)
            W.append(("copy", f"要注意ワード『{w}』：…{re.sub(r'\\s+',' ',snippet.group(0))}…"))

    # ---- WARN: 販売ステータス ----
    st = status_of(code)
    dead = [s for s in st if s[1].startswith("DC") or s[2] == "1"]
    live = [s for s in st if not (s[1].startswith("DC") or s[2] == "1")]
    if st and not live:
        W.append(("status", f"マスターでは全品番が廃番/取扱終了（{[s[1] for s in dead]}）だがページは公開中"))
    if "販売は終了" in body or "取り扱いを終了" in body or "生産終了" in body:
        if live:
            W.append(("status", "ページに『販売終了/生産終了』の案内があるがマスターでは販売中の品番がある"))
    if card and card.get("status") and live:
        W.append(("status", f"一覧カードの status『{card['status']}』だがマスターでは販売中"))

    # ---- INFO: マスター側の品質 ----
    for key, lb in (("spec", "仕様"), ("note", "注意"), ("remarks", "備考"), ("material", "材質"), ("dimensions", "サイズ")):
        vals = {(v.get(key) or "").strip() for v in vs}
        if len(vals) > 1 and len(vs) > 1:
            I.append(("master", f"バリエーション間で「{lb}」が異なる（{len(vals)}通り）"))
    for key, lb in (("weight", "質量"), ("dimensions", "サイズ"), ("material", "材質"), ("included", "セット内容")):
        if not any((v.get(key) or "").strip() for v in vs):
            I.append(("master", f"「{lb}」がマスターで空欄"))
    if "青色シール" in (v0.get("remarks") or "") and code.startswith("TR") and "アルミ" in (v0.get("material") or ""):
        I.append(("master", "アルミケースなのに備考が青色シール（黄色シールなら master_overrides に登録）"))

    return [("ERROR", k, m) for k, m in E] + [("WARN", k, m) for k, m in W] + [("INFO", k, m) for k, m in I]

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    codes = [c.upper() for c in args] or sorted(CARDS.keys())
    lines = ["# 商品マスター監査 %s" % datetime.date.today().isoformat(), "",
             "マスター: data-source/ItemList_SHAD.csv（上書きルール tools/master_overrides.json 適用後の products.json と比較）", ""]
    tot = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for code in codes:
        res = audit(code)
        if not res:
            continue
        lines.append("## %s" % code)
        for lv, k, m in res:
            tot[lv] += 1
            lines.append("- [%s] %s: %s" % (lv, k, m))
        lines.append("")
    summary = "%d 商品 / ERROR %d・WARN %d・INFO %d" % (len(codes), tot["ERROR"], tot["WARN"], tot["INFO"])
    lines.append(summary)
    print("\n".join(lines))
    if "--no-file" not in sys.argv:
        out_dir = os.path.join(ROOT, "docs", "audit"); os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, "master_audit_%s.md" % datetime.date.today().strftime("%Y%m%d"))
        open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print("\n→", os.path.relpath(out, ROOT))
