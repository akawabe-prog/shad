# 商品データの更新手順

SHAD JAPAN サイトの商品データは、**商品マスター CSV 1本**から自動生成しています。
CSV を差し替えて 1コマンド実行するだけで、サイト全体の商品情報が更新されます。

---

## 更新のやり方（3ステップ）

### 1. 新しい CSV を上書きコピー

```
SHAD_ReBranding/data-source/ItemList_SHAD.csv   ← ここに上書き
```

※ ファイル名は `ItemList_SHAD.csv` のまま（変えると認識されません）
※ 文字コードは Shift_JIS（cp932）のままでOK。EC からのエクスポートそのままで使えます

### 2. ビルドを実行

```bash
python3 tools/build_catalog.py
```

実行すると、件数と除外の内訳がレポートされます。

### 3. 生成された JSON をアップロード

```
site/data/catalog/   ← このフォルダを本番へアップロード
```

本番フォルダ `dist/shad/` に反映する場合は、あわせて同期してください。

```bash
rsync -a --delete --exclude='.DS_Store' site/ dist/shad/
```

> **HTML は書き換わりません。** JSON だけが更新されるので、デザインやページ構成には影響しません。
> 何度実行しても同じ結果になります（冪等）。

### 4. 一覧カードの表示情報を共有JSONに反映

商品一覧（`site/products.html` の `var PRODUCTS`）が持つ型番・容量・カテゴリ名・
キャッチコピー・特徴アイコンは、適合検索の結果ページ（`/fitment`）のカードでも
同じ内容を表示しています。**キャッチコピーや特徴を直したら**、次を実行して
共有JSONを更新してください。

```bash
python3 tools/build_cards_json.py     # → site/data/catalog/cards.json
```

原本は `products.html` の1か所だけなので、両ページで表示がずれることはありません。

---

## シンプル版トップページ

`site/index.html` を原本に、セクションを絞った簡易版トップを作ります。
デザインもマークアップも本体と同じものを使い回すので、本体を直したら
作り直すだけで揃います（NEWSを更新したときは `build_news.py` が自動で回します）。

```bash
python3 tools/build_top_simple.py     # → site/top-simple.html（/top-simple）
```

| | 本体トップ | シンプル版 |
|---|---|---|
| HERO / 新商品 / 車種から探す | ○ | ○ |
| カテゴリから探す | 5枚（フィッティング含む） | **4枚を大きく配置** |
| NEWS | ページ下部 | **カテゴリから探すの直後** |
| Shad on the Road（リール） | ○ | ○ |
| SHADカタログ（PDF） | — | **追加** |
| SHAD Technology／鍵がなくても〜／なぜ純正に選ぶのか／買ってからも〜／映像で知る | ○ | **削除** |

カタログ枠は**本国サイト（www.shad-japan.com）下部のデザインを踏襲**しています。
45°ストライプの帯（`.ptn-stripe45`）の中に、左＝カタログの見開き画像、
右＝赤いPDFボタンを縦に並べる構成です。

PDFは `site/docs/catalog/`、画像は `site/img/catalog/`（PDF1ページ目＝見開きをwebp化）。
年度を足すときは `build_top_simple.py` の `CATALOGS` の先頭に追記してください
（画像は先頭＝最新年度のものを使い、ファイルサイズはビルド時に自動表示します）。

本体トップと内容が重なるため `noindex` を入れています。正式公開するときは外してください。

---

## FAQ の更新（商品ページ）

FAQの原本は**CJのAPI**です。取得してJSONに落とし、商品ページへ書き出す2段構成です。

```bash
python3 tools/fetch_faq.py     # API → site/data/faq/faq.json
python3 tools/build_faq.py     # JSON → 商品ページ48枚のFAQセクション
```

| 段階 | 内容 |
|---|---|
| `fetch_faq.py` | `GET https://api-f.customjapan.net/api/v1/faq?slug=shad`。他のCJ APIと同じく先に `init` でセッションを取る。`<span style>` を外し、EC・旧サイトへのリンクを自サイトのパスへ読み替える |
| `build_faq.py` | 各商品ページの `<!-- FAQ:START -->`〜`<!-- FAQ:END -->` を差し替え（冪等）。`details/summary` のアコーディオン＋構造化データ（FAQPage） |

