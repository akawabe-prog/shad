# カスタムジャパン版（shad.customjapan.net）アップロード手順

ブランドサイト（www.shad-japan.com）とは**別のサイト**として配信します。
原本は同じ `site/` で、販売表示だけを足したものが `dist/cj/` です。

## 1. 価格・在庫を最新化

```bash
python3 tools/fetch_api_prices.py
```

ECのAPIから販売価格・定価・在庫を取得し、`site/data/ec/api_prices.json` を更新します。
**価格と在庫は変動するため、公開前と定期的（できれば毎日）に実行してください。**

## 2. ビルド

```bash
python3 tools/build_cj_site.py
```

`dist/cj/` が作られます。ブランドサイト（`site/` と `dist/shad/`）は変更されません。

## 3. アップロード

`dist/cj/` の中身を **shad.customjapan.net のドキュメントルート直下**に配置します。
`index.html` がトップ（https://shad.customjapan.net/）になります。

## ブランドサイトとの違い

| 項目 | ブランドサイト（shad-japan.com） | カスタムジャパン版（shad.customjapan.net） |
|---|---|---|
| 価格 | 定価（税込）のみ | **販売価格（税込）＋定価＋割引率** |
| 在庫 | 表示なし | **◯在庫あり／△残りわずか／取寄 など** |
| 購入 | 商品ページ下部に1つだけ導線 | **各商品に購入ボタン**（品番ごとにECの該当ページへ） |
| 一覧 | 価格なし | **カードに販売価格**（定価は打ち消し） |
| ヘッダー | カートなし | カートアイコン（EC） |
| フッター | — | ご利用ガイド・送料・返品への導線 |

## 購入導線について（要確認）

現在は「購入する」を押すと **ECの該当商品ページ**（`moto.customjapan.net/i/<品番>`）が開きます。
サイト内で直接カートに入れるURL仕様（例 `?add_cart=品番`）があれば、
`site/js/cj_shop.js` の先頭 `ITEM_URL` を差し替えるだけで全ページに反映されます。

ヘッダーのカートは暫定で `moto.customjapan.net/cart` を指しています。正しいURLをご指定ください。
