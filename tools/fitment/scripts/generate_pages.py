"""
商品ごとの適合HTML生成スクリプト

テンプレート HTML の特定文字列を置換して商品ページを量産する。
  トップケース : templates/baseplateS.html → タイトル・fetch 先 JSON を差し替え
  サイドケース : templates/sidecaseS.html → タイトル・ケースコードフィルタを差し替え
出力 : dist/{製品コード}.html

旧 SHAD_ベースプレート.csv / SHAD_TOPCASE.csv は ItemList_SHAD.csv に統合された。
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(ROOT, "dist")
TEMPLATES_DIR = os.path.join(ROOT, "templates")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/ を import パスに追加
from itemlist_common import load_items, is_catalog_visible

# サイドケース商品コード（sidecaseS.html ベースで生成する対象）
SIDE_CASE_CODES = ["SH23", "SH35", "SH36", "SH38X"]


def read_baseplate_mapping(items):
    """メインシリーズ='ベースプレート' の単品行 → {品番: メーカー品番(SHADコード)}

    セット内容・付属品に記載されたベースプレートの品番を SHAD 品番に変換するために使用。
    """
    mapping = {}
    for row in items:
        if row["メインシリーズ"] != "ベースプレート" or not is_catalog_visible(row):
            continue
        cj_code = row["品番"].strip()
        shad_code = row["メーカー品番"].strip()
        if cj_code and shad_code:
            mapping[cj_code] = shad_code
    return mapping


def read_product_baseplate_mapping(items):
    """ベースプレート単品行のメーカータイプから {製品コード: SHADフィッティングキットコード} を構築

    TERRA 製品（TR37/TR48/TR55 等）はセット内容・付属品にベースプレート品番が記載されていないため、
    ベースプレートのメーカータイプ列を逆引きしてフォールバックとして使用する。
    同一製品コードが複数ベースプレートに対応する場合は先頭行（最初の一致）を採用。
    """
    mapping = {}
    for row in items:
        if row["メインシリーズ"] != "ベースプレート" or not is_catalog_visible(row):
            continue
        shad_code = row["メーカー品番"].strip()
        for part in row["メーカータイプ"].split("_"):
            part = part.strip()
            # shad_code 自身や空文字・重複は除外
            if part and part != shad_code and part not in mapping:
                mapping[part] = shad_code
    return mapping


TOPCASE_LIKE_CATEGORIES = {"トップケース・リアボックス", "シートバッグ"}


def read_topcase_baseplates(items):
    """カテゴリ='トップケース・リアボックス'/'シートバッグ' の単品行 → {製品コード: ベースプレートコード(SHAD)}

    シートバッグ（TR50等）もベースプレート経由で装着するため対象に含める。

    ベースプレートコードの解決優先順位:
    1. セット内容・付属品の「品番: XXXX」から抽出 → ベースプレート単品行で 品番→SHADコード 変換
    2. ベースプレートのメーカータイプ逆引き（TERRA 製品等のフォールバック）
    """
    cj_to_bp = read_baseplate_mapping(items)
    product_to_bp = read_product_baseplate_mapping(items)
    result = {}
    for row in items:
        if row["カテゴリ名"] not in TOPCASE_LIKE_CATEGORIES or not is_catalog_visible(row):
            continue
        code = row["メーカータイプ"].strip()
        if not code or code in result:
            continue  # 同一製品コードが複数行ある場合は最初の行を採用
        # セット内容・付属品から「品番：D1B40PAR」のような記載を正規表現で抽出
        m = re.search(r'品番[：:]\s*([A-Za-z0-9]+)', row.get("セット内容・付属品", ""))
        if m:
            result[code] = cj_to_bp.get(m.group(1))
        else:
            result[code] = product_to_bp.get(code)
    return result


def generate_topcase_page(code, bp_code):
    """baseplateS.html をベースにトップケース商品ページを生成

    テンプレート内の固定文字列（タイトル・fetch URL）を商品コード固有の値に置換する。
    """
    with open(os.path.join(TEMPLATES_DIR, "baseplateS.html"), encoding="utf-8") as f:
        html = f.read()

    html = html.replace(
        "<title>SHAD D1B40PAR 適合車種検索</title>",
        f"<title>{code} 適合車種</title>",
    ).replace(
        "<h1>SHAD D1B40PAR 適合車種検索</h1>",
        f"<h1>{code} 適合車種</h1>",
    ).replace(
        # fetch 先を商品対応のベースプレート JSON に変更
        "fetch('data.json')",
        f"fetch('topcase_{bp_code}.json')",
    )

    out_path = os.path.join(DIST_DIR, f"{code}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def generate_sidecase_page(code):
    """sidecaseS.html をベースにサイドケース商品ページを生成

    全サイドケースデータ（sidecase_data.json）をロードした後、
    JS 側で cases フィールドに該当コードを含む行だけにフィルタリングする。
    """
    with open(os.path.join(TEMPLATES_DIR, "sidecaseS.html"), encoding="utf-8") as f:
        html = f.read()

    html = html.replace(
        "<title>SHAD サイドケース 適合フィッティングキット検索</title>",
        f"<title>{code} 適合フィッティングキット</title>",
    ).replace(
        "<h1>SHAD サイドケース 適合フィッティングキット検索</h1>",
        f"<h1>{code} 適合フィッティングキット</h1>",
    ).replace(
        # init に渡すデータを商品コードで事前フィルタ（全データ共通の JSON を使い回すため JS 側でフィルタ）
        ".then(([DATA, GROUPS]) => init(DATA, GROUPS))",
        f".then(([DATA, GROUPS]) => init(DATA.filter(d => d.cases.includes('{code}')), GROUPS))",
    ).replace(
        # 商品個別ページではケースサイズ絞り込みボタンは不要なため非表示に
        "<label>ケースサイズで絞り込む</label>\n<div id=\"caseButtons\"></div>\n\n<hr class=\"section-divider\">\n\n",
        "<div id=\"caseButtons\" style=\"display:none\"></div>\n\n",
    ).replace(
        "ケースサイズまたはメーカーを選択するか、キーワードを入力してください",
        "メーカーを選択するか、キーワードを入力してください",
    )

    out_path = os.path.join(DIST_DIR, f"{code}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def main():
    items = load_items()
    baseplates = read_topcase_baseplates(items)
    generated = []
    skipped = []

    print("=== トップケース ===")
    for code, bp in baseplates.items():
        if bp is not None:
            # 対応する topcase_*.json が存在する場合のみ生成（JSON 未生成なら先に generate_topcase_data.py を実行）
            json_path = os.path.join(DIST_DIR, f"topcase_{bp}.json")
            if os.path.exists(json_path):
                generate_topcase_page(code, bp)
                generated.append(f"{code}.html")
                print(f"  ✓ {code}.html  ({bp})")
            else:
                skipped.append((code, bp))
                print(f"  - {code}: スキップ (JSONファイルなし: topcase_{bp}.json)")
        else:
            skipped.append((code, bp))
            print(f"  - {code}: スキップ (ベースプレートコード不明)")

    print("\n=== サイドケース ===")
    for code in SIDE_CASE_CODES:
        generate_sidecase_page(code)
        generated.append(f"{code}.html")
        print(f"  ✓ {code}.html")

    print(f"\n生成: {len(generated)} ファイル")
    if skipped:
        print(f"スキップ: {len(skipped)} 製品 ({', '.join(c for c, _ in skipped)})")


if __name__ == "__main__":
    main()
