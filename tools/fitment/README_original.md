# SHADブランドサイト商品 適合検索

- SHADは バイク用のトップケース(リアボックス)、サイドケース、タンクバッグ等をもつブランド。
- 当プロジェクトでは、SHADのブランディングサイトに「商品→適合バイク」「バイク→適合商品」の両方向の検索・一覧ページを生成する。
- 競合はGIVI。

## データソース

**`data/ItemList_SHAD.csv`** — SHAD全商品のマスタエクスポート（cp932/Shift_JIS、232列）。すべての生成スクリプトはこの1本のCSVから必要な行をカテゴリ・メインシリーズ列でフィルタして読む。

| 列名 | 内容 |
|---|---|
| `品番` | CJ管理コード（商品ページURLの末尾・画像URLの一部と一致） |
| `商品名` | 商品名（フィッティングキットの場合、先頭にシリーズ名が付く） |
| `カテゴリ名` | 商品カテゴリ（例: `トップケース・リアボックス`、`パニア・サイドケース・サイドボックス`、`サイドバッグ`、`タンクバッグ`、`フィッティングキット・ステー・ベース`） |
| `メインシリーズ` | フィッティングキットの種別（`トップマスターフィッティングキット`／`3Pシステムフィッティングキット`／`4Pシステムフィッティングキット`／`サイドバッグホルダーキット`／`SRバッグフィッティングキット`／`クリックシステム`／`ベースプレート` 等） |
| `対応メーカー` | 適合バイクのメーカー |
| `代表適合車種` | 適合バイクの車種名・年式（`｜`区切りで複数、`[開始年-終了年]`表記） |
| `メーカータイプ` | 対応製品コード（`_`区切りで複数記載。ベースプレートコードやケースコードなど） |
| `メーカー品番` | SHAD純正のプレート/キットコード（例: `D1B29PAR`） |
| `セット内容・付属品` | セット同梱物のテキスト（「品番：XXXX」の記載からベースプレート紐付けを抽出） |
| `一覧非表示`／`Web非表示`／`セット`／`アウトレット`／`CJ廃番` | 可視性フラグ（`"1"`で該当）。すべて`"0"`の行のみ採用 |

可視性判定・URL組み立て・メーカー表記統一は `scripts/itemlist_common.py` に共通化されている（`is_catalog_visible` / `is_kit_visible` / `product_url` / `product_img` / `normalize_maker`）。**廃番（CJ廃番=1）の商品・キットはすべて除外**（badge表示ではなく完全非表示）。

`data/SHAD_モデルグループ.csv` のみ例外で、ItemList由来ではない手動管理の車種グループ上書きマッピング（1行のみ）。

## ビルド

```bash
python3 build.py
```

`scripts/`配下の生成スクリプトを順番に実行し、`dist/`に全ファイルを出力する。個別のスクリプトを直接叩いて部分再生成することも可能（各スクリプトは冪等）。

| # | スクリプト | 出力 | 系統 |
|---|---|---|---|
| 1 | `generate_groups.py` | `model_groups.json` | 順引き |
| 2 | `generate_data.py` | `data.json` | 順引き |
| 3 | `generate_topcase_data.py` | `topcase_{ベースプレートコード}.json` × 5 | 順引き |
| 4 | `generate_sidecase_data.py` | `sidecase_data.json` | 順引き |
| 5 | `generate_pages.py` | `{製品コード}.html` × 23 | 順引き |
| 6 | `generate_reverse_data_from_itemlist.py` | `reverse_data.json`、`model_search.html` | 逆引き |
| 7 | `generate_kit_pages.py` | `fitting_*.html`（一覧5ページ） | 逆引き |
| 8 | `generate_fitting_kits_overview.py` | `fitting_kits.html`（概要ページ） | 逆引き |

---

## 順引き（商品ページ埋め込み用）

**商品ごとに1つのHTMLファイルを生成し、SHADブランドサイトの商品ページに埋め込む。**

