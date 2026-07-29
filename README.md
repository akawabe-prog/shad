# SHAD ReBranding — ブランディングコマースサイト構想

バイクケースブランド **SHAD（スペイン・NAD S.L.）** の日本向けブランディングコマースサイト立ち上げ＋ SHAD JAPAN 統合プロジェクトの作業フォルダ。
運営主体：株式会社カスタムジャパン（SHAD日本総代理店）。最終更新：2026-06-12。

---

## 📁 成果物

| ファイル | 内容 |
|---|---|
| `SHAD_branding_commerce_proposal.pptx` | 社内共有用 提案書（全12枚・経営/意思決定層向けサマリー） |
| `mockups/top_wireframe.html` | TOPページ全体のワイヤーフレーム（ブラウザで開く） |
| `mockups/story_section.html` | STORYセクション（動画メディア風・横スライダー） |
| `mockups/fitment_finder.html` | 車種適合ファインダー UIモック（動作デモ・デモデータ入り） |
| `site/` | **実装版サイト（HTML/Tailwind/JS）** — `index.html`（TOP）＋`products.html`（製品ショールーム・26モデル）＋`product-*.html`（**全26モデルの詳細ページ**）＋`css/custom.css`＋`js/main.js`＋素材 |
| `site/product-{code}.html` | 各モデルの詳細ページ（画像ギャラリー・容量・カラー展開・説明文・スペック表・関連製品）。`tools/gen_product_pages.py` がExcel＋公式画像から自動生成 |
| `site/products_data.json` | 商品リスト（SHAD_ItemList.xlsx 1,785行）から抽出したモデル単位データ。色違いSKUは1モデルに集約。NEW/FLAGSHIPフラグ付き |
| `tools/gen_product_pages.py` | 詳細ページ＋一覧データのジェネレーター（再実行で再生成） |
| `mockups/top_comp.html` | TOP 高精度デザインカンプ（確定コピーv2＋公式実素材：ヒーロー動画/製品写真/縦リール/公式ロゴ） |
| `mockups/img/` `mockups/media/` | カンプ用に最適化済みのWeb素材（画像リサイズ済・動画は軽量リール厳選） |
| `assets/` | SHAD公式 提供素材一式（約13GB：カタログ/製品写真/動画/ロゴ/CI マニュアル/プレスリリース。配布元 OneDrive zip） |
| `copy_top_v2.md` | **TOPページコピー 最新版**（HERO=A案確定・メリハリ設計） |
| `copy_top_v1.md` | TOPページコピー v1（旧版・参照用） |

> **ファインダーUIの方針**：画面上にはEC要素（カート・価格・購入分岐）を出さない。適合製品＋車種専用フィッティングのセット提示と「製品詳細を見る」まで。購入導線の扱いは戦略資料・裏側設計でのみ管理する。

※ `mockups/*.html` はブラウザでそのまま開けます（アイコンはCDN読込）。

---

## 🎯 戦略の核（一文）

> OEMと特許に裏打ちされた“あなたのバイク専用”のプレミアム・ラゲッジを、車種適合検索を入口に体験させ、取付はディーラー網へ送る — **価格ではなく技術で選ばれるブランドの家**をつくる。

---

## ✅ 確定した方針

| 論点 | 決定 |
|---|---|
| チャネル | **O2Oハイブリッド**（体験・需要創出は新サイト／取付要品は取扱店・SHAD BASEへ送客） |
| 統合方式 | **独立JPサイト（案A）**。本国 shad.es の世界観・適合機能を移植 |
| ポジショニング | **技術プレミアムへ昇華**（価格訴求→OEM/特許/受賞でブランド格・ASP向上） |
| カート/決済 | **shad.customjapan.net**（既存EC基盤）。新サイトはSKUへディープリンクで受け渡し |
| 製品詳細 | **ブランドサイト側に保持（案あ）**。「カートに入れる」のみEC側へ |

---

## 📊 根拠（要点）

- **市場**：世界CAGR 11.6%（2024→2034で約3倍）の急成長・寡占（上位5社で約70%）。
- **SHAD**：GIVI約16%に対し4.7–9.8%の技術ドリブン挑戦者。非対称優位＝①OEM信頼 ②メカニカル特許（Expandable/3P/ダブルロック）③カスタムジャパンB2Bインフラ（ディーラー90%超）。
- **競合の隙**：最大の競合 GIVI 日本サイトは適合検索なし・ブランド物語なし・価格なしの薄いパンフレット。SHADが強い領域がそのまま空白＝逆転の好機。価格非表示・店舗送客は国内ハードラゲッジの標準（O2O判断を裏付け）。

---

## 🧭 サイト構成（2層 + O2O）

```
SHAD ブランドコマースサイト（新規・独立JP）
  ├ ブランド物語 ／ 車種適合ファインダー ／ 製品情報・レビュー
  └「購入」で分岐
       ├ A. 取付不要品 → 直販 → shad.customjapan.net（カート・決済）
       └ B. 取付要品  → 取扱店・SHAD BASE で取付購入
並行：B2Bディーラー卸 customjapan.net（既存・不変）
```

### TOPスクロール導線
HERO動画 → 車種適合ファインダー → 注目製品 → PRODUCT REELS（SNS縦長動画 9:16）→ WHY SHAD（技術プレミアム証明）→ STORY（動画）→ レビュー（Amazon）→ 取扱店・SHAD BASE → NEWS/RACING → フッター

---

## 🎨 デザイン（本国準拠）

- カラー：黒基調 ＋ **SHADレッド `#E31E24`** ＋ 白・グレー
- 見出し：DIN系コンデンス大文字（Dine）／本文：Helvetica Neue Condensed
- トーン：シネマティック・動画主体・「PATENTED」＆受賞バッジ

---

## ⏭ 次のアクション候補

1. ~~車種適合ファインダーのUI高精度モック~~ → 完了（`mockups/fitment_finder.html`）
2. TOPの高精度デザインカンプ化
3. TOPワイヤーの実装HTML/CSS書き起こし
4. モバイル版TOPワイヤー

---

## 参考（一次情報）

- 本国サイト：https://www.shad.es/en/
- 現行JAPAN：https://shad-japan.com/
- 競合：GIVI日本 https://givi-jp.com/ ／ SW-MOTECH(アクティブ) http://www.acv.co.jp/swmotech/ ／ デイトナ https://www.daytona.co.jp/
