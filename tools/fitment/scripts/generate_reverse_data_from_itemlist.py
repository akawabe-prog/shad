"""
data/ItemList_SHAD.csv（全商品マスタ）から dist/reverse_data.json を生成し、
templates/model_search.html を dist/ にコピーする。

旧 generate_reverse_data.py は個別エクスポートCSV（ベースプレート/トップマスター
フィッティングキット/TOPCASE/サイドケース/サイドケースフィッティング3P4P）を
ソースにしていたが、ItemList_SHAD.csv は同じ商品群を1本のマスタに含んでいるため、
カテゴリ・メインシリーズ列で絞り込んで同等のデータを再構築する。

出力 JSON 構造は旧スクリプトと同じ（tankbags/sidebags/clicksystem_kits のみ新規追加）:
  plates    : {ベースプレートコード: {name, url, topcases: [{name, url, img, capacity, included}]}}
  sidecases : {ケースコード: [{name, url, img, capacity}]}  # カテゴリ='パニア・サイドケース・サイドボックス'（ハードケース）
  sidebags  : {ケースコード: [{name, url, img, capacity}]}  # カテゴリ='サイドバッグ'（ソフトバッグ）
  tankbags  : [{name, url, img, capacity}]        # 車種フィッティングとは連動しない全SKU一覧
  clicksystem_kits : [{name, url, maker, models, cases}]  # 参照用一覧のみ（車種紐付けなし）
  bikes     : [{maker, model, group,
                top:  [{plate, url, name}],
                side: [{system, url, name, cases}]}]

capacity（容量・単位L）は itemlist_common.capacity_for() で解決する数値または null。
容量列 → 商品名の「NNL」表記 → （トップ/サイドケースのみ）品番の数字部分、の順で
フォールバックする（SH23=23L 等、SHAD品番の数字がそのまま容量と一致する命名規則を利用）。

すべての商品・キットは CJ廃番=1（廃盤）を除外している（is_catalog_visible /
is_kit_visible）。廃盤バッジを付けて表示を継続する設計ではなく、完全に除外する。

sidecases/sidebags は商品カテゴリで分けて表示するが、3P/4Pキット・サイドバッグ
ホルダーキットの cases 列（対応コード一覧）はハード/ソフトを区別しないため、
車種別フィッティング結果を組み立てる側（テンプレートJS）は両方の辞書を合わせて引く。

サイドバッグ（E48/SW42/SL58）は「サイドバッグホルダーキット」、カフェレーサー系
サイドバッグ（E48SR/SR38）は「SRバッグフィッティングキット」経由で車種に取り付ける
ため、3P/4Pキットと同様に bikes[].side に組み込む（shad.es の "SE specific" /
"Specific SR" 区分に相当）。ただし1件だけ「トップマスター取付 ※要適合確認」という
複数メーカー・複数車種を【YAMAHA】【HONDA】...のセクション見出しでまとめた特殊行
（shad.es の "Universal side bag holder" D0SS5SE に相当）があり、クリックシステム
と同じ理由（1行=1車種の前提が崩れる）で対象外にしている。

タンクバッグはベルト/マグネット等で直接取り付ける汎用品、またはクリックシステムの
ように1キットが複数メーカー・複数車種にまたがる複合表記（代表適合車種／対応メーカー
とも複数値の組み合わせ）で、トップ/サイドケース用キットのような「1行=1メーカー+1車種」
という前提が成り立たない。自動での車種別マッチングは誤適合のリスクが高いため、車種
フィッティングには組み込まず、全商品一覧にのみ表示する（データ生成元と相談済み）。
"""

import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # scripts/ を import パスに追加
from utils import expand_models, override_maker
from itemlist_common import (
    load_items, is_catalog_visible, is_kit_visible,
    normalize_maker, product_url, product_img, capacity_for,
)

DIST_DIR = os.path.join(ROOT, "dist")
TEMPLATES_DIR = os.path.join(ROOT, "templates")

TOPCASE_KIT_PREFIX = "トップマスターフィッティングキット "

# ベースプレート経由で装着するトップケース系カテゴリ
# （TR50 のようにカテゴリが「シートバッグ」の製品も含む。generate_pages.py と同じ範囲）
TOPCASE_LIKE_CATEGORIES = {"トップケース・リアボックス", "シートバッグ"}


