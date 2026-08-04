"""
data/ItemList_SHAD.csv（全商品マスタ）を読み込む各生成スクリプト共通のヘルパー。

順引き系（generate_data.py / generate_topcase_data.py / generate_sidecase_data.py /
generate_pages.py）・逆引き系（generate_reverse_data_from_itemlist.py）の両方が
同じ ItemList_SHAD.csv を読むため、可視性フィルタやURL組み立てなどの共通処理を
ここに集約する。
"""

import csv
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(ROOT))   # SHAD_ReBranding
DATA_DIR = os.path.join(ROOT, "data")
# 商品マスターはプロジェクト共通の data-source/ を参照する（重複管理を避ける）
MASTER_DIR = os.path.join(PROJECT_ROOT, "data-source")

ITEMLIST_CSV = os.path.join(MASTER_DIR, "ItemList_SHAD.csv")
ITEMLIST_ENCODING = "cp932"  # ECサイト側エクスポートは Shift_JIS 系

BASE_URL = "https://moto.customjapan.net/i/"

# BigQuery の compatible_maker 表記を表示用に統一（全生成スクリプト共通）
MAKER_NORMALIZE = {
    "CF MOTO": "CFMOTO",
    "MOTO GUZZI": "Moto Guzzi",
    "KEEWAY": "Keeway",
    "ROYAL ENFIELD": "Royal Enfield",
    "RIEJU": "Rieju",
    "Husqvarna_KTM": "KTM/Husqvarna",
    "PEUGEOT": "Peugeot",
}


def normalize_maker(maker):
    maker = MAKER_NORMALIZE.get(maker, maker)
    if "_" in maker:
        maker = maker.replace("_", "/")
    return maker


def product_url(cj_code):
    return BASE_URL + cj_code.strip()


def product_img(cj_code):
    return f"https://img.customjapan.net/items/{cj_code.strip()}_1.jpg"


def load_items():
    with open(ITEMLIST_CSV, encoding=ITEMLIST_ENCODING) as f:
        return list(csv.DictReader(f))


def is_catalog_visible(row):
    """一覧・Webに表示される、セット品/アウトレット品/廃番品以外の単品SKU"""
    return (row["一覧非表示"] == "0" and row["Web非表示"] == "0"
            and row["セット"] == "0" and row["アウトレット"] == "0"
            and row["CJ廃番"] == "0")


def is_kit_visible(row):
    """一覧・Webに表示され、アウトレット（訳あり）/廃番ではないキット単品行"""
    return (row["一覧非表示"] == "0" and row["Web非表示"] == "0"
            and row["アウトレット"] == "0" and row["CJ廃番"] == "0")


# トップケース・サイドケースはSHAD品番の数字部分がそのまま容量(L)と一致する命名規則
# （SH23=23L、SH48=48L、TR55=55L 等）。容量列・商品名のどちらにも記載がない一部SKU
# （SH23/35/36/38X/44/45/47/48/58X/59X）救済用の最終フォールバック。
CAPACITY_FALLBACK_CATEGORIES = {"トップケース・リアボックス", "パニア・サイドケース・サイドボックス"}


def _parse_liters(text):
    """テキストから容量(L)の数値を抽出する。括弧内（片側○○L 等の補足）は無視し、
    複数マッチした場合は最大値を採用する（例: "46-58L(片側23-29L)" → 58）。"""
    if not text:
        return None
    stripped = re.sub(r"[（(][^)）]*[)）]", "", text)
    nums = [int(n) for n in re.findall(r"(\d+)\s*L", stripped, re.IGNORECASE)]
    return max(nums) if nums else None


def capacity_for(row):
    """行の容量(L)を返す。容量列 → 商品名 → （トップ/サイドケースのみ）品番の数字、の順に解決。
    どれからも取得できない場合は None。"""
    cap = _parse_liters(row.get("容量", ""))
    if cap is not None:
        return cap
    cap = _parse_liters(row.get("商品名", ""))
    if cap is not None:
        return cap
    if row.get("カテゴリ名") in CAPACITY_FALLBACK_CATEGORIES:
        m = re.search(r"(\d+)", row.get("メーカータイプ", "").strip())
        if m:
            return int(m.group(1))
    return None
