#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 商品カタログ ビルドスクリプト
=============================================================================
商品マスター（ItemList_SHAD.csv）から、サイトが読み込む JSON を生成します。

■ 使い方（商品データを更新するとき）
    1. 新しい ItemList_SHAD.csv を data-source/ に上書きコピー
    2. このコマンドを実行：
           python3 tools/build_catalog.py
    3. 生成された site/data/catalog/*.json をサイトと一緒にアップロード

    ※ HTML は書き換えません。JSON だけが更新されます。
    ※ 何度実行しても同じ結果になります（冪等）。

■ 入力
    data-source/ItemList_SHAD.csv   （cp932 / Shift_JIS）

■ 出力（site/data/catalog/）
    products.json     本体商品（トップケース・サイドケース・バッグ等）＋カラーバリエーション
    fitting.json      フィッティングキット（トップマスター / 3P / 4P / サイドバッグホルダー / SR）
    accessories.json  アクセサリー・補修パーツ（キーシリンダー・バックレスト・ベースプレート等）
    meta.json         生成日時・件数・除外統計

■ 除外ルール（★ ここを変えれば除外条件を変更できます）
    ・CJ廃番 = 1        → 廃盤のため除外
    ・セット   = 1        → セット商品のため除外
    ・品番が YY / ZZ 始まり → 社内用品番のため除外
=============================================================================
"""

import csv
import json
import os
import re
import sys
from collections import OrderedDict, Counter
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------- パス設定
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data-source", "ItemList_SHAD.csv")
OUT_DIR = os.path.join(ROOT, "site", "data", "catalog")
CSV_ENCODING = "cp932"  # EC側エクスポートは Shift_JIS 系

# ---------------------------------------------------------------- 除外ルール
EXCLUDE_DISCONTINUED = True   # CJ廃番 = 1 を除外
EXCLUDE_SETS = True           # セット = 1 を除外
EXCLUDE_INTERNAL_PREFIX = ("YY", "ZZ")  # 社内用品番の接頭辞

# ---------------------------------------------------------------- 分類ルール
# フィッティングキットと判定する「メインシリーズ」
FITTING_SERIES = (
    "トップマスターフィッティングキット",
    "3Pシステムフィッティングキット",
    "4Pシステムフィッティングキット",
    "サイドバッグホルダーキット",
    "SRバッグフィッティングキット",
)
# 本体商品（製品ページに載るケース・バッグ本体）と判定する「メインシリーズ」
BODY_SERIES = (
    "TERRA", "トップケース", "サイドケース", "クリックシステム",
    "ソフトバッグ", "システムバッグ", "カフェレーサーバッグ", "X-FRAME",
    "SHADロック", "コンフォートシート",
)
# アクセサリー・補修パーツと判定する「メインシリーズ」
# （本体と同じ型番を名前に含むが、本体ではないもの）
ACCESSORY_SERIES = (
    "アクセサリー", "バックレスト", "シーシーバー", "ベースプレート",
)

# 商品名にこの語が含まれるものは「本体」ではない（型番で始まっていても部品／キット）
NON_BODY_KEYWORDS = (
    "フィッティングキット", "バックレスト", "カラーパネル", "ロックカバー",
    "インナーバッグ", "アッパーラック", "キーシリンダー", "ベースプレート",
    "テールランプ", "ストッパー", "付属パーツ", "ドライバッグ", "ボトルハーネス",
    "シーシーバー", "専用パネル", "補修", "スペアキー",
    "交換用ラック", "ウォールラック", "エンドキャップ", "アタッチメント",
)

# サイトに製品ページがあるモデルコード（site/product-*.html と対応）
SITE_CODES = [
    "TR55", "TR50", "TR48", "TR47", "TR46", "TR41", "TR40", "TR37", "TR36", "TR30", "TR27", "TR10",
    "SH58X", "SH51", "SH48", "SH47", "SH44", "SH38X", "SH34", "SH33", "SH23",
    "SW80", "SL18", "E48", "LOCK", "SEAT",
    # 2026-07 追加（マスターにあるがページが無かった商品）
    "SH59X", "SH45", "SH40CG", "SH40", "SH39", "SH36", "SH35", "SH29", "SH26",
    "TR15CL", "TR08", "SL58", "SR38", "SC25", "IB20",
    "E09CL", "E09CM", "E09C", "E03CL", "E03C", "E02C", "E04",
    "XFRAME",
]
# 長いコードから先に判定（SH58X が SH5 に誤マッチしないように）
SITE_CODES_SORTED = sorted(SITE_CODES, key=len, reverse=True)

IMG_BASE = "https://img.customjapan.net/items/{}_1.jpg"

# 商品名が製品コードで始まらないモデルの対応表（先に判定する）
NAME_ALIASES = (
    (re.compile(r"^\s*SH40\s*CARGO", re.I), "SH40CG"),
    (re.compile(r"^\s*X-?FRAME\s*スマートフォンホルダー"), "XFRAME"),
    (re.compile(r"^\s*スマートフォンホルダー"), "XFRAME"),
)

# 「メインカラー」だけでは区別できないカラー違い（例：TR55のブラックとピュアブラックは
# どちらもメインカラー＝ブラック）があるため、商品名の色名を優先して表示ラベルにする。
COLOR_TOKENS = (
    "ピュアブラック", "マットブラック", "ブラックメタル", "ダークグレー", "アルミパネル",
    "チタニウム", "カーボン", "ガンメタ", "チタン",
    "シルバー", "ブラック", "ホワイト", "グレー", "レッド", "ブルー", "イエロー", "ベージュ",
)


def cell(row, key):
    return (row.get(key) or "").strip()


def color_label(row):
    """カラー表示名。商品名に含まれる色名を出現順に並べる（例：ホワイト/カーボン）。
    「ピュアブラック」のように長い語が優先され、内包される「ブラック」は無視する。"""
    name = cell(row, "商品名")
    spans = []
    for token in sorted(COLOR_TOKENS, key=len, reverse=True):
        start = 0
        while True:
            i = name.find(token, start)
            if i < 0:
                break
            end = i + len(token)
            if not any(i < e and s < end for s, e in spans):
                spans.append((i, end))
            start = end
    if spans:
        spans.sort()
        return "/".join(name[s:e] for s, e in spans)
    return cell(row, "メインカラー")


# 同じモデル内で表示名が重複するときに優先して使う区別語（左右・マウント種別）
VARIANT_QUALIFIERS = ("右用", "左用", "左右", "3P", "4P",
                      "ミラークランプ式", "ハンドルバークランプ式")


def _differing_part(name, others):
    """同一モデルの他の商品名と共通する前後を落として、違う部分だけを返す。"""
    head = 0
    while all(len(o) > head and len(name) > head and o[head] == name[head] for o in others):
        head += 1
    tail = 0
    while all(
        len(o) > head + tail and len(name) > head + tail and o[-1 - tail] == name[-1 - tail]
        for o in others
    ):
        tail += 1
    part = name[head:len(name) - tail] if tail else name[head:]
    # 「38cm / 44cm」のように単位が共通末尾に含まれる場合は単位まで戻す
    if tail and part and part[-1].isalnum():
        unit = name[len(name) - tail:].split(" ")[0].split("　")[0]
        if len(unit) <= 4:
            part += unit
    part = part.strip(" 　/・")
    # 括弧が開いたまま切れないように整える
    if part.count("(") > part.count(")"):
        part = part[:part.rfind("(")].strip()
    return part


def dedupe_variant_labels(variants):
    """同一モデル内でカラー表示名が重複する場合、商品名の違う部分で区別する。"""
    groups = {}
    for v in variants:
        groups.setdefault(v["color"], []).append(v)
    for label, group in groups.items():
        if len(group) < 2:
            continue
        names = [v["name"] for v in group]
        for v in group:
            q = next((t for t in VARIANT_QUALIFIERS if t in v["name"]), "")
            if not q:
                q = _differing_part(v["name"], [n for n in names if n != v["name"]])
                if len(q) > 24:
                    q = q[:24]
                    if q.count("(") > q.count(")"):
                        q = q[:q.rfind("(")].strip()
            if not q:
                continue
            v["color"] = (label + " " + q) if (label and label not in q) else q
        # まだ同名なら品番で区別する（マスターに同名品番が複数ある場合）
        seen = {}
        for v in group:
            seen.setdefault(v["color"], []).append(v)
        for lab, same in seen.items():
            if len(same) > 1:
                for v in same:
                    v["color"] = lab + "（" + v["cjCode"] + "）"


# アクセサリー名の末尾にある「対応ボックスの型番リスト」を落とすための判定
_ACC_CODE = r"(?:[A-Z]{1,3}\d{1,3}[A-Z]{0,2}|TERRA)"
ACC_TAIL_CODES = re.compile(
    r"(?:\s(?:対応|専用|用))?\s+" + _ACC_CODE + r"(?:\s*[/／]\s*" + _ACC_CODE
    + r"|\s+" + _ACC_CODE + r")*\s*$"
)


def strip_tail_codes(name):
    """「バックレスト SH58X/SH59X」→「バックレスト」。
    型番が先頭にある名前（SH33専用カラーパネル 等）はそのまま返す。"""
    short = ACC_TAIL_CODES.sub("", name).strip(" 　/・")
    # 型番だけの名前になってしまう場合や、極端に短くなる場合は元の名前を使う
    if len(short) < 3:
        return name
    return short


def to_int(value):
    v = re.sub(r"[^\d]", "", value or "")
    return int(v) if v else None


def is_excluded(row):
    """除外ルールに該当するか。（理由の文字列 or None）"""
    if EXCLUDE_DISCONTINUED and cell(row, "CJ廃番") == "1":
        return "廃盤(CJ廃番)"
    if EXCLUDE_SETS and cell(row, "セット") == "1":
        return "セット商品"
    if cell(row, "品番").upper().startswith(EXCLUDE_INTERNAL_PREFIX):
        return "社内用品番(YY/ZZ)"
    return None


def codes_in_name(row):
    """商品名に含まれるサイト製品コードを、登場順にすべて返す（パーツの対応機種抽出用）。
    TR10CL のように型番の後に記号が続くケースも拾う。"""
    name = cell(row, "商品名").upper()
    found = []
    for code in SITE_CODES_SORTED:
        m = re.search(r"(?<![A-Z0-9])" + re.escape(code) + r"(?![0-9])", name)
        if m:
            found.append((m.start(), code))
    found.sort()
    out = []
    for _, c in found:
        # 短いコードが長いコードの一部（SH58X の中の…等）にならないよう重複排除
        if not any(c != o and c in o for o in out):
            out.append(c)
    return out


def detect_body_code(row):
    """本体商品なら、そのサイト製品コードを返す。本体でなければ None。"""
    series = cell(row, "メインシリーズ")
    raw = cell(row, "商品名")
    if not any(k in raw for k in NON_BODY_KEYWORDS):
        for pat, code in NAME_ALIASES:
            if pat.match(raw):
                return code
    if not any(s in series for s in BODY_SERIES):
        return None
    if any(s in series for s in FITTING_SERIES):
        return None
    # 型番で始まっていても、部品・キット名を含むものは本体ではない
    raw_name = cell(row, "商品名")
    if any(k in raw_name for k in NON_BODY_KEYWORDS):
        return None

    name = raw_name.upper()
    # 本体は「型番で始まる」のが基本（例: TR41 TERRA トップケース / SH48 トップケース）
    for code in SITE_CODES_SORTED:
        if re.match(r"^\s*" + re.escape(code) + r"(?![0-9])", name):
            # 「SH38X専用 インナーメッシュ」のような “型番＋専用○○” は付属品
            if re.match(r"^\s*" + re.escape(code) + r"[^\s]*\s*専用", raw_name):
                return None
            return code
    # SHADロック / コンフォートシートは型番を持たないため名称で判定
    if "SHADロック" in series or "ハンドルバーロック" in name:
        return "LOCK"
    if "コンフォートシート" in series:
        return "SEAT"
    return None


def images_of(row):
    """商品画像1〜10 のうち、値があるものを配列で返す。"""
    out = []
    for i in range(1, 11):
        v = cell(row, f"商品画像{i}")
        if v:
            out.append(v)
    return out


def base_item(row):
    """1商品（1品番）の共通フィールド。"""
    code = cell(row, "品番")
    return OrderedDict([
        ("cjCode", code),
        ("name", cell(row, "商品名")),
        ("maker", cell(row, "メーカー名")),
        ("series", cell(row, "メインシリーズ")),
        ("category", cell(row, "カテゴリ名")),
        ("mainCategory", cell(row, "メインカテゴリ名")),
        ("color", color_label(row)),
        ("colorMain", cell(row, "メインカラー")),
        ("size", cell(row, "メインサイズ")),
        ("msrpTaxIn", to_int(cell(row, "希望小売価格(税込)"))),
        ("makerCode", cell(row, "メーカー品番")),
        ("jan", cell(row, "JANコード")),
        ("capacity", cell(row, "容量")),
        ("weight", cell(row, "質量")),
        ("material", cell(row, "材質")),
        ("dimensions", cell(row, "商品サイズ")),
        ("spec", cell(row, "仕様")),
        ("included", cell(row, "セット内容・付属品")),
        ("catch", cell(row, "キャッチ")),
        ("fitModels", cell(row, "代表適合車種")),
        ("fitMakers", cell(row, "対応メーカー")),
        ("images", images_of(row)),
        ("thumb", IMG_BASE.format(code) if code else ""),
    ])


def main():
    if not os.path.exists(CSV_PATH):
        sys.exit(f"✗ 商品マスターが見つかりません: {CSV_PATH}\n"
                 f"  data-source/ItemList_SHAD.csv を配置してください。")

    with open(CSV_PATH, encoding=CSV_ENCODING, newline="") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    excluded = Counter()
    kept = []
    for r in rows:
        why = is_excluded(r)
        if why:
            excluded[why] += 1
        else:
            kept.append(r)

    # ---- 3分類に振り分け ----
    products = OrderedDict()   # site code -> {code, variants:[...]}
    fitting = []
    accessories = []
    others = []

    for r in kept:
        series = cell(r, "メインシリーズ")
        item = base_item(r)

        # ① フィッティングキット（シリーズ判定＋商品名に「フィッティングキット」を含むもの）
        if any(s in series for s in FITTING_SERIES) or "フィッティングキット" in cell(r, "商品名"):
            item["kitType"] = next((s for s in FITTING_SERIES if s in series), series or "フィッティングキット")
            fitting.append(item)
            continue

        # ② 本体商品（カラー／仕様バリエーションとしてまとめる）
        code = detect_body_code(r)
        if code:
            # 製品ページ用の説明文は本体商品にだけ持たせる（他のJSONを軽く保つ）
            item["descSub"] = cell(r, "商品説明サブ")
            item["remarks"] = cell(r, "備考")
            item["note"] = cell(r, "注意")
            entry = products.setdefault(code, OrderedDict([("code", code), ("variants", [])]))
            entry["variants"].append(item)
            continue

        # ③ アクセサリー・補修パーツ（対応する本体コードを紐づける）
        item["forCodes"] = codes_in_name(r)
        # 表示用：末尾の対応ボックス型番リストを外した短い名前
        item["displayName"] = strip_tail_codes(item["name"])
        if any(s in series for s in ACCESSORY_SERIES):
            accessories.append(item)
        else:
            others.append(item)

    # 本体商品：価格の安い順に並べ、代表情報をトップに持たせる
    for code, entry in products.items():
        entry["variants"].sort(key=lambda v: (v["msrpTaxIn"] or 10**9))
        dedupe_variant_labels(entry["variants"])
        first = entry["variants"][0]
        entry["name"] = first["name"]
        entry["series"] = first["series"]
        entry["colorCount"] = len([v for v in entry["variants"] if v["color"]])
        entry["priceMin"] = min([v["msrpTaxIn"] for v in entry["variants"] if v["msrpTaxIn"]] or [None])
        entry["priceMax"] = max([v["msrpTaxIn"] for v in entry["variants"] if v["msrpTaxIn"]] or [None])

    # 製品コード → 対応アクセサリー・補修パーツの索引
    # （商品詳細ページで「この商品に使えるアクセサリー／補修パーツ」を出すため）
    acc_index = OrderedDict()
    for item in accessories + others:
        for c in item.get("forCodes") or []:
            acc_index.setdefault(c, []).append(item["cjCode"])
    acc_index = OrderedDict(
        (c, acc_index[c]) for c in SITE_CODES if c in acc_index
    )

    os.makedirs(OUT_DIR, exist_ok=True)
    jst = timezone(timedelta(hours=9))
    meta = OrderedDict([
        ("generatedAt", datetime.now(jst).isoformat(timespec="seconds")),
        ("source", "data-source/ItemList_SHAD.csv"),
        ("totalRows", total),
        ("kept", len(kept)),
        ("excluded", OrderedDict(sorted(excluded.items()))),
        ("counts", OrderedDict([
            ("products", len(products)),
            ("productVariants", sum(len(e["variants"]) for e in products.values())),
            ("fitting", len(fitting)),
            ("accessories", len(accessories)),
            ("others", len(others)),
        ])),
        ("exclusionRules", [
            "CJ廃番 = 1（廃盤）",
            "セット = 1（セット商品）",
            "品番が YY / ZZ 始まり（社内用）",
        ]),
    ])

    def dump(name, obj):
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        return os.path.getsize(path)

    meta["counts"]["accessoryIndexCodes"] = len(acc_index)
    sizes = {
        "products.json": dump("products.json", products),
        "fitting.json": dump("fitting.json", fitting),
        "accessories.json": dump("accessories.json", accessories),
        "accessory_index.json": dump("accessory_index.json", acc_index),
        "others.json": dump("others.json", others),
        "meta.json": dump("meta.json", meta),
    }

    # ---- レポート ----
    print("=" * 62)
    print("SHAD JAPAN 商品カタログ ビルド完了")
    print("=" * 62)
    print(f"入力  : {os.path.relpath(CSV_PATH, ROOT)}  （{total} 行）")
    print(f"除外  : {sum(excluded.values())} 件")
    for k, v in sorted(excluded.items()):
        print(f"          - {k}: {v}")
    print(f"有効  : {len(kept)} 件")
    print()
    print(f"本体商品          : {len(products):4d} モデル "
          f"（{sum(len(e['variants']) for e in products.values())} 品番／カラー違い含む）")
    print(f"フィッティングキット: {len(fitting):4d} 品番")
    print(f"アクセサリー・パーツ: {len(accessories):4d} 品番")
    print(f"その他            : {len(others):4d} 品番")
    print()
    print(f"出力  : {os.path.relpath(OUT_DIR, ROOT)}/")
    for n, s in sizes.items():
        print(f"          {n:20s} {s/1024:8.1f} KB")

    # 本体商品のカラー展開が分かる一覧
    multi = [(c, e) for c, e in products.items() if len(e["variants"]) > 1]
    if multi:
        print()
        print(f"カラー/仕様バリエーションがある本体商品: {len(multi)} モデル")
        for c, e in sorted(multi, key=lambda x: -len(x[1]["variants"]))[:12]:
            colors = " / ".join(v["color"] or "—" for v in e["variants"])
            print(f"          {c:7s} {len(e['variants'])}種  {colors[:64]}")

    missing = [c for c in SITE_CODES if c not in products]
    if missing:
        print()
        print(f"⚠ サイトに製品ページがあるがマスターで未検出: {', '.join(missing)}")


if __name__ == "__main__":
    main()