### リアルタイム取得（site/js/faq.js）

2026/08/14 に CJ側で `https://www.shad-japan.com` が許可オリジンに追加され、
**セッション無し**で取得できるようになりました（Cookie不要／プリフライトも通過）。
`site/js/faq.js` が本番ドメインでだけAPIを叩き、取得できた内容に差し替えます。

| オリジン | APIの応答 | faq.js の挙動 |
|---|---|---|
| `https://www.shad-japan.com` | 200（Cookie不要） | APIの最新内容に差し替え |
| `https://shad-japan.com`（www無し） | **403** | 静的FAQのまま |
| localhost / GitHub Pages | 403 | リクエストを送らない（静的FAQのまま） |

許可は www 付きの1オリジンだけなので、`location.hostname` で判定しています。
**www無しでもサイトが見える場合は、www へリダイレクトするか、CJ側で apex も
許可してもらう必要があります。**

静的HTML（`build_faq.py` の出力）は常に残します。検索エンジン向けの構造化データ
（FAQPage）と、JS無効時・API障害時の表示を守るためです。取得に失敗しても
静的FAQがそのまま表示され、コンソールにエラーは出ません。

確認用に `window.SHAD_FAQ_LIVE = true / false` で強制切り替えできます。

### どのFAQがどの商品ページに出るか

| グループ | 条件 | 例 |
|---|---|---|
| この商品について | FAQの `relItems` / `slug`（`shad-<型番>`）がその型番を指す | SH40・SH40CG に「SH40とSH40CARGOの違い」 |
| `<カテゴリ>`について | FAQの分類（`classS`）が商品の種類名に含まれる | 「トップケース」→ トップケース系17モデル |
| SHADについて | 分類が「全般」 | 全48ページ共通（保証・鍵・修理・防水 など） |

現在のAPIの中身は **全般10件＋トップケース7件＋商品別1件**。サイド・バッグ系の分類が
増えれば、`fetch_faq.py` → `build_faq.py` を回すだけでそのカテゴリのページに出ます。

### サイト全体のFAQページ（/faq）

2026/08/18 に**APIへ一本化**しました。手書きの設問は廃止し、`build_faq.py` が
`site/faq.html` のマーカー間（`<!-- FAQ:CHIPS:START -->` / `<!-- FAQ:BODY:START -->`）を
書き換えます。ページのデザイン（カテゴリ見出し・チップ・アコーディオン）は従来のままです。

APIの分類・タグを、ページ内のカテゴリへ振り分けています（`TAG_TO_CAT` / `ID_TO_CAT`）。

| ページ内カテゴリ | 振り分け元のタグ | 現在の件数 |
|---|---|---|
| 適合・取り付け | `取付` | 6 |
| 製品について | `雨・防水` `操作・仕様` `規格・仕様*` ＋タグ無し | 5 |
| 購入・お届け | `注文・返品*` | 1 |
| 保証・修理 | `保証・アフターサービス` `修理・補修` `カギ` | 4 |
| 店舗・SHAD BASE | （ID指定） | 1 |

設問が0件のカテゴリは、チップごと出しません（現在「返品・交換」が該当）。
CJ側でタグが増えたら `TAG_TO_CAT` に1行足すだけで振り分けられます。

**一本化で消えた設問**（APIに同等のものが無い13問）は
`data-source/faq_legacy/FAQ追加依頼.md` にまとめてあります。CJさんに登録いただければ
`fetch_faq.py` → `build_faq.py` を回すだけでページに戻ります。
手書き版のHTMLも `data-source/faq_legacy/` に保管しています。

---

## NEWS の更新

記事は `site/data/news/news.json` の1ファイルにまとめています。**JSONを編集して
ビルドするだけ**で、一覧・詳細・TOPページの最新4件がまとめて更新されます。

```bash
python3 tools/build_news.py
```

| 生成されるもの | URL |
|---|---|
| `site/news/index.html` | `/news`（カテゴリで絞り込み） |
| `site/news/<slug>.html` | `/news/<slug>`（詳細） |
| `site/index.html` の NEWS 枠 | 最新4件のカード（`<!-- NEWS:START -->`〜`<!-- NEWS:END -->` を差し替え） |

### 記事の書き方（news.json）