def read_plates(items):
    """メインシリーズ='ベースプレート' の単品SKUからプレートカタログを構築

    返り値:
      plates      : {SHADコード(メーカー品番): {name, url, img, topcases: []}}
      cj_to_plate : {品番: SHADコード}（セット内容・付属品の品番変換用）
      code_plates : {トップケース製品コード: [SHADコード, ...]}（メーカータイプ逆引き）
    """
    plates = {}
    cj_to_plate = {}
    code_plates = {}
    for row in items:
        if row["メインシリーズ"] != "ベースプレート" or not is_catalog_visible(row):
            continue
        shad_code = row["メーカー品番"].strip()
        if not shad_code:
            continue
        # 商品名末尾の対応製品リスト（"TR37/TR48/…"）を除いた部分を表示名にする
        name_tokens = [t for t in row["商品名"].split() if "/" not in t]
        plates[shad_code] = {
            "name": " ".join(name_tokens),
            "url": product_url(row["品番"]),
            "img": product_img(row["品番"]),
            "topcases": [],
        }
        cj_to_plate[row["品番"].strip()] = shad_code
        for part in row["メーカータイプ"].split("_"):
            part = part.strip()
            if part and part != shad_code:
                code_plates.setdefault(part, []).append(shad_code)
    return plates, cj_to_plate, code_plates


def attach_topcases(items, plates, cj_to_plate, code_plates):
    """カテゴリ='トップケース・リアボックス' の単品SKUを対応ベースプレートに紐付け

    ベースプレート解決:
      1. セット内容・付属品の「品番：XXXX」→ そのプレートが付属 (included=True)
      2. 記載なし → メーカータイプのプレート逆引きで全対応プレート (included=False)
    """
    for row in items:
        if not is_catalog_visible(row):
            continue
        code = row["メーカータイプ"].strip()
        if not code:
            continue
        # トップケース系カテゴリ（シートバッグ含む）に加え、商品側のカテゴリが違っても
        # ベースプレート側のメーカータイプが対応を宣言している製品はプレート配下に載せる。
        if row["カテゴリ名"] not in TOPCASE_LIKE_CATEGORIES and code not in code_plates:
            continue
        sku = {"name": row["商品名"], "url": product_url(row["品番"]),
               "img": product_img(row["品番"]), "capacity": capacity_for(row)}
        m = re.search(r"品番[：:]\s*([A-Za-z0-9]+)", row.get("セット内容・付属品", ""))
        if m and cj_to_plate.get(m.group(1)):
            targets = [(cj_to_plate[m.group(1)], True)]
        else:
            targets = [(bp, False) for bp in code_plates.get(code, [])]
        for bp, included in targets:
            if bp in plates:
                plates[bp]["topcases"].append({**sku, "included": included})
    for p in plates.values():
        p["topcases"].sort(key=lambda s: s["name"])


def collect_side_codes(items):
    """3P/4Pシステムフィッティングキットのメーカータイプ列から対応ケースコード一覧を収集"""
    codes = set()
    for row in items:
        if row["メインシリーズ"] not in ("3Pシステムフィッティングキット", "4Pシステムフィッティングキット"):
            continue
        for part in row["メーカータイプ"].split("_"):
            part = part.strip()
            if part:
                codes.add(part)
    return codes


def read_case_products_by_category(items, category):
    """指定カテゴリの単品SKUをメーカータイプ（コード）別に集める

    サイドケース（パニア・サイドケース・サイドボックス）とサイドバッグは別カテゴリ
    だが、どちらも3P/4Pキットの cases 列から同じ仕組みで参照されるため、
    呼び出し側はカテゴリごとに本関数を呼んで別々の辞書として保持する。
    """
    products = {}
    for row in items:
        if row["カテゴリ名"] != category or not is_catalog_visible(row):
            continue
        code = row["メーカータイプ"].strip()
        if not code:
            continue
        products.setdefault(code, []).append(
            {"name": row["商品名"], "url": product_url(row["品番"]),
             "img": product_img(row["品番"]), "capacity": capacity_for(row)}
        )
    for skus in products.values():
        skus.sort(key=lambda s: s["name"])
    return products


def read_tankbag_products(items):
    """カテゴリ='タンクバッグ' の単品SKUを名前で一意化して集める（車種紐付けなし）"""
    seen = {}
    for row in items:
        if row["カテゴリ名"] != "タンクバッグ" or not is_catalog_visible(row):
            continue
        name = row["商品名"]
        if name not in seen:
            seen[name] = {"name": name, "url": product_url(row["品番"]),
                          "img": product_img(row["品番"]), "capacity": capacity_for(row)}
    return sorted(seen.values(), key=lambda s: s["name"])


