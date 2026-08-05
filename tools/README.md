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
  現在：`TR40`（マスター上は廃盤）／`SW80`・`SL18`（マスターに未登録）
  → これらのページは商品データが紐づかないため、定価やカラー選択が表示されません。
  マスターに登録されれば、次回ビルドで自動的に反映されます。
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
