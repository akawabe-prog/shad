"""
data/ItemList_SHAD.csv → dist/data.json 生成

D1B40PAR ベースプレート対応商品の適合車種一覧を JSON に変換する。
baseplateS.html テンプレートが fetch('data.json') で読み込む
（実際に生成される各商品ページでは topcase_{コード}.json に差し替えられるため、
テンプレートのデフォルト表示用としてのみ使われる）。

旧 D1B40PAR.csv は ItemList_SHAD.csv に統合されたため、メインシリーズ=
'トップマスターフィッティングキット' の単品行から同等のデータを再構築する。
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/ を import パスに追加
from utils import expand_models, override_maker
from itemlist_common import load_items, is_kit_visible, normalize_maker, product_url

DIST_DIR = os.path.join(ROOT, "dist")

TARGET_CODE = "D1B40PAR"
TOPCASE_KIT_PREFIX = "トップマスターフィッティングキット "

records = []
for row in load_items():
    if row["メインシリーズ"] != "トップマスターフィッティングキット" or not is_kit_visible(row):
        continue
    # メーカータイプは "_" 区切りで複数の対応品番を持つ。TARGET_CODE が含まれる行だけ対象
    if TARGET_CODE not in row["メーカータイプ"].split("_"):
        continue
    cj_code = row["品番"]
    maker = normalize_maker(override_maker(cj_code, row["対応メーカー"]))
    name = row["商品名"]
    if name.startswith(TOPCASE_KIT_PREFIX):
        name = name[len(TOPCASE_KIT_PREFIX):]
    # 連名表記のキット（CJ_CODE_MODEL_SPLIT 対象）は複数の車種行に分割される
    for model_name, group in expand_models(cj_code, name, row["代表適合車種"],
                                           row["対応メーカー"], row["商品名"]):
        records.append({
            "url": product_url(cj_code),
            "maker": maker,
            "model": model_name,
            "group": group,
        })

output_path = os.path.join(DIST_DIR, "data.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"{len(records)} 件 → dist/data.json")
