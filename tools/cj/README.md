# SHAD × Custom Japan サイト（shad.customjapan.net）

デザイン原本は **`site-cj/`**（「White Studio」テンプレート。SP Connect のフォルダで
作成されていたものを取り込み）。そこへブランドサイト側で整備した実データを流し込んで
`dist/cj/` を生成します。

## ビルド

```bash
python3 tools/fetch_api_prices.py     # 販売価格・在庫をECのAPIから取得
python3 tools/cj/build_site.py        # dist/cj/ を生成
```

ローカル確認：`cj-shop`（http://localhost:8743 ／ dist/cj を配信）

## 何を統合しているか

| 対象 | 元データ | 反映先 |
|---|---|---|
| 商品（45モデル） | `data/catalog/products.json`（マスターCSV由来） | カテゴリ一覧・商品詳細45ページ |
| コピー・特徴 | `data/catalog/cards.json` | カードの説明文・特徴チップ |
| 販売価格・定価・在庫 | `data/ec/api_prices.json`（ECのAPI） | 一覧の価格・詳細の価格/OFF率/在庫 |
| 商品写真 | `assets/img/products/cards/*`（最適化済み）＋ マスターの本国写真（img.customjapan.net） | カード画像・詳細ギャラリー（最大6枚） |
| 映像 | `assets/media/*.mp4` | TOPのHERO（hero_brand.mp4） |
| 仕様 | マスターの容量・重量・寸法・素材・仕様・JAN・メーカー品番 | 詳細の Specifications |
| 適合データ | `data/fitment/*.json`（車種463件・キット突合済み） | `/fitting` の車種検索＋商品詳細の「この商品が装着できる車種」 |

## カテゴリの割り当て

マスターのカテゴリ表記から自動で振り分けます。

| ページ | 件数 | 内容 |
|---|---|---|
| `/top-cases` | 19 | トップケース・リアボックス |
| `/side-cases` | 7 | パニア・サイドケース |
| `/bags` | 17 | タンクバッグ・サイドバッグ・シートバッグ等 |
| `/accessories` | 2 | ハンドルロック・コンフォートシート |
| `/helmets` `/phone` | 0 | **マスターに該当SKUが無い**ため「取扱準備中」の案内を表示 |

## 商品詳細ページ

- URL は `/product/<型番>`（例 `/product/tr55`）。テンプレートの `product.html?id=` 方式は
  静的ページに置き換え済み（SEOと表示速度のため）
- カラー・仕様を選ぶと **価格・在庫・品番・写真・購入リンク**が切り替わります
- 購入は `moto.customjapan.net/i/<品番>`（選択中の品番のページ）

## 適合検索

- `/fitting`：デザインのデモUI（ダミーselect3つ）を実データのファインダーに置き換え。
  メーカー→シリーズ→車種、またはキーワードで検索。結果はカテゴリ・シリーズ・容量で絞り込み可
- 商品詳細：ページ下部に「この商品が装着できる車種」（3段プルダウンで装着判定＋必要キット）
- ロジックは `site/js/fitment.js`（ブランドサイト）から移植した `site-cj/assets/js/fitment.js`。
  変更点は「価格を表示する」「画像パスを /assets に読み替える」の2点のみで、判定ロジックは同一
- 見た目は `site-cj/assets/css/fitment-cj.css`（White Studio のトークンで作り直し）

## 購入導線とAPI

| 項目 | 現状 |
|---|---|
| 価格・在庫 | ECのAPIから取得した値をビルド時に埋め込み（`fetch_api_prices.py`） |
| 購入 | 「公式通販で購入」でECの該当商品ページ（`moto.customjapan.net/i/<品番>`）へ遷移 |
| サイト内カート | **未実装**。ただし技術的には可能（下記） |

ブラウザからAPIを直接呼べることを確認済み：

```
GET  https://api-i.customjapan.net/api/v1/init      → Access-Control-Allow-Origin: https://shad.customjapan.net
POST https://api-e.customjapan.net/api/v1/items     → 同上（credentials 可・Cookie は Domain=customjapan.net）
```

ECのフロントが使っているカートAPIも判明しています（`moto.customjapan.net` のバンドルより）。

| 操作 | エンドポイント |
|---|---|
| カート取得 | `GET /api/v1/cart` |
| カートに追加 | `PUT /api/v1/cart/details` |
| 数量変更 | `PUT /api/v1/cart/details/quantity` |
| 削除 | `POST /api/v1/cart/details/delete` |
| 決済画面 | `moto.customjapan.net/cart/buy` |

**リクエストボディのキー名（品番・数量の指定方法）だけが未確認**です。社内ドキュメントで
確認いただければ、サイト内で「カートに入れる」→ EC の決済画面へ、という流れに変更できます。

## 注意

- 価格・在庫は変動します。**公開前に必ず `fetch_api_prices.py` を実行**してください
- `site-cj/` はデザイン原本です。ビルドは `dist/cj/` に出力し、原本は書き換えません
