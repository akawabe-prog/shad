"""
data/ItemList_SHAD.csv → dist/sidecase_data.json 生成

3P・4Pシステム両方のサイドケースフィッティングキットを1つの JSON に統合する。
sidecaseS.html テンプレートが fetch('sidecase_data.json') で読み込み、
各商品ページ（SH23.html 等）はロード後に cases フィールドでフィルタリングする。

旧 SHADサイドケースフィッティング3P4P.csv は ItemList_SHAD.csv に統合された。
廃番（CJ廃番=1）は is_kit_visible で除外済みのため discontinued フィールドは持たない
（reverse_data.json 側の方針と統一）。
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/ を import パスに追加
from utils import expand_models, override_maker
from itemlist_common import load_items, is_kit_visible, normalize_maker, product_url

DIST_DIR = os.path.join(ROOT, "dist")

# 対象サイドケース品番。メーカータイプに含まれるものだけ cases フィールドに記録する
# （sidecaseS.html 個別ページは SH23/SH35/SH36/SH38X の4種のみ生成するため、旧スクリプトと同じ範囲に揃える）
SIDE_CASES = {"SH23", "SH35", "SH36", "SH38X"}

records = []
for row in load_items():
    if row["メインシリーズ"] not in ("3Pシステムフィッティングキット", "4Pシステムフィッティングキット"):
        continue
    if not is_kit_visible(row):
        continue
    cj_code = row["品番"]
    maker = normalize_maker(override_maker(cj_code, row["対応メーカー"]))
    system = "3P" if "3P" in row["メインシリーズ"] else "4P"
    # メーカータイプの "_" 区切りリストから SIDE_CASES に該当するものだけ抽出
    cases = [c for c in row["メーカータイプ"].split("_") if c in SIDE_CASES]

    # 商品名からシリーズプレフィックスを除去して車種名だけ残す
    # 例: "3Pシステムフィッティングキット CB500X(13-18)" → "CB500X(13-18)"
    prefix = row["メインシリーズ"] + " "
    item_name = row["商品名"]
    name = item_name[len(prefix):] if item_name.startswith(prefix) else item_name

    # 連名表記のキット（CJ_CODE_MODEL_SPLIT 対象）は複数の車種行に分割される
    for model_name, group in expand_models(cj_code, name, row["代表適合車種"],
                                           row["対応メーカー"], row["商品名"]):
        records.append({
            "url": product_url(cj_code),
            "maker": maker,
            "name": model_name,
            "models": row["代表適合車種"],
            "system": system,
            "cases": cases,           # 対応ケース品番リスト（UI のフィルタリングに使用）
            "group": group,
        })

output_path = os.path.join(DIST_DIR, "sidecase_data.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"{len(records)} 件 → dist/sidecase_data.json")
