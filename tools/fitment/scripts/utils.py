"""
共通ユーティリティ

get_group() : CSV の compatible_models / compatible_maker / item_name から
              UI 表示用グループ名を返す。

ルールの優先順位は上から評価される（CASE WHEN と同じ挙動）。
最下部の else がフォールバック（先頭の英字を自動抽出）。

ルールの追加方法は README 参照。
"""

import re

# cj_code 単位のメーカー上書き
# S0VS12ST: KLV1000 は日本未販売のためカワサキ表記だが実質スズキVストロームと同一モデル
CJ_CODE_MAKER_OVERRIDE = {
    "S0VS12ST": "スズキ",
}


def override_maker(cj_code: str, maker: str) -> str:
    """cj_code 個別のメーカー上書きを適用（全生成スクリプト共通）"""
    return CJ_CODE_MAKER_OVERRIDE.get(cj_code, maker)


# cj_code 単位の表示車種名分割
# 1つのキットが複数車種を連名表記している場合、別々の車種行として表示する
CJ_CODE_MODEL_SPLIT = {
    # スカイウェイブ650/バーグマン650 は名称が異なる別車種扱いにする
    "S0BR62ST": ["スカイウェイブ650(02-08)", "バーグマン650 エグゼクティブ(04-24)"],
    # Dio/Vision/リード は別車種扱いにする
    "H0VS12ST": ["Dio 110(11-25)", "Vision 110(11-26)", "リード125(22-25)"],
}


def expand_models(cj_code: str, display_name: str, compatible_models: str,
                  compatible_maker: str, item_name: str) -> list:
    """(表示車種名, グループ名) のリストを返す。

    CJ_CODE_MODEL_SPLIT に登録された cj_code は複数ペアに分割され、
    グループは分割後の各車種名から判定される。それ以外は1ペア。
    """
    names = CJ_CODE_MODEL_SPLIT.get(cj_code)
    if not names:
        return [(display_name,
                 get_group(compatible_models, compatible_maker, item_name, cj_code))]
    return [(n, get_group(n, compatible_maker, n, cj_code)) for n in names]


def get_group(compatible_models: str, compatible_maker: str, item_name: str, cj_code: str = "") -> str:
    m = compatible_models or ""
    maker = override_maker(cj_code, compatible_maker or "")
    name = item_name or ""

    # cj_code 単位の個別指定
    CJ_CODE_GROUP = {
        "29327300": "400X",
    }
    if cj_code in CJ_CODE_GROUP:
        return CJ_CODE_GROUP[cj_code]

    # ホンダ
    if m.startswith("ADV") and maker == "ホンダ":
        return "ADV"
    if re.match(r"^CB[0-9]", m) and maker == "ホンダ":
        return "CB"
    if re.match(r"^CBF[0-9]", m) and maker == "ホンダ":
        return "CBF"
    if re.match(r"^CBR[0-9]", m) and maker == "ホンダ":
        return "CBR"
    if re.search(r"africa twin", name, re.IGNORECASE):
        return "Africa Twin"
    if m.startswith("ホーネット"):
        return "ホーネット"
    if m.startswith("X-ADV"):
        return "X-ADV"
    if m.startswith("SHモード") or m.startswith("SH MODE"):
        return "SH"
    if m.startswith("フォルツァ") or m.startswith("FORZA"):
        return "FORZA"
    if m.startswith("インテグラ"):
        return "インテグラ"
    if m.startswith("MSX"):
        return "GROM"

    # ヤマハ
    if m.startswith("X-MAX") and maker == "ヤマハ":
        return "XMAX"
    if m.startswith("MT-") and maker == "ヤマハ":
        return "MT"
    if (m.startswith("Delight") or m.startswith("D'elight") or m.startswith("D’elight")) and maker == "ヤマハ":
        return "DELIGHT"
    if m.startswith("グランドマジェスティ") and maker == "ヤマハ":
        return "MAJESTY"
    if m.startswith("マジェスティ") and maker == "ヤマハ":
        return "MAJESTY"
    if m.startswith("トリシティ") and maker == "ヤマハ":
        return "TRICITY"
    # NEO S / NEO'S / NEOS の表記ゆれをまとめる
    if m.startswith("NEO") and maker == "ヤマハ":
        return "NEOS"

    # スズキ
    # 商品名がスカイウェイブの行は compatible_models が輸出名バーグマン始まりのため、item_name で先に判定
    if "スカイウェイブ" in name and maker == "スズキ":
        return "スカイウェイブ"
    if m.startswith("バーグマン") and maker == "スズキ":
        return "バーグマン"
    if m.startswith("アドレス") and maker == "スズキ":
        return "アドレス"
    if (m.startswith("Vストローム") or m.startswith("V-ストローム")) and maker == "スズキ":
        return "Vストローム"
    if m.startswith("バンディット") and maker == "スズキ":
        return "バンディット"
    if m.startswith("グラディウス") and maker == "スズキ":
        return "グラディウス"

    # フォールバック1: 先頭の英字部分を大文字で返す（末尾ハイフンは除去: FZ-1 → FZ）
    mm = re.match(r"^([A-Za-z][A-Za-z\-]*)", m)
    if mm:
        return mm.group(1).upper().rstrip("-")

    # フォールバック2: カタカナ先頭（レブル250 等）はカタカナ部分をグループ名に。
    # 英語表記由来の既存グループと重複するものはマッピングで統合
    KANA_GROUP = {
        "トレーサー": "TRACER",
        "ディバージョン": "DIVERSION",
        "フェザー": "FAZER",
    }
    mm = re.match(r"^([ァ-ヴー]+)", m)
    if mm:
        return KANA_GROUP.get(mm.group(1), mm.group(1))

    # フォールバック3: 数字先頭（400X 等）は数字+英字部分をグループ名に
    mm = re.match(r"^([0-9]+[A-Za-z\-]*)", m)
    if mm:
        return mm.group(1).upper().rstrip("-")

    return m