例：
- `TR41.html` → TR41 トップケースに装着可能なバイク一覧
- `SH23.html` → SH23 サイドケースに装着可能なバイク一覧

### トップケースの適合ロジック

```
トップケース（例：TR41）
  → 付属ベースプレートを特定（TR41 → D1B40PAR）
  → そのベースプレートに対応するフィッティングキット一覧 = 適合バイク
```

同じベースプレートを使うトップケースは適合データが共通（例：TR41, TR46, SH39… はすべて D1B40PAR）。

ベースプレートコードの解決優先順位（`generate_pages.py`）:
1. セット内容・付属品の「品番：XXXX」から抽出 → ベースプレート単品行で 品番→メーカー品番(SHADコード) 変換
2. ベースプレートのメーカータイプ列を逆引き（TERRA製品等、①の記載がない場合のフォールバック。同一製品コードが複数ベースプレートに対応する場合は先頭一致を採用）

### サイドケースの適合ロジック

```
サイドケース（例：SH23）
  → メーカータイプ に SH23 を含む 3P/4P フィッティングキットを抽出 = 適合バイク
```

### ベースプレートラインナップ（5種）

| メーカー品番 | 名称 | 対応トップケース |
|---|---|---|
| `D1B29PAR` | ベースプレートS | SH26/SH29/SH33/SH34 |
| `D1B40PAR` | ベースプレートM | SH39/SH40/SH40CG/SH44/SH45/SH47/TR41/TR46 |
| `D1B591PA` | ベースプレートL 樹脂製 | TR37/TR48/TR50/TR55/SH48/SH51/SH58X/SH59X |
| `D1BTRPA2` | アルミ製ベースプレートL ブラック | TR37/TR48/TR50/TR55/SH48/SH51/SH58X/SH59X |
| `D1BTRPA` | アルミ製ベースプレートL アルミ | TR37/TR48/TR50/TR55/SH48/SH51/SH58X/SH59X |

D1BTRPA/D1BTRPA2はTERRA製品向けの色違い（黒/アルミ）で対応トップケースは同一。TERRA製品（TR37/TR48/TR55等）はセット内容・付属品にベースプレート記載がないため、メーカータイプ逆引きで（ItemList内の行順で先頭一致した）どちらかが割り当てられる。

### 生成済みHTMLファイル

**トップケース（19ファイル）**: SH26, SH29, SH33, SH34, SH39, SH40, SH40CG, SH44, SH45, SH47, SH48, SH51, SH58X, SH59X, TR37, TR41, TR46, TR48, TR55

**サイドケース（4ファイル）**: SH23, SH35, SH36, SH38X

### ファイル構成

| ファイル | 役割 |
|---|---|
| `templates/baseplateS.html` | トップケース商品ページのテンプレート（`generate_pages.py`が参照） |
| `templates/sidecaseS.html` | サイドケース商品ページのテンプレート（`generate_pages.py`が参照） |
| `dist/data.json` | D1B40PAR全件データ（`baseplateS.html`のデフォルトfetch先。個別商品ページでは`topcase_{コード}.json`に差し替えられる） |

---

## 逆引き（`dist/model_search.html`）

車種から適合する商品（トップケース・サイドケース・サイドバッグ・タンクバッグ）を検索するページ。

### reverse_data.json 構造

| キー | 内容 |
|---|---|
| `plates` | ベースプレートコード → `{name, url, img, topcases: [{name, url, img, included}]}`（`included`=付属/別売） |
| `sidecases` | サイドケースコード → `[{name, url, img}]`（カテゴリ=`パニア・サイドケース・サイドボックス`、ハードケース） |
| `sidebags` | サイドバッグコード → `[{name, url, img}]`（カテゴリ=`サイドバッグ`、ソフトバッグ） |
| `tankbags` | `[{name, url, img}]`（車種フィッティングと非連動の全SKU一覧） |
| `clicksystem_kits` | `[{name, url, maker, models, cases}]`（参照用のみ、車種紐付けなし） |
| `bikes` | `[{maker, model, group, top: [{plate, url, name}], side: [{system, url, name, cases}]}]` |

