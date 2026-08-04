"""
SHAD_モデルグループ.csv → dist/model_groups.json 生成

HTML の JS 側では車種名の先頭英字をプレフィックスとして自動抽出してグループ化する。
このスクリプトはその自動抽出結果を上書きする例外マッピングを JSON に変換する。

CSV カラム:
  prefix : JS が自動抽出するプレフィックス（先頭の英字部分、例: CBR）
  group  : 表示グループ名（例: CB）— prefix と異なる場合のみ記載が必要

例: CBR650R → JS は "CBR" と抽出するが、"CB" グループにまとめたい場合に記載
"""

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
DIST_DIR = os.path.join(ROOT, "dist")

prefix_normalize = {}

with open(os.path.join(DATA_DIR, "SHAD_モデルグループ.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        prefix = row["prefix"].strip().upper()
        group = row["group"].strip()
        # prefix と group が同じ行は変換不要なので除外（CSV の記載ミス対策も兼ねる）
        if prefix and group and prefix != group:
            prefix_normalize[prefix] = group

out = {"prefix_normalize": prefix_normalize}
with open(os.path.join(DIST_DIR, "model_groups.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"dist/model_groups.json 生成: {len(prefix_normalize)} 件のマッピング")
for k, v in prefix_normalize.items():
    print(f"  {k} → {v}")