def read_clicksystem_kits(items):
    """クリックシステムフィッティングキット単位の参照用一覧（車種紐付けなし）

    1キットが複数メーカー・複数車種にまたがる複合表記で自動車種マッチングは
    行わないため（モジュール docstring 参照）、代表適合車種は生テキストのまま
    保持し、参照用の一覧ページ（クリックシステム一覧）でのみ表示する。
    """
    tankbag_codes = {row["メーカータイプ"].strip() for row in items
                      if row["カテゴリ名"] == "タンクバッグ" and is_catalog_visible(row)
                      and row["メーカータイプ"].strip()}

    kits = []
    for row in items:
        if row["メインシリーズ"] != "クリックシステム" or row["カテゴリ名"] != "フィッティングキット・ステー・ベース":
            continue
        if not is_kit_visible(row) or row["セット"] == "1":
            continue
        cases = [c for c in row["メーカータイプ"].split("_") if c in tankbag_codes]
        models = [m.strip() for m in re.split(r"[｜│]", row["代表適合車種"]) if m.strip()]
        kits.append({
            "name": row["商品名"],
            "url": product_url(row["品番"]),
            "maker": row["対応メーカー"],
            "models": models,
            "cases": cases,
        })
    return sorted(kits, key=lambda k: k["name"])




SPEC_MODELS_RE = re.compile(r"対応モデル[：:]\s*([^\n]+)")
SPEC_PLATE_RE = re.compile(r"対応ベースプレート[：:]\s*([^\n]+)")


def kit_spec_models(row):
    """キットの仕様欄から「対応モデル」を読む。

    マスターの仕様欄はキットごとに対応トップケースを明記している。
      例）NADTN（シーシーバー取付 ※プレート付）
          対応ベースプレート：不要(フィッティングキットに直接取付)
          対応モデル：SH26/SH29/SH33/SH34
    プレート経由の逆引きより確実なので、記載があればこれを正とする。

    返り値: (対応モデルコードのリスト, ベースプレート不要か)
    """
    spec = (row.get("仕様") or "").replace("\\n", "\n")
    m = SPEC_MODELS_RE.search(spec)
    models = []
    if m:
        text = m.group(1)
        if "全て" in text or "すべて" in text:
            # 例）「全てのSHAD＆TERRAトップケース/バッグに対応」→ 全モデル対応
            models = ["*"]
        else:
            # 区切りは「/」「・」「、」「,」。分類の注記（例：（サイドケース））は括弧ごと外す
            text = re.sub(r"[（(][^）)]*[）)]", " ", text)
            for token in re.split(r"[/／・、,\s]+", text):
                token = token.strip()
                if re.fullmatch(r"[A-Za-z0-9]+", token):
                    models.append(token.upper())
    p = SPEC_PLATE_RE.search(spec)
    no_plate = bool(p and "不要" in p.group(1))
    return models, no_plate


MOUNT_KIT_RE = re.compile(r"^(.+?)取付[（(](.+?)[）)]")


def remap_mount_kit(model_name, known_models):
    """「シーシーバー取付(レブル250/500/1100/エリミネーター/バルカンS)」のような
    “取付方法”の名前は車種ではないので、括弧内に挙がっている実在の車種に振り替える。

    括弧内を「/」で分解し、数字だけのトークンには先頭トークンの車名部分を補う
    （例: レブル250/500/1100 → レブル250 / レブル500 / レブル1100）。
    返り値: 振り替え先の車種名リスト（見つからなければ空リスト）
    """
    m = MOUNT_KIT_RE.match(model_name)
    if not m:
        return None
    tokens = [t.strip() for t in m.group(2).split("/") if t.strip()]
    if not tokens:
        return []
    stem = re.match(r"^[^\d]*", tokens[0]).group(0)
    keywords = []
    for t in tokens:
        keywords.append(t)
        if stem and re.match(r"^[\d]", t):
            keywords.append(stem + t)
    hits = []
    for km in known_models:
        if any(k and k in km for k in keywords if len(k) >= 3):
            hits.append(km)
    return sorted(set(hits))


def bike_key(maker, model):
    return f"{maker}|{model}"


SIDEBAG_HOLDER_SERIES = "サイドバッグホルダーキット"