`sidecases`/`sidebags`はカテゴリで分けて表示するが、キットの`cases`列（対応コード一覧）はハード/ソフトを区別しないため、車種別フィッティング結果を組み立てる側（`model_search.html`のJS）は両方の辞書を合わせて引く。サムネイルURLは`https://img.customjapan.net/items/{品番}_1.jpg`。

### bikes[].side の system 種別

| system | 由来（メインシリーズ） | 備考 |
|---|---|---|
| `3P` / `4P` | `3Pシステムフィッティングキット` / `4Pシステムフィッティングキット` | ハード/ソフトケース共通 |
| `サイドバッグホルダー` | `サイドバッグホルダーキット` | E48/SW42/SL58 用（shad.esの"SE specific"相当） |
| `サイドバッグホルダーSR` | `SRバッグフィッティングキット` | E48SR/SR38 用、カフェレーサー系（shad.esの"Specific SR"相当） |

### 車種別マッチングの対象外にしているもの

以下は「1行=1メーカー+1車種」という前提が成り立たず、自動マッチングは誤適合のリスクが高いため、車種フィッティングには組み込んでいない（`reverse_data.json`には参照用データのみ、または完全除外）。

- **クリックシステム（タンクバッグ用）**: 1キットが複数メーカー・複数車種にまたがる複合表記（代表適合車種／対応メーカーとも複数値）。`clicksystem_kits`に生データのまま保持し、`fitting_clicksystem.html`で参考表示のみ。
- **ユニバーサルサイドバッグホルダー（D0SS5SE）**: 「トップマスター取付 ※要適合確認」という、複数メーカー・複数車種を【YAMAHA】【HONDA】...のセクション見出しでまとめた特殊行1件。`fitting_kits.html`から商品ページへ直接リンクするのみ。

### fitting_*.html（フィッティングキット一覧ページ）

`model_search.html`の各セクション見出しから遷移する、写真なし・表形式の一覧ページ（`generate_kit_pages.py`）。

| ファイル | 内容 |
|---|---|
| `fitting_baseplates.html` | ベースプレート単位。対応トップケース・対応車種一覧 |
| `fitting_topcases.html` | トップマスターフィッティングキット単位。対応車種（メーカー優先順: ホンダ→ヤマハ→スズキ→カワサキ→アルファベット順）・対応ベースプレート |
| `fitting_sidekits.html` | 車種単位。3P/4Pキットの有無をバッジ表示（クリックでキット商品ページへ） |
| `fitting_sidebagholders.html` | サイドバッグホルダーキット単位（SE系＋SR系）。対応車種・対応サイドバッグコード |
| `fitting_clicksystem.html` | クリックシステムキット単位。対応メーカー・適合車種（生テキスト参考表示）・対応タンクバッグコード |

### fitting_kits.html（フィッティングキット概要ページ）

