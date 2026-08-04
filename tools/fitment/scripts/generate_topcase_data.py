"""
data/ItemList_SHAD.csv → ベースプレート別 JSON 生成

1つのフィッティングキット行はメーカータイプに複数のベースプレートコードを "_" 区切りで持つ。
対応ベースプレートコードはメインシリーズ='ベースプレート'の単品行のメーカー品番から
自動取得し、各コードごとに dist/topcase_{コード}.json を出力する。

旧 SHAD_ベースプレート.csv / SHAD_トップマスターフィッティングキット.csv は
ItemList_SHAD.csv に統合された。
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/ を import パスに追加
from utils import expand_models, override_maker
from itemlist_common import (
    load_items, is_catalog_visible, is_kit_visible, normalize_maker, product_url,
)

DIST_DIR = os.path.join(ROOT, "dist")

TOPCASE_KIT_PREFIX = "トップマスターフィッティングキット "


def read_target_baseplates(items):
    """メインシリーズ='ベースプレート' の単品行のメーカー品番を重複なしで返す。
    新しいベースプレートが追加されても ItemList 更新だけで自動対応できる。"""
    codes = []
    for row in items:
        if row["メインシリーズ"] != "ベースプレート" or not is_catalog_visible(row):
            continue
        code = row["メーカー品番"].strip()
        if code and code not in codes:
            codes.append(code)
    return codes


def main():
    items = load_items()
    target_baseplates = read_target_baseplates(items)
    records = {bp: [] for bp in target_baseplates}

    for row in items:
        if row["メインシリーズ"] != "トップマスターフィッティングキット" or not is_kit_visible(row):
            continue
        # メーカータイプは "_" 区切りで複数ベースプレートコードを保持
        maker_types = [t for t in row["メーカータイプ"].split("_") if t]
        cj_code = row["品番"]
        maker = normalize_maker(override_maker(cj_code, row["対応メーカー"]))
        # 商品名からシリーズプレフィックスを除去して車種名だけ残す
        name = row["商品名"]
        if name.startswith(TOPCASE_KIT_PREFIX):
            name = name[len(TOPCASE_KIT_PREFIX):]

        # 連名表記のキット（CJ_CODE_MODEL_SPLIT 対象）は複数の車種行に分割される
        for model_name, group in expand_models(cj_code, name, row["代表適合車種"],
                                               row["対応メーカー"], row["商品名"]):
            record = {"url": product_url(cj_code), "maker": maker, "model": model_name, "group": group}

            # 1行が複数ベースプレートに対応する場合、それぞれのリストに追加
            for bp in target_baseplates:
                if bp in maker_types:
                    records[bp].append(record)

    for bp, recs in records.items():
        out_path = os.path.join(DIST_DIR, f"topcase_{bp}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(recs, f, ensure_ascii=False, indent=2)
        print(f"  {bp}: {len(recs)}件 → dist/topcase_{bp}.json")


if __name__ == "__main__":
    main()
