# SHAD JAPAN 本番アップロード手順（www.shad-japan.com）

## 1. アップロードするもの

アップロード対象は **`dist/shad/` フォルダの中身すべて**です。
（`site/` が編集用のソース。`dist/shad/` は不要ファイルを除外した本番用コピーで、内容は同一です）

`dist/shad/` の中身を、**www.shad-japan.com のドキュメントルート直下**にそのまま配置してください。
`index.html` がトップ（https://www.shad-japan.com/）になります。

### フォルダ構成（この階層のまま維持）

```
（ドキュメントルート）/
├── index.html ほか *.html（全45ページ）
├── contact.php            ← お問い合わせ送信処理（PHP）
├── stores.json / products_data.json
├── css/                   ← custom.css
├── js/                    ← main.js, fitment.js, purchase.js ほか
├── img/                   ← 画像（約55MB）
├── media/                 ← 動画 mp4（約199MB）
├── docs/                  ← 製品ユーザーガイドPDF（約42MB）
└── data/                  ← 適合検索・EC価格データ（JSON）
```

### フォルダごとアップロードする場合の順番（推奨）

1. `css/` `js/` `data/`（軽量・先に）
2. `img/` `docs/` `media/`（大容量。時間がかかります）
3. ルートの `*.html` `*.php` `*.json`（最後に一括）

※ 相対パスのみ使用しているため、この構成を崩さなければサブディレクトリ配置でも動作します。

## 2. お問い合わせフォーム（API＝メール送信）について

eXs（exs.customjapan.net）の `contact.php` と同じ方式で実装しています。

- 送信フロー: `contact.html` →（POST）→ `contact.php` → 成功 `thanks.html` / 失敗・不備 `form-error.html`
- 送信先: **info@customjapan.jp**
- 差出人: `From: noreply@shad-japan.com`（Reply-To は入力メールアドレス）
- 件名: `【SHAD JAPAN】お問い合わせ（種別）`
- スパム対策: ハニーポット（非表示の `website` 欄）＋サーバー側バリデーション
- 送信前にJavaScriptでも入力チェック（未入力は送信されません）

### 必要なサーバー要件
- **PHP が動作すること**（`mail()` または `mb_send_mail()` が利用可能）。eXs と同じサーバー方式であれば問題ありません。
- 送信ドメイン `shad-japan.com` からの `noreply@` 差出人が SPF 等で許可されていること（eXs の `noreply@exs.customjapan.net` と同様の設定）。

> ローカルの静的プレビューでは PHP は動作しません。実際の送信テストは本番（またはPHPが動くステージング）で行ってください。

## 3. 外部読み込み（CDN）
以下はインターネット経由で読み込みます（本番で追加設定は不要）:
Tailwind CSS / Tabler Icons / Google Fonts / GSAP / Leaflet・OSM（店舗地図）。

## 4. 差し替え推奨（任意）
- フッターのSNSリンク（Instagram / Facebook / YouTube）が現在 `#`。公式アカウントURLに差し替え。
- カートアイコンのリンク（現在 `#`）。EC導線に合わせて設定。
- 特商法・会社情報の「設立・資本金」等、未記載項目があれば追記可能。

## 5. ソース更新後に本番フォルダを作り直すコマンド
`site/` を編集したら、以下で `dist/shad/` を再生成できます。

```bash
cd /Users/cjmac002/Desktop/RIDEOUT_MEDIA/SHAD_ReBranding
find site -name ".DS_Store" -delete
rsync -a --delete --exclude='.DS_Store' --exclude='.git' --exclude='*.map' site/ dist/shad/
```
