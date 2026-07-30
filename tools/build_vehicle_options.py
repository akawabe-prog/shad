#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 車種別オプション（バックレストキット / シーシーバーキット）索引
=============================================================================
バックレストキットとシーシーバーキットは「ボックスの型番」ではなく
「車種」に紐づく商品なので、適合検索の結果に一緒に出せるように
車種 → オプション商品 の索引を作ります。

■ 使い方
    python3 tools/build_vehicle_options.py
        → site/data/fitment/vehicle_options.json を出力

■ 突き合わせ方法
    マスターの「代表適合車種（モデル[年式]）」と「対応メーカー」を、
    適合検索の車種リスト（fitment_index.json）とメーカー・車種名・年式で照合。
    照合できなかったキットはレポートに出すので、必要なら
    MANUAL_MATCH に車種IDを直接書いて補完できます。
=============================================================================
"""

import csv
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data-source", "ItemList_SHAD.csv")
INDEX_PATH = os.path.join(ROOT, "site", "data", "fitment", "fitment_index.json")
OUT_PATH = os.path.join(ROOT, "site", "data", "fitment", "vehicle_options.json")
BUY_BASE = "https://moto.customjapan.net/i/"
IMG_BASE = "https://img.customjapan.net/items/{}_1.jpg"

# 商品名の先頭でオプション種別を判定
OPTION_TYPES = (
    ("バックレストキット", "バックレスト"),
    ("シーシーバーキット", "シーシーバー"),
)

# メーカー表記の揺れ（マスター ↔ 適合検索）
MAKER_ALIASES = {
    "ホンダ": {"ホンダ", "honda"},
    "ヤマハ": {"ヤマハ", "yamaha"},
    "スズキ": {"スズキ", "suzuki"},
    "カワサキ": {"カワサキ", "kawasaki"},
    "bmw": {"bmw"},
    "ducati": {"ducati", "ドゥカティ"},
    "piaggio": {"piaggio", "ピアジオ"},
    "kymco": {"kymco", "キムコ"},
    "sym": {"sym"},
    "zontes": {"zontes"},
    "benda": {"benda"},
    "keeway": {"keeway"},
    "silence": {"silence"},
    "royalenfield": {"royalenfield", "royal enfield", "ロイヤルエンフィールド"},
    "qjmotor": {"qjmotor", "qj motor"},
    "morbidelli": {"morbidelli"},
    "hyosung": {"hyosung", "ヒョースン"},
    "aeon": {"aeon"},
}

# 自動照合できない車種を手動で紐づける場合（品番 → 車種ID の配列）
MANUAL_MATCH = {}


def cell(row, key):
    return (row.get(key) or "").strip()


def norm(s):
    s = unicodedata.normalize("NFKC", str(s or "")).lower()
    return re.sub(r"[^a-z0-9ぁ-んァ-ヶー一-龠]", "", s)


def maker_key(s):
    n = norm(s)
    for key, names in MAKER_ALIASES.items():
        if any(norm(x) == n or norm(x) in n for x in names):
            return key
    return n


def parse_years(label):
    """'17-24' や '2025' → (2017, 2024) の西暦範囲。"""
    nums = re.findall(r"\d{2,4}", str(label or ""))
    if not nums:
        return None
    def y(v):
        v = int(v)
        if v >= 1000:
            return v
        return 2000 + v if v < 80 else 1900 + v
    ys = [y(v) for v in nums]
    return min(ys), max(ys)


def years_overlap(a, b):
    if not a or not b:
        return True          # 年式が読めないときは絞り込みに使わない
    return a[0] <= b[1] and b[0] <= a[1]


def _letters(s):
    return re.sub(r"[0-9]", "", norm(s))


def _numbers(s):
    """車種名に含まれる排気量などの数値（年式は含まない前提）。"""
    return set(re.findall(r"\d{2,4}", unicodedata.normalize("NFKC", str(s or ""))))


def model_match(kit_model, veh_model):
    """車種名の緩い一致。
    ・括弧内（フレーム型式・別称）は無視
    ・文字部分がどちらかを含む　かつ　排気量の数値が重なる"""
    kit_model = re.sub(r"[(（][^)）]*[)）]", " ", str(kit_model or ""))
    veh_model = re.sub(r"[(（][^)）]*[)）]", " ", str(veh_model or ""))
    a, b = norm(kit_model), norm(veh_model)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    la, lb = _letters(a), _letters(b)
    if not la or not lb:
        return False
    if not (la in lb or lb in la):
        return False
    na, nb = _numbers(kit_model), _numbers(veh_model)
    if na and nb:
        return bool(na & nb)
    # 片方に排気量が無い場合は、文字部分が完全一致するときだけ同一車種とみなす
    # （例：ADV350 と X-ADV を取り違えないため）
    return la == lb


def main():
    index = json.load(open(INDEX_PATH, encoding="utf-8"))
    vehicles = index["vehicles"]

    rows = list(csv.DictReader(open(CSV_PATH, encoding="cp932", errors="replace")))
    kits = []
    for r in rows:
        name = cell(r, "商品名")
        if cell(r, "CJ廃番") == "1" or "【セット品】" in name:
            continue
        kind = next((label for prefix, label in OPTION_TYPES if name.startswith(prefix)), None)
        if not kind:
            continue
        kits.append((r, kind))

    out = {}
    matched, unmatched = 0, []
    for r, kind in kits:
        code = cell(r, "品番")
        name = cell(r, "商品名")
        mk = maker_key(cell(r, "対応メーカー"))
        groups = [g.strip() for g in cell(r, "代表適合車種").split("｜") if g.strip()]

        ids = set(MANUAL_MATCH.get(code, []))
        for g in groups:
            m = re.match(r"^(.*?)\[(.*?)\]\s*$", g)
            gm, gy = (m.group(1), m.group(2)) if m else (g, "")
            ky = parse_years(gy)
            for v in vehicles:
                if maker_key(v.get("maker")) != mk:
                    continue
                if not years_overlap(ky, parse_years(v.get("yearLabel"))):
                    continue
                vm = re.sub(r"^\s*" + re.escape(str(v.get("maker") or "")) + r"\s*", "",
                            str(v.get("modelKey") or ""), flags=re.I)
                if model_match(gm, vm) or model_match(gm, v.get("modelKey")):
                    ids.add(v["id"])

        if not ids:
            unmatched.append({"cjCode": code, "name": name, "maker": cell(r, "対応メーカー"),
                              "groups": groups})
            continue
        matched += 1
        item = {
            "cjCode": code,
            "type": kind,
            "name": name,
            "url": BUY_BASE + code,
            "image": IMG_BASE.format(code),
            "priceTaxIn": int(re.sub(r"[^\d]", "", cell(r, "希望小売価格(税込)")) or 0) or None,
            "fit": cell(r, "代表適合車種"),
        }
        for vid in ids:
            out.setdefault(vid, []).append(item)

    for vid in out:
        out[vid].sort(key=lambda x: (x["type"], x["priceTaxIn"] or 0))

    payload = {
        "generatedAt": index.get("generatedAt"),
        "source": "data-source/ItemList_SHAD.csv",
        "counts": {"kits": len(kits), "matched": matched, "unmatched": len(unmatched),
                   "vehicles": len(out)},
        "unmatched": unmatched,
        "byVehicle": out,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    json.dump(payload, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("=" * 62)
    print("車種別オプション索引を出力: site/data/fitment/vehicle_options.json")
    print("=" * 62)
    print("対象キット      : %d 品番（バックレスト / シーシーバー）" % len(kits))
    print("車種と紐づけ済み: %d 品番 → %d 車種" % (matched, len(out)))
    print("紐づけできず    : %d 品番" % len(unmatched))
    for u in unmatched:
        print("    %-10s %-46s %s" % (u["cjCode"], u["name"][:46], (u["groups"] or [""])[0][:34]))
    print("\n※ 紐づけできないものは MANUAL_MATCH に車種IDを追記すると反映されます。")


if __name__ == "__main__":
    main()