[shad.es/en/fitting-kits/](https://www.shad.es/en/fitting-kits/) を参考にした、フィッティングキットの種類を写真付きで紹介するランディングページ（`generate_fitting_kits_overview.py`）。トップマスター／3P・4Pシステム／サイドバッグホルダー（SE/ユニバーサル/SR）／クリックシステムの4種を、shad.es本国サイトの実写真（掲載許諾確認済み・ホットリンク）と自社商品データを組み合わせて構成。バックレスト・シーシーバー・SHADロックは未対応（対象外）。

---

## 車種グループの管理

車種一覧はグループ（シリーズ単位）のアコーディオンで表示される。グループ名は `scripts/utils.py` の `get_group()` 関数で決定され、JSON生成時に各レコードの `group` フィールドに格納される（順引き・逆引き両方の生成スクリプトが共通利用）。

### グループルールの追加方法

`scripts/utils.py` の `get_group()` に if 文を追加する。**上から順に評価される**ため、より具体的なルールを先に書く。

```python
def get_group(compatible_models, compatible_maker, item_name, cj_code=""):
    m = compatible_models or ""
    maker = override_maker(cj_code, compatible_maker or "")
    name = item_name or ""

    # ---- ここにルールを追加 ----

    # 例1: 前方一致（LIKE 'PCX%' 相当）
    if m.startswith("PCX") and maker == "ホンダ":
        return "PCX"

    # 例2: 先頭が英字+数字（REGEXP_CONTAINS(r'^MT[0-9]') 相当）
    if re.match(r"^MT[0-9]", m) and maker == "ヤマハ":
        return "MT"

    # 例3: 名称に特定文字列を含む（LIKE '%Africa Twin%' 相当、大文字小文字無視）
    if re.search(r"africa twin", name, re.IGNORECASE):
        return "Africa Twin"

    # ---- フォールバック（変更不要） ----
    ...
```

ルール追加後は `python3 build.py` を実行してJSON・HTMLを再生成する。

### BQ CASE WHEN → Python 変換対応表

| BQ 構文 | Python 構文 |
|---|---|
| `LIKE 'ADV%'` | `m.startswith("ADV")` |
| `LIKE '%Africa Twin%'` | `"Africa Twin" in name` |
| `REGEXP_CONTAINS(r'^CB[0-9]')` | `re.match(r"^CB[0-9]", m)` |
| `REGEXP_CONTAINS(r'(?i)africa twin')` | `re.search(r"africa twin", name, re.IGNORECASE)` |
| `compatible_maker = 'ホンダ'` | `maker == "ホンダ"` |

### 現在定義済みのグループルール

**cj_code 個別指定**（最優先で評価）

| cj_code | グループ名 |
|---|---|
| `29327300` | `400X` |

**モデル名・メーカー条件**

| グループ名 | 条件 |
|---|---|
| `ADV` | 代表適合車種が `ADV` で始まる かつ ホンダ |
| `CB` | 代表適合車種が `CB` + 数字 で始まる かつ ホンダ |
| `CBF` | 代表適合車種が `CBF` + 数字 で始まる かつ ホンダ |
| `CBR` | 代表適合車種が `CBR` + 数字 で始まる かつ ホンダ |
| `Africa Twin` | 商品名に `Africa Twin` を含む（大文字小文字無視） |
| `ホーネット` | 代表適合車種が `ホーネット` で始まる |
| `X-ADV` | 代表適合車種が `X-ADV` で始まる |
| `SH` | 代表適合車種が `SHモード` または `SH MODE` で始まる |
| `FORZA` | 代表適合車種が `フォルツァ` または `FORZA` で始まる |
| `インテグラ` | 代表適合車種が `インテグラ` で始まる |
| `GROM` | 代表適合車種が `MSX` で始まる |
| `XMAX` | 代表適合車種が `X-MAX` で始まる かつ ヤマハ |
| `MT` | 代表適合車種が `MT-` で始まる かつ ヤマハ |
| `DELIGHT` | 代表適合車種が `Delight` または `D'elight` で始まる かつ ヤマハ |
| `MAJESTY` | 代表適合車種が `グランドマジェスティ` または `マジェスティ` で始まる かつ ヤマハ |
| `TRICITY` | 代表適合車種が `トリシティ` で始まる かつ ヤマハ |
| `NEOS` | 代表適合車種が `NEO` で始まる かつ ヤマハ（NEO S / NEO'S / NEOS の表記ゆれ統合） |
| `スカイウェイブ` | 商品名に `スカイウェイブ` を含む かつ スズキ（代表適合車種は輸出名バーグマン始まりのため商品名で判定） |
| `バーグマン` | 代表適合車種が `バーグマン` で始まる かつ スズキ |
| `アドレス` | 代表適合車種が `アドレス` で始まる かつ スズキ |
| `Vストローム` | 代表適合車種が `Vストローム` または `V-ストローム` で始まる かつ スズキ |
| `バンディット` | 代表適合車種が `バンディット` で始まる かつ スズキ |
| `グラディウス` | 代表適合車種が `グラディウス` で始まる かつ スズキ |

**フォールバック**（上記に該当しない場合、順に評価）

| 条件 | グループ名 |
|---|---|
| 先頭が英字 | 先頭の英字部分を大文字化（末尾ハイフン除去: `FZ-1`→`FZ`、`ER-6n`→`ER`） |
| 先頭がカタカナ | カタカナ部分（例: `レブル250`→`レブル`）。`KANA_GROUP` で英語表記グループに統合（`トレーサー`→`TRACER`、`ディバージョン`→`DIVERSION` 等） |
| 先頭が数字 | 数字+英字部分（例: `400X(NC47)`→`400X`） |

---

## メーカー名・車種名の個別補正（`scripts/utils.py`）

### メーカー名の個別上書き（CJ_CODE_MAKER_OVERRIDE）

メーカー名の一括変換（`normalize_maker`）では対応できない個別修正。全生成スクリプト共通。

| cj_code | 変換後 maker | 理由 |
|---|---|---|
| `S0VS12ST` | `スズキ` | KLV1000は日本未販売のため。CSVでは`カワサキ`だが実質スズキVストロームと同一モデル |

### 車種名の分割（CJ_CODE_MODEL_SPLIT）

1つのキットが複数車種を連名表記している場合、別々の車種行として表示する。全生成スクリプト共通。グループは分割後の各車種名から再判定される。

| cj_code | 分割後 |
|---|---|
| `S0BR62ST` | `スカイウェイブ650(02-08)` ／ `バーグマン650 エグゼクティブ(04-24)` |
| `H0VS12ST` | `Dio 110(11-25)` ／ `Vision 110(11-26)` ／ `リード125(22-25)` |

```python
# scripts/utils.py
CJ_CODE_MODEL_SPLIT = {
    "S0BR62ST": ["スカイウェイブ650(02-08)", "バーグマン650 エグゼクティブ(04-24)"],
    "対象のcj_code": ["車種名1", "車種名2", ...],
}
```

---

## ディレクトリ構成

```
data/
  ItemList_SHAD.csv       全商品マスタ（唯一のデータソース、cp932）
  SHAD_モデルグループ.csv   手動管理の車種グループ上書き（1行のみ、ItemList非依存）
scripts/
  itemlist_common.py       ItemList読み込み・可視性判定・URL組み立ての共通ヘルパー
  utils.py                 グループ判定・メーカー/車種名の個別補正
  generate_groups.py       → dist/model_groups.json
  generate_data.py         → dist/data.json
  generate_topcase_data.py → dist/topcase_*.json
  generate_sidecase_data.py→ dist/sidecase_data.json
  generate_pages.py        → dist/{製品コード}.html（順引き23ファイル）
  generate_reverse_data_from_itemlist.py → dist/reverse_data.json, dist/model_search.html
  generate_kit_pages.py    → dist/fitting_{baseplates,topcases,sidekits,sidebagholders,clicksystem}.html
  generate_fitting_kits_overview.py → dist/fitting_kits.html
templates/
  baseplateS.html / sidecaseS.html   順引きページのテンプレート
  model_search.html                  逆引きページ本体
dist/                       ビルド成果物（build.py の出力先）
bak/                        旧CSV5分割パイプライン（ItemList統合により退避、参照専用）
```

`bak/`内のファイルはビルドから参照されない。旧`generate_reverse_data.py`（個別CSV5分割版）と、それが使っていたCSV群（現行スクリプトからも参照されなくなったもの）を退避している。