def collect_bikes(items, plates, side_codes, sidebags):
    """トップ/サイド用フィッティングキットを車種単位でマージ"""
    bikes = {}
    mount_kits = []   # 「◯◯取付(車種…)」の形のキット（あとで実車種へ振り替える）

    def get_bike(maker, model, group):
        key = bike_key(maker, model)
        if key not in bikes:
            bikes[key] = {"maker": maker, "model": model, "group": group,
                          "top": [], "side": []}
        return bikes[key]

    # トップケース用フィッティングキット
    for row in items:
        if row["メインシリーズ"] != "トップマスターフィッティングキット":
            continue
        if not is_kit_visible(row):
            continue
        cj_code = row["品番"]
        maker = normalize_maker(override_maker(cj_code, row["対応メーカー"]))
        name = row["商品名"]
        if name.startswith(TOPCASE_KIT_PREFIX):
            name = name[len(TOPCASE_KIT_PREFIX):]
        url = product_url(cj_code)
        # キットが対応するベースプレートコード（なしの場合もある: シーシーバー取付プレート付 等）
        kit_plates = [bp.strip() for bp in row["メーカータイプ"].split("_") if bp.strip() in plates]
        spec_models, no_plate = kit_spec_models(row)
        for model_name, group in expand_models(cj_code, name, row["代表適合車種"],
                                               row["対応メーカー"], row["商品名"]):
            if MOUNT_KIT_RE.match(model_name):
                # 車種ではなく取付方法（シーシーバー取付 等）。あとで実車種に振り替える
                mount_kits.append({"maker": maker, "model": model_name, "group": group,
                                   "plates": kit_plates, "url": url, "name": row["商品名"],
                                   "models": spec_models, "noPlate": no_plate})
                continue
            bike = get_bike(maker, model_name, group)
            entry = {"url": url, "name": row["商品名"]}
            if spec_models:
                entry["models"] = spec_models      # 仕様欄の対応モデル（これを正とする）
            if no_plate:
                entry["noPlate"] = True            # ベースプレート不要（キットに直接取付）
            if kit_plates:
                for bp in kit_plates:
                    bike["top"].append({**entry, "plate": bp})
            else:
                bike["top"].append({**entry, "plate": None})

    # サイドケース用フィッティングキット（3P/4P）
    for row in items:
        if row["メインシリーズ"] not in ("3Pシステムフィッティングキット", "4Pシステムフィッティングキット"):
            continue
        if not is_kit_visible(row):
            continue
        cj_code = row["品番"]
        maker = normalize_maker(override_maker(cj_code, row["対応メーカー"]))
        system = "3P" if "3P" in row["メインシリーズ"] else "4P"
        cases = [c for c in row["メーカータイプ"].split("_") if c in side_codes]
        prefix = row["メインシリーズ"] + " "
        item_name = row["商品名"]
        name = item_name[len(prefix):] if item_name.startswith(prefix) else item_name
        for model_name, group in expand_models(cj_code, name, row["代表適合車種"],
                                               row["対応メーカー"], row["商品名"]):
            bike = get_bike(maker, model_name, group)
            bike["side"].append({
                "system": system,
                "url": product_url(cj_code),
                "name": row["商品名"],
                "cases": cases,
            })

    # サイドバッグホルダーキット（E48/SW42/SL58 等のソフトバッグ用ブラケット）
    # NOTE: 1件だけ「トップマスター取付 ※要適合確認」という複数メーカー・複数車種を
    #       【YAMAHA】【HONDA】...のセクション見出しでまとめた特殊行があり、
    #       クリックシステムと同様に1行=1車種の前提が崩れるため対象外にする。
    for row in items:
        if row["メインシリーズ"] != SIDEBAG_HOLDER_SERIES:
            continue
        if not is_kit_visible(row):
            continue
        if "【" in row["代表適合車種"]:
            continue
        cases = [c for c in row["メーカータイプ"].split("_") if c in sidebags]
        if not cases:
            continue
        cj_code = row["品番"]
        maker = normalize_maker(override_maker(cj_code, row["対応メーカー"]))
        prefix = row["メインシリーズ"] + " "
        item_name = row["商品名"]
        name = item_name[len(prefix):] if item_name.startswith(prefix) else item_name
        for model_name, group in expand_models(cj_code, name, row["代表適合車種"],
                                               row["対応メーカー"], row["商品名"]):
            bike = get_bike(maker, model_name, group)
            bike["side"].append({
                "system": "サイドバッグホルダー",
                "url": product_url(cj_code),
                "name": row["商品名"],
                "cases": cases,
            })

    # SRバッグフィッティングキット（E48SR/SR38 等、カフェレーサー系サイドバッグ用ブラケット）
    # shad.es の "Specific SR side bag holder" に相当。サイドバッグホルダーキットとは
    # 別系統（対応バッグが異なる）だが、車種への紐付け方は同じ1行=1メーカー+1車種。
    for row in items:
        if row["メインシリーズ"] != "SRバッグフィッティングキット":
            continue
        if not is_kit_visible(row):
            continue
        cases = [c for c in row["メーカータイプ"].split("_") if c in sidebags]
        if not cases:
            continue
        cj_code = row["品番"]
        maker = normalize_maker(override_maker(cj_code, row["対応メーカー"]))
        prefix = row["メインシリーズ"] + " "
        item_name = row["商品名"]
        name = item_name[len(prefix):] if item_name.startswith(prefix) else item_name
        for model_name, group in expand_models(cj_code, name, row["代表適合車種"],
                                               row["対応メーカー"], row["商品名"]):
            bike = get_bike(maker, model_name, group)
            bike["side"].append({
                "system": "サイドバッグホルダーSR",
                "url": product_url(cj_code),
                "name": row["商品名"],
                "cases": cases,
            })

    # 「◯◯取付(車種…)」のキットを、実在する車種へ振り替える
    #   例: シーシーバー取付(レブル250/500/1100/エリミネーター/バルカンS)
    #       → レブル250/500(17-26) / レブル1100/CMX1100(21-26) /
    #         エリミネーター/SE(24-26) / バルカンS(15-25) の各車種に
    #         「シーシーバー装着車用のトップマスターキット」として追加する
    known = [b["model"] for b in bikes.values()]
    unmatched = []
    for mk in mount_kits:
        targets = remap_mount_kit(mk["model"], known) or []
        if not targets:
            unmatched.append(mk["model"])
            continue
        for model_name in targets:
            for b in bikes.values():
                if b["model"] != model_name:
                    continue
                entry = {"url": mk["url"], "name": mk["name"]}
                if mk.get("models"):
                    entry["models"] = mk["models"]
                if mk.get("noPlate"):
                    entry["noPlate"] = True
                if mk["plates"]:
                    for bp in mk["plates"]:
                        b["top"].append({**entry, "plate": bp})
                else:
                    b["top"].append({**entry, "plate": None})
    if unmatched:
        print("  ※ 実車種に振り替えできなかった取付キット: %s" % " / ".join(sorted(set(unmatched))))

    result = sorted(bikes.values(), key=lambda b: (b["maker"], b["model"]))
    for b in result:
        b["side"].sort(key=lambda s: s["system"])
        # 同じキット・同じプレートの重複を除く
        seen, uniq = set(), []
        for t in b["top"]:
            k = (t.get("plate"), t.get("url"))
            if k in seen:
                continue
            seen.add(k)
            uniq.append(t)
        b["top"] = uniq
    return result


