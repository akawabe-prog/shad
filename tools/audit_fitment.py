#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 適合情報（フィッティング）監査：サイトの適合データと商品マスターの食い違い
=============================================================================
適合検索のデータ（site/data/fitment/*.json）は tools/fitment/build.py がマスターから作りますが、
「作り直し忘れ」と「マスター自体の登録ミス」は生成しても直りません。それを一覧します。

    python3 tools/audit_fitment.py            # → docs/audit/fitment_audit_<日付>.md
    python3 tools/audit_fitment.py --no-file

■ 見る場所と重さ
  [ERROR] サイトの適合データが今のマスターと合っていない（tools/fitment/build.py で直る）
          ・適合データが参照するキット／商品がマスターで廃番・販売終了・非表示になっている
          ・マスターで有効なキットが適合データに無い、キット名が古い
          ・商品の品番（カラー）が products.json と食い違う
  [WARN ] マスターの登録どうしが矛盾している（EC側のマスターを直す）
          ・キットの仕様欄「対応モデル」と対応コード列（メーカータイプ）が一致しない
          ・ベースプレートの対応トップケースと、トップケース側の付属/注意書きが一致しない
          ・商品ページの注意書き（3P/4Pが必要）と、キット側の対応宣言が合わない
  [INFO ] 検索の見え方に影響するマスターの表記ゆれ
          ・同じ車種が年式表記の違いで別々に出る（例：R1300GS(23-25) と (23-26)）
          ・メーカー名の表記ゆれ（CF MOTO／CFMOTO 等）
=============================================================================
"""
import os, re, sys, csv, json, html, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
CSV_PATH = os.path.join(ROOT, "data-source", "ItemList_SHAD.csv")
RD = json.load(open(os.path.join(SITE, "data", "fitment", "reverse_data.json"), encoding="utf-8"))
PI = json.load(open(os.path.join(SITE, "data", "fitment", "product_index.json"), encoding="utf-8"))
P = json.load(open(os.path.join(SITE, "data", "catalog", "products.json"), encoding="utf-8"))
ROWS = list(csv.DictReader(open(CSV_PATH, encoding="cp932", newline="")))
BY_CJ = {r["品番"]: r for r in ROWS}
BY_MK = {r["メーカー品番"]: r for r in ROWS if r.get("メーカー品番")}
CODE_RX = r"(SH\d+X?|TR\d+(?:CL)?|E\d+C[LM]?|E48SR|E48|SL58|SR38|IB20)"

def visible(r):
    return (r["CJ廃番"] != "1" and not r["品番"].startswith(("YY", "ZZ")) and not r["商品ステータスコード"].startswith("DC")
            and r.get("セット", "0") != "1" and r.get("Web非表示", "0") != "1")

def cj_of(url):
    m = re.search(r"/i/([A-Za-z0-9]+)", url or "")
    return m.group(1) if m else ""

E, W, I = [], [], []

# ---------------- ERROR: 適合データ vs マスター ----------------
ref = collections.OrderedDict()   # 品番 → 適合データ内の名前
for b in RD["bikes"]:
    for k in b.get("top", []) + b.get("side", []) + b.get("sidebag", []) + b.get("sr", []):
        c = cj_of(k.get("url"));
        if c: ref.setdefault(c, k.get("name", ""))
for k in RD.get("clicksystem_kits", []):
    c = cj_of(k.get("url"));
    if c: ref.setdefault(c, k.get("name", ""))
for cj, name in ref.items():
    r = BY_CJ.get(cj) or BY_MK.get(cj)
    if not r:
        E.append(("kit", f"適合データのキット {cj}『{name[:36]}』がマスターに無い")); continue
    if not visible(r):
        E.append(("kit", f"適合データのキット {cj}『{name[:36]}』はマスターで {r['商品ステータスコード']}／CJ廃番={r['CJ廃番']}（作り直しが必要）"))
    elif name and r["商品名"] and re.sub(r"\s+", "", name) != re.sub(r"\s+", "", r["商品名"]):
        E.append(("kit", f"キット名が古い {cj}：適合『{name[:30]}』≠ マスター『{r['商品名'][:30]}』"))
master_kits = [r for r in ROWS if visible(r) and "フィッティングキット" in r["商品名"] and r["代表適合車種"].strip()]
lock_kits = [r for r in master_kits if "ロック" in r["商品名"]]
if lock_kits:
    I.append(("kit", f"SHADロックフィッティングキット {len(lock_kits)} 件は適合検索の対象外（ハンドルバーロック用。載せるなら tools/fitment に区分を追加）"))
for r in master_kits:
    if r["品番"] not in ref and r not in lock_kits:
        W.append(("kit", f"マスターの有効キット {r['品番']}『{r['商品名'][:36]}』が適合データに出ていない（代表適合車種：{r['代表適合車種'][:30]}）"))

# 商品（トップ/サイド/バッグ/タンク）の品番
prod_refs = []
for pl in RD["plates"].values():
    prod_refs += pl.get("topcases", [])
for grp in ("sidecases", "sidebags"):
    for lst in RD.get(grp, {}).values():
        prod_refs += lst
prod_refs += RD.get("tankbags", [])
for it in prod_refs:
    cj = cj_of(it.get("ecUrl") or it.get("url")); code = it.get("code")
    r = BY_CJ.get(cj)
    if not r:
        E.append(("product", f"適合データの商品 {cj}『{it.get('name','')[:30]}』がマスターに無い")); continue
    if not visible(r):
        E.append(("product", f"適合データの商品 {cj}『{it.get('name','')[:30]}』はマスターで {r['商品ステータスコード']}／CJ廃番={r['CJ廃番']}"))
    if code and code in P and cj not in {v["cjCode"] for v in P[code]["variants"]}:
        E.append(("product", f"{code} の品番 {cj} が products.json のバリエーションに無い"))
for code, e in P.items():
    cat = e["variants"][0].get("category", "")
    in_fit = code in PI["topcasePlate"] or code in PI["sidecaseCodes"] or code in PI["sidebagCodes"] or code in PI["tankbagCodes"]
    if not in_fit and any(k in cat for k in ("トップケース", "サイドケース", "サイドバッグ", "タンクバッグ")):
        W.append(("product", f"{code}（{cat}）が適合データのどの区分にも入っていない"))

# ---------------- WARN: マスター内の矛盾 ----------------
KITSPEC = {}
plate_members = {}
for r in ROWS:
    if visible(r) and "ベースプレート" in r["商品名"] and r["メーカー品番"] and r["メーカータイプ"]:
        plate_members[r["メーカー品番"]] = set(x for x in r["メーカータイプ"].split("_") if x)
for r in [x for x in ROWS if visible(x) and "フィッティングキット" in x["商品名"]]:
    m = re.search(r"対応モデル[：:]\s*([^\n]+)", r["仕様"])
    if not m:
        continue
    ALIAS = {"E03CLP": "E03CL", "E09CLP": "E09CL"}   # コード列の PRO 表記ゆれ
    spec_codes = set(re.findall(CODE_RX, m.group(1)))
    mt = set(ALIAS.get(x, x) for x in r["メーカータイプ"].split("_") if x)
    if not spec_codes or not mt:
        continue
    if any(x in plate_members for x in mt):          # トップマスター：プレート → ケース に展開
        expect = set().union(*(plate_members.get(x, {x}) for x in mt))
    else:
        expect = mt
    if spec_codes != expect:
        only_spec, only_code = sorted(spec_codes - expect), sorted(expect - spec_codes)
        KITSPEC.setdefault((tuple(only_spec), tuple(only_code)), []).append(r["品番"])

for (only_spec, only_code), cjs in sorted(KITSPEC.items(), key=lambda x: -len(x[1])):
    W.append(("kit-spec", f"仕様欄「対応モデル」とコード列の不一致 {len(cjs)} 件：仕様欄だけ {list(only_spec)} / コード列だけ {list(only_code)}（{', '.join(cjs[:6])}{' …' if len(cjs) > 6 else ''}）"))

for code, plate in PI["topcasePlate"].items():
    v = P.get(code, {}).get("variants", [{}])[0]
    t = " ".join((v.get(k) or "") for k in ("included", "note", "spec"))
    mention = set(re.findall(r"D1B[A-Z0-9]+", t))
    if mention and plate not in mention:
        W.append(("plate", f"{code}：適合データのベースプレート {plate} が商品側の記載 {sorted(mention)} に無い"))
    for pl, members in plate_members.items():
        if code in members and pl not in (mention or {pl}) and mention:
            W.append(("plate", f"{code}：ベースプレート {pl} は対応を宣言しているが商品側の記載に無い"))

side_kits = collections.defaultdict(collections.Counter)
for r in ROWS:
    if visible(r) and "フィッティングキット" in r["商品名"]:
        for c in r["メーカータイプ"].split("_"):
            if c: side_kits[c][r["メインシリーズ"] or r["商品名"].split()[0]] += 1
for code in PI["sidecaseCodes"] + PI["sidebagCodes"]:
    v = P.get(code, {}).get("variants", [{}])[0]
    note = (v.get("note") or "") + (v.get("spec") or "")
    kinds = side_kits.get(code, {})
    has3 = any("3P" in k for k in kinds); has4 = any("4P" in k for k in kinds)
    says3 = "3Pシステム" in note; says4 = "4Pシステム" in note
    if says4 and not says3 and has3:
        W.append(("kit-side", f"{code}：注意書きは4P必要だが、3Pキット {sum(n for k,n in kinds.items() if '3P' in k)} 件が {code} 対応を宣言（マスター要確認）"))
    if says3 and not has3:
        W.append(("kit-side", f"{code}：注意書きに3Pとあるが、3Pキットで {code} 対応を宣言しているものが無い"))
    if not kinds:
        I.append(("kit-side", f"{code}：対応を宣言するキットがマスターに無い（車種専用キット不要の商品なら問題なし）"))

# ---------------- INFO: 表記ゆれ ----------------
names = collections.defaultdict(list)
for b in RD["bikes"]:
    key = (b["maker"], re.sub(r"[\(（][^)）]*[\)）]", "", b["model"]).replace(" ", "").lower())
    names[key].append(b["model"])
for (mk, _), v in sorted(names.items()):
    if len(v) > 1:
        I.append(("bike", f"{mk}：{' / '.join(v)}（年式表記の違いで別車種として出る）"))
makers = collections.Counter(b["maker"] for b in RD["bikes"])
norm_mk = collections.defaultdict(set)
for mk in makers:
    norm_mk[re.sub(r"[\s\-]", "", mk).lower()].add(mk)
for k, v in norm_mk.items():
    if len(v) > 1:
        I.append(("maker", f"メーカー名の表記ゆれ：{sorted(v)}"))

# ---------------- 出力 ----------------
lines = ["# 適合情報監査 %s" % datetime.date.today().isoformat(), "",
         "適合データ: site/data/fitment/reverse_data.json（%d 車種）／マスター: data-source/ItemList_SHAD.csv" % len(RD["bikes"]), ""]
for title, items in (("ERROR（適合データの作り直し／サイト側）", E), ("WARN（マスターの登録どうしの矛盾）", W), ("INFO（表記ゆれ）", I)):
    lines.append("## %s — %d 件" % (title, len(items)))
    for k, m in items:
        lines.append("- [%s] %s" % (k, m))
    lines.append("")
lines.append("ERROR %d・WARN %d・INFO %d" % (len(E), len(W), len(I)))
print("\n".join(lines))
if "--no-file" not in sys.argv:
    out_dir = os.path.join(ROOT, "docs", "audit"); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "fitment_audit_%s.md" % datetime.date.today().strftime("%Y%m%d"))
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n→", os.path.relpath(out, ROOT))