```json
{
  "slug": "tr41-order-resume",          ← URLになる英数字（重複させない）
  "date": "2026-06-10",                 ← 表示は 2026.06.10。並び順もこれが基準
  "category": "News",                   ← categories に無い値は絞り込みに出ません
  "title": "TERRA TR41 受注を再開しました",
  "lead": "一覧とOGPに出る1〜2文",
  "image": "/img/news_1.webp",          ← 空ならグレーのプレースホルダー
  "draft": true,                        ← true = 「本文は準備中です」の案内を表示
  "body": [
    {"type": "h",     "text": "見出し"},
    {"type": "p",     "text": "段落。改行は \\n"},
    {"type": "ul",    "items": ["箇条書き1", "箇条書き2"]},
    {"type": "img",   "src": "/img/news/xxx.webp", "caption": "写真の説明"},
    {"type": "quote", "text": "引用・コメント"},
    {"type": "link",  "items": [
       {"href": "/product/tr27", "text": "商品ページ", "primary": true},
       {"href": "https://prtimes.jp/...", "text": "プレスリリース"}
    ]}
  ],
  "products": ["TR41"]                  ← 記事下の「関連商品」（型番／任意）
}
```

- **本文が用意できていない記事**は `body: []` ＋ `draft: true` にしておけば、
  リンク切れを作らずに公開できます（詳細ページに「準備中」の案内が出ます）。
  本文を入れたら `draft` を `false` に変えてください
- `link` ブロックは記事下部の導線ボタン。`primary: true` が赤ボタン、
  `/` 始まり以外（外部URL）は自動で別タブ＋外部リンクアイコンになります
- 画像は `site/img/news/` に置き、WEBP に最適化してから参照してください
  （ヒーローは16:9、本文中は4:3が収まりよく、幅1200〜1600pxで十分です）
- 記事を消すときは JSON から該当ブロックを削除してビルド（古いHTMLも消えます）

---

## 除外ルール

以下は自動的に除外されます（`tools/build_catalog.py` 冒頭で変更可能）。

| ルール | 内容 |
|---|---|
| `CJ廃番 = 1` | 廃盤商品を除外 |
| `セット = 1` | セット商品を除外 |
| 品番が `YY` / `ZZ` 始まり | 社内用品番を除外 |

さらに、型番で始まっていても以下は「本体商品」ではなく**アクセサリー・補修パーツ**に分類されます。

- 商品名に `フィッティングキット` `バックレスト` `カラーパネル` `ロックカバー` `インナーバッグ` `キーシリンダー` `ベースプレート` `テールランプ` などを含むもの
- 商品名が `型番＋専用○○` の形のもの（例：`SH38X専用 インナーメッシュ`）

---

## 生成されるファイル

| ファイル | 内容 |
|---|---|
| `products.json` | 本体商品。製品コード（TR41 等）ごとに、**カラー／仕様バリエーションを品番単位でまとめたもの**。定価・画像・スペックを含む |
| `fitting.json` | フィッティングキット（トップマスター／3P／4P／サイドバッグホルダー／SR） |
| `accessories.json` | アクセサリー・補修パーツ。`forCodes` に対応する本体型番が入る |
| `accessory_index.json` | 製品コード → 対応アクセサリー品番の索引（商品詳細ページで「対応パーツ」を出すため） |
| `others.json` | 上記に当てはまらないもの（店舗用品など） |
| `meta.json` | 生成日時・件数・除外統計。**更新できたかの確認に使えます** |

---

## 更新できたかの確認

`site/data/catalog/meta.json` を開くと、生成日時と件数が入っています。

```json
{
 "generatedAt": "2026-07-29T...",
 "totalRows": 1824,
 "kept": 901,
 "excluded": { "セット商品": 185, "廃盤(CJ廃番)": 736, "社内用品番(YY/ZZ)": 2 },
 "counts": { "products": 23, "productVariants": 50, "fitting": 674, ... }
}
```

---

## 注意点・既知の状況

- **マスターに存在しない製品ページ**があるとビルド時に警告が出ます。
  現在：`TR40`（マスター上は廃盤）
  → 商品データが紐づかないため、定価やカラー選択が表示されません。
  マスターに登録されれば、次回ビルドで自動的に反映されます。
