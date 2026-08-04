"""
ビルドスクリプト — 全スクリプトを順番に実行

実行順:
  1. generate_groups.py      : SHAD_モデルグループ.csv → dist/model_groups.json
  2. generate_data.py        : D1B40PAR.csv → dist/data.json
  3. generate_topcase_data.py: SHAD_トップ*.csv → dist/topcase_*.json
  4. generate_sidecase_data.py: SHADサイドケース*.csv → dist/sidecase_data.json
  5. generate_pages.py       : templates/ + dist/*.json → dist/*.html
  6. generate_reverse_data_from_itemlist.py : ItemList_SHAD.csv → dist/reverse_data.json + model_search.html
  7. generate_kit_pages.py   : dist/reverse_data.json → dist/fitting_*.html（一覧ページ）
  8. generate_fitting_kits_overview.py : dist/reverse_data.json → dist/fitting_kits.html（概要ページ）

旧 generate_reverse_data.py（個別CSV5分割版）は ItemList_SHAD.csv 一本化に伴い
bak/scripts/ へ退避済み。同様に data/SHADサイドケース.csv も bak/data/ へ退避済み
（旧スクリプトのみが参照していたため）。

使い方:
  python3 build.py
"""

import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(ROOT, "scripts")

STEPS = [
    ("generate_groups.py",       "モデルグループJSON"),
    ("generate_data.py",         "ベースプレートデータJSON"),
    ("generate_topcase_data.py", "トップケースデータJSON"),
    ("generate_sidecase_data.py","サイドケースデータJSON"),
    ("generate_pages.py",        "製品ページHTML"),
    ("generate_reverse_data_from_itemlist.py", "車種逆引きデータJSON + 検索ページ"),
    ("generate_kit_pages.py",     "フィッティングキット一覧ページ"),
    ("generate_fitting_kits_overview.py", "フィッティングキット概要ページ"),
]

def main():
    ok = True
    for script, label in STEPS:
        path = os.path.join(SCRIPTS_DIR, script)
        print(f"\n▶ {label} ({script})")
        result = subprocess.run([sys.executable, path], capture_output=False)
        if result.returncode != 0:
            print(f"  ✗ エラー終了 (code {result.returncode})")
            ok = False
            break

    print()
    if ok:
        print("✓ ビルド完了")
    else:
        print("✗ ビルド失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()