def main():
    items = load_items()

    plates, cj_to_plate, code_plates = read_plates(items)
    attach_topcases(items, plates, cj_to_plate, code_plates)

    side_codes = collect_side_codes(items)
    sidecases = read_case_products_by_category(items, "パニア・サイドケース・サイドボックス")
    sidebags = read_case_products_by_category(items, "サイドバッグ")

    tankbags = read_tankbag_products(items)
    clicksystem_kits = read_clicksystem_kits(items)

    bikes = collect_bikes(items, plates, side_codes, sidebags)

    output = {"plates": plates, "sidecases": sidecases, "tankbags": tankbags,
              "sidebags": sidebags, "clicksystem_kits": clicksystem_kits, "bikes": bikes}
    out_path = os.path.join(DIST_DIR, "reverse_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    both = sum(1 for b in bikes if b["top"] and b["side"])
    sidebag_sku_count = sum(len(skus) for skus in sidebags.values())
    print(f"車種 {len(bikes)} 件（トップ+サイド両対応 {both} 件）、"
          f"タンクバッグ {len(tankbags)} 件、サイドバッグ {sidebag_sku_count} 件 → dist/reverse_data.json")

    src = os.path.join(TEMPLATES_DIR, "model_search.html")
    if os.path.exists(src):
        shutil.copy(src, os.path.join(DIST_DIR, "model_search.html"))
        print("templates/model_search.html → dist/model_search.html")


if __name__ == "__main__":
    main()