- `SL18`・`SW80` はマスター未登録かつEC本体SKUも無いため**非公開**にしました（2026-08-17）。
  ページ・画像は `data-source/unpublished/` に退避しています（戻し方は同フォルダのREADME）。
- 商品名の付け方が変わると分類ルールに影響する場合があります。
  ビルド後のレポート（本体商品の件数・カラー展開）が想定と違うときはご連絡ください。

---

## 容量（サイズ）をECのAPIから取得する

マスターCSVの「容量」欄は空のことがあり、可変容量モデル（SH38X / SH58X /
SH59X など）は特に記載が抜けています。容量はECのAPIから取得してください。

```bash
python3 tools/fetch_api_sizes.py        # 全モデル
python3 tools/fetch_api_sizes.py SH38X  # モデル指定
python3 tools/build_catalog.py          # 取得した容量を反映
python3 tools/gen_pages_from_catalog.py # 追加ページに反映（既存ページは対象外）
```

`fetch_api_sizes.py` は社内ドキュメントの認証手順に従います。

1. `GET https://api-i.customjapan.net/api/v1/init`（`Cache-Control: no-cache`）
   → `guid` / `authorization` が Cookie に発行される
2. `POST https://api-e.customjapan.net/api/v1/items` に上記Cookieを付けて
   `{"ids":[品番,...]}` を送る

取得結果は `site/data/catalog/api_sizes.json` に保存され、`build_catalog.py` が
容量として取り込みます（見出し＝1個ぶん／左右セットは片側、スペック表＝内訳つき）。

---

## フィッティングキット解説ページ（/fitting-kits）

本国サイト（shad.es/en/fitting-kits）の内容を日本語化し、当サイトのデザインで
再構成した静的ページです（`site/fitting-kits.html`）。

- 画像は本国サイトの公式素材を WEBP 化して `site/img/fitting/` に取り込み（27点・約305KB）
- 数値・品番・対応ケースは、本国の記載と社内マスター（`ItemList_SHAD.csv`）を突合した内容のみ
  掲載しています。ベースプレートの日本語名・定価はマスター（アクセサリー）から取得
- ベースプレートの対応ケースは `site/data/fitment/reverse_data.json` のプレート構成と一致
  （D1B29PAR / D1B40PAR / D1B591PA / D1BTRPA / D1BTRPA2）
- 商品ラインアップやプレート価格が変わったときは、このページの該当箇所を直接修正してください
  （自動生成ではありません）
- ページ構成（ビジュアル主体）：フルブリードHERO（写真）→ **カテゴリー型のページ内ナビ（8タイル）**
  → 装着の流れ（写真の帯に01/02/03）→ トップマスター（帯）→ ベースプレート5種（製品写真）
  → 3P/4P（帯＋比較2枚）→ サイドバッグ（動画の帯＋3タイプ）→ クリックシステム（動画の帯）
  → バックレスト／SHADロック → 適合検索CTA（帯）
- 使用素材：`img/terra/ride2・urban・corner`、`img/expandable/night・gs_full`、
  `media/reel_tr30.mp4`（サイドバッグ）、`media/reel_click.mp4`（クリックシステム）
- タイルは下部セクションへのアンカー。タイルを過ぎると細い追従ナビが現れ、
  いま見ているセクションを赤い下線で示します（スクリプトはページ内に記述）

---

## ヘッダー（全ページ共通）

ヘッダーのHTMLは各ページに実体があります（静的サイトのため）。項目を増減するときは
`site/*.html` `site/product/*.html` `site/news/*.html` の3か所をまとめて置換してください。

- PCメニューは **1024px（`lg:`）以上**で表示。それ未満はハンバーガー。
  項目が6つあるため、768〜1023pxでは2段に折り返してしまうのでこの設定です
- **PRODUCTS のホバーメニュー**（シリーズ2件＋カテゴリ5件のサムネイル）は
  `site/js/nav.js` が生成します。**HTMLの編集は不要**で、掲載内容は nav.js 冒頭の
  `SERIES` / `CATEGORIES` 配列を書き換えるだけで全ページに反映されます
- スタイルは `site/css/custom.css` の `.mega*`。1023px以下では非表示（スマホは
  ハンバーガーメニューを使用）

---

