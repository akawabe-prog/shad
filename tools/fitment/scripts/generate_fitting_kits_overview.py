"""
「フィッティングキットとは」概要ページ生成

https://www.shad.es/en/fitting-kits/（shad.es/shad_es_fitting.html に保存したスナップ
ショット）を参考にした、フィッティングキットの種類を紹介するランディングページ。
主役は各ケース・バッグそのものではなく、車体と繋ぐ「フィッティングキット（金具）」。
写真・バナーはshad.es本国サイトの実画像をそのまま利用し（掲載許諾確認済み）、
リンク・対応車種データは dist/reverse_data.json（customjapan実商品）を使う。

対象は往復対応済みの4種類（トップマスター／3P・4Pシステム／サイドバッグホルダー
（SE/ユニバーサル/SR）／タンクバッグ・クリックシステム）。バックレスト・シーシー
バー・SHADロックは対象外（未整備のため）。

出力 : dist/fitting_kits.html
"""

import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(ROOT, "dist")

SHAD_ES = "https://www.shad.es/wp-content/uploads"

# shad.es 実写真（許諾確認済み・ホットリンク）
IMG = {
    "nav_topmaster": f"{SHAD_ES}/2022/05/fijaciones-1.jpg",
    "nav_3p": f"{SHAD_ES}/2022/05/fijaciones-2.jpg",
    "nav_4p": f"{SHAD_ES}/2022/05/fijaciones-3.jpg",
    "nav_sidebag": f"{SHAD_ES}/2022/05/fijaciones-4.jpg",
    "nav_tankbag": f"{SHAD_ES}/2023/06/Sin-titulo-1.jpg",
    "banner_topmaster": f"{SHAD_ES}/2022/05/fijaciones-maletas-banner.jpg",
    "banner_sidesystem": f"{SHAD_ES}/2022/05/10-Ducati-Diavel-Perspective.jpg",
    "banner_sidebag": f"{SHAD_ES}/2022/05/fijaciones-bolsas-banner.jpg",
    "banner_tankbag": f"{SHAD_ES}/2023/05/click-system-banner-Home-960x247-1.jpg",
    "logo_3p": f"{SHAD_ES}/2022/05/3p-system-logo.png",
    "logo_4p": f"{SHAD_ES}/2023/06/4p-system-logo.png",
    "rack_small": f"{SHAD_ES}/2023/01/PARRILLA-PEQUEN%CC%83A.jpg",
    "rack_medium": f"{SHAD_ES}/2023/01/PARRILLA-MEDIANA-2.jpg",
    "rack_big": f"{SHAD_ES}/2023/01/PARRILLA-GRANDE-1.jpg",
    "rack_alu_black": f"{SHAD_ES}/2023/01/PARRILLA-ALUMINIO-NEGRO-1.jpg",
    "rack_alu": f"{SHAD_ES}/2023/01/PARRILLA-ALUMINIO-1.jpg",
    "size_s": f"{SHAD_ES}/2022/06/S.png",
    "size_m": f"{SHAD_ES}/2022/05/M.png",
    "size_b": f"{SHAD_ES}/2022/05/B.png",
    "size_a": f"{SHAD_ES}/2022/05/A.png",
    "sidebag_se": f"{SHAD_ES}/2022/05/14-MT09-SBH-SILUETA-sombra70.jpg",
    "sidebag_universal": f"{SHAD_ES}/2022/05/15-Zontes_GI_125_SBH_Universal_sombra70.jpg",
    "sidebag_sr": f"{SHAD_ES}/2022/05/04-Royal_Enfiel_SR_Silueta_sombra70.jpg",
}

# トップマスター用ラック: SHADコード → (shad.es写真, サイズアイコン, 表示名)
RACK_PHOTOS = {
    "D1B29PAR": (IMG["rack_small"], IMG["size_s"], "スモールラック"),
    "D1B40PAR": (IMG["rack_medium"], IMG["size_m"], "ミディアムラック"),
    "D1B591PA": (IMG["rack_big"], IMG["size_b"], "ビッグラック"),
    "D1BTRPA2": (IMG["rack_alu_black"], IMG["size_a"], "ブラックアルミラック"),
    "D1BTRPA": (IMG["rack_alu"], IMG["size_a"], "アルミラック"),
}

# 「トップマスター取付」汎用サイドバッグホルダー(D0SS5SE)は複数メーカー・複数車種の
# 特殊行のため車種紐付けから除外している（generate_reverse_data_from_itemlist.py 参照）。
# 商品ページへは直接リンクする。
UNIVERSAL_HOLDER_URL = "https://moto.customjapan.net/i/13081485"

PAGE_STYLE = """
:root { --accent: #d81f26; --dark: #111; --panel: #17181a; --border: #e2e2e2; }
* { box-sizing: border-box; }
body {
  font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
  max-width: 1160px; margin: 0 auto; padding: 24px 20px 60px; color: #1a1a1a; background: #fff;
}
.brand-bar {
  background: linear-gradient(115deg, var(--dark) 88%, var(--accent) 88.3%, var(--accent) 92%, var(--dark) 92.3%, var(--dark) 94%, var(--accent) 94.3%);
  color: #fff; padding: 20px 28px; margin-bottom: 28px; display: flex; align-items: baseline; gap: 16px; flex-wrap: wrap;
}
.brand-logo { font-weight: 900; font-size: 1.6rem; letter-spacing: 4px; font-style: italic; }
.brand-logo .dot { color: var(--accent); }
.brand-title { font-size: 0.9rem; color: #bbb; letter-spacing: 2px; font-weight: bold; }

.intro h1 { font-size: 1.5rem; margin: 0 0 12px; }
.intro p { font-size: 0.92rem; line-height: 1.9; color: #333; margin: 0 0 12px; }

/* 種類ナビ */
.type-nav { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 24px 0 48px; }
.type-nav a {
  display: block; text-decoration: none; color: var(--dark); border: 1px solid var(--border);
  text-align: center; transition: border-color 0.12s;
}
.type-nav a:hover { border-color: var(--accent); }
.type-nav .thumb { aspect-ratio: 16/10; overflow: hidden; background: #f2f2f2; }
.type-nav .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.type-nav .label { font-size: 0.72rem; font-weight: bold; padding: 8px 4px; letter-spacing: 0.5px; }
.type-nav a:hover .label { color: var(--accent); }

/* 種類ごとのセクション */
.kit-type-section { margin: 0 0 64px; scroll-margin-top: 16px; }
.kit-type-hero { position: relative; margin-bottom: 20px; background: var(--dark); overflow: hidden; }
.kit-type-hero img { width: 100%; display: block; opacity: 0.55; max-height: 260px; object-fit: cover; }
.kit-type-hero h2 {
  position: absolute; left: 26px; bottom: 18px; color: #fff; font-size: 1.4rem;
  font-weight: 800; font-style: italic; margin: 0; letter-spacing: 1px; line-height: 1.3;
}
.kit-type-desc { font-size: 0.88rem; line-height: 1.85; color: #333; margin: 0 0 18px; }
.kit-subhead { font-size: 1rem; font-weight: 800; font-style: italic; margin: 26px 0 10px; color: var(--dark); }
.kit-type-more {
  display: inline-block; font-size: 0.8rem; font-weight: bold; color: #fff; background: var(--accent);
  text-decoration: none; padding: 9px 18px; margin-top: 8px;
}
.kit-type-more:hover { background: var(--dark); }

/* 3P/4P スペックブロック */
.spec-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 8px 0 28px; }
.spec-block { border: 1px solid var(--border); padding: 18px; }
.spec-block img.system-photo { width: 100%; aspect-ratio: 16/10; object-fit: cover; margin-bottom: 12px; }
.spec-block .logo { height: 40px; margin-bottom: 10px; }
.spec-block h3 { font-size: 1rem; font-weight: 800; margin: 0 0 8px; }
.spec-block p { font-size: 0.85rem; line-height: 1.8; color: #333; margin: 0 0 10px; }
.spec-table { width: 100%; font-size: 0.8rem; border-collapse: collapse; margin-top: 10px; }
.spec-table th { text-align: left; color: #888; font-weight: bold; padding: 6px 8px 6px 0; white-space: nowrap; vertical-align: top; width: 30%; }
.spec-table td { padding: 6px 0; color: #333; }
.spec-note { font-size: 0.78rem; color: var(--accent); margin-top: 8px; }
@media (max-width: 700px) { .spec-columns { grid-template-columns: 1fr; } }

/* サイドバッグホルダー 3タイプカード */
.holder-columns { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin: 8px 0 28px; }
.holder-card { border: 1px solid var(--border); }
.holder-card img { width: 100%; aspect-ratio: 3/2; object-fit: cover; display: block; }
.holder-card .body { padding: 14px 16px; }
.holder-card h3 { font-size: 0.92rem; font-weight: 800; margin: 0 0 4px; }
.holder-card .code { font-size: 0.72rem; color: #999; margin: 0 0 8px; }
.holder-card p { font-size: 0.8rem; line-height: 1.7; color: #333; margin: 0 0 8px; }
.holder-card .compat { font-size: 0.78rem; color: var(--dark); }
.holder-card .compat b { color: var(--accent); }
.holder-card a.holder-link { display: block; font-size: 0.78rem; font-weight: bold; color: var(--accent); text-decoration: none; margin-top: 6px; }
.holder-card a.holder-link:hover { text-decoration: underline; }
@media (max-width: 700px) { .holder-columns { grid-template-columns: 1fr; } }

/* ラック（トップマスター）グリッド */
.rack-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin: 14px 0 22px; }
.rack-card { border: 1px solid var(--border); text-decoration: none; color: inherit; display: block; }
.rack-card img.rack-photo { width: 100%; aspect-ratio: 4/3; object-fit: cover; display: block; }
.rack-card .body { padding: 10px 12px 14px; }
.rack-card .size-icon { height: 16px; margin-bottom: 6px; }
.rack-card h4 { font-size: 0.82rem; font-weight: 800; margin: 0 0 2px; }
.rack-card .code { font-size: 0.72rem; color: #999; margin: 0 0 6px; }
.rack-card .compat { font-size: 0.72rem; color: #666; line-height: 1.6; }
.rack-card:hover { border-color: var(--accent); }
.rack-card:hover h4 { color: var(--accent); }

/* 商品カードグリッド（model_search.html と共通デザイン） */
.product-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 14px; margin: 14px 0 18px;
}
.product-card { border: 1px solid var(--border); background: #fff; display: flex; flex-direction: column;
  transition: box-shadow 0.12s, transform 0.12s, border-color 0.12s; }
.product-card:hover { border-color: var(--dark); box-shadow: 5px 5px 0 var(--dark); transform: translate(-2px, -2px); }
.card-link { text-decoration: none; color: inherit; display: block; }
.card-thumb { aspect-ratio: 1; background: #fff; display: flex; align-items: center; justify-content: center;
  border-bottom: 1px solid #f0f0f0; padding: 8px; }
.card-thumb img { width: 100%; height: 100%; object-fit: contain; }
.card-thumb.noimg img { display: none; }
.card-thumb.noimg::after { content: 'NO IMAGE'; color: #ccc; font-size: 0.75rem; }
.card-name { font-size: 0.8rem; font-weight: bold; padding: 10px 12px 4px; color: var(--dark); line-height: 1.5; }
.card-link:hover .card-name { color: var(--accent); }
.card-goto { font-size: 0.7rem; font-weight: bold; color: #aaa; padding: 0 12px 10px; letter-spacing: 1px; }
.card-link:hover .card-goto { color: var(--accent); }

@media (max-width: 600px) {
  .type-nav { grid-template-columns: repeat(3, 1fr); }
  .product-grid, .rack-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
}
"""


def load_reverse_data():
    with open(os.path.join(DIST_DIR, "reverse_data.json"), encoding="utf-8") as f:
        return json.load(f)


def product_card(name, url, img):
    return f"""<div class="product-card">
  <a class="card-link" href="{html.escape(url)}" target="_blank">
    <div class="card-thumb"><img src="{html.escape(img)}" loading="lazy" alt="{html.escape(name)}"
      onerror="this.parentElement.classList.add('noimg')"></div>
    <div class="card-name">{html.escape(name)}</div>
    <div class="card-goto">詳細を見る ›</div>
  </a>
</div>"""


def product_grid(items):
    cards = "\n".join(product_card(i["name"], i["url"], i["img"]) for i in items)
    return f'<div class="product-grid">\n{cards}\n</div>'


def rack_card(code, plate):
    photo, size_icon, label = RACK_PHOTOS.get(code, (plate["img"], None, plate["name"]))
    size_img = f'<img class="size-icon" src="{html.escape(size_icon)}" alt="">' if size_icon else ""
    return f"""<a class="rack-card" href="{html.escape(plate['url'])}" target="_blank">
  <img class="rack-photo" src="{html.escape(photo)}" loading="lazy" alt="{html.escape(label)}">
  <div class="body">
    {size_img}
    <h4>{html.escape(label)}</h4>
    <div class="code">{html.escape(code)}</div>
    <div class="compat">{html.escape(plate['name'])}</div>
  </div>
</a>"""


def rack_grid(plates_dict):
    order = list(RACK_PHOTOS.keys())
    codes = order + sorted(c for c in plates_dict if c not in RACK_PHOTOS)
    cards = "\n".join(rack_card(c, plates_dict[c]) for c in codes if c in plates_dict)
    return f'<div class="rack-grid">\n{cards}\n</div>'


def main():
    data = load_reverse_data()

    plates = data["plates"]
    sidecases = sorted(
        [sku for skus in data["sidecases"].values() for sku in skus],
        key=lambda s: s["name"],
    )
    sidebags = sorted(
        [sku for skus in data["sidebags"].values() for sku in skus],
        key=lambda s: s["name"],
    )
    tankbags = sorted(data["tankbags"], key=lambda s: s["name"])

    html_doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>フィッティングキットとは | SHAD</title>
<style>{PAGE_STYLE}</style>
</head>
<body>

<div class="brand-bar">
  <span class="brand-logo">SHAD<span class="dot">.</span></span>
  <span class="brand-title">フィッティングキットとは</span>
</div>

<div class="intro">
  <h1>フィッティングキットとは？</h1>
  <p>「フィッティング」とは、車体とSHADのケース・バッグをつなぐ取付部品のことです。
  SHADはケースやバッグ専用のフィッティングキットを自社で開発しており、車種本来のデザインを損なうことなく、
  すべてのパーツを安全に取り付けられるようにしています。</p>
  <p>取り付ける製品の種類によって、フィッティングキットの種類も異なります。</p>
</div>

<div class="type-nav">
  <a href="#topmaster"><div class="thumb"><img src="{IMG['nav_topmaster']}" loading="lazy" alt=""></div><div class="label">01 トップマスター</div></a>
  <a href="#sidesystem"><div class="thumb"><img src="{IMG['nav_3p']}" loading="lazy" alt=""></div><div class="label">02 サイド 3Pシステム</div></a>
  <a href="#sidesystem"><div class="thumb"><img src="{IMG['nav_4p']}" loading="lazy" alt=""></div><div class="label">03 サイド 4Pシステム</div></a>
  <a href="#sidebagholder"><div class="thumb"><img src="{IMG['nav_sidebag']}" loading="lazy" alt=""></div><div class="label">04 サイドバッグホルダー</div></a>
  <a href="#clicksystem"><div class="thumb"><img src="{IMG['nav_tankbag']}" loading="lazy" alt=""></div><div class="label">05 クリックシステム</div></a>
</div>

<div class="kit-type-section" id="topmaster">
  <div class="kit-type-hero"><img src="{IMG['banner_topmaster']}" loading="lazy" alt="">
    <h2>トップケース用<br>フィッティングキット</h2></div>

  <p class="kit-type-desc">SHADの「トップマスター」フィッティングキットは、トップケースを車体に取り付けるための専用キットです。
  車種ごとの特性を踏まえて専用設計されており、高品質で着脱も簡単・安全に行えます。
  トップケースを取り付けるには、このフィッティングキットに加えて、SHADケース本体に付属するラック
  （ベースプレート、TERRAシリーズを除く）が必要です。</p>

  <div class="kit-subhead">トップケース用ラック（ベースプレート）</div>
  <p class="kit-type-desc">SHADのプラスチック製ケースには、簡単・快適に取り付けられるラックと金具が付属します。
  SH48/SH51/SH58X/SH59X/TR37/TR48/TR55などの大型ケース・TERRAシリーズには、アクセサリーとして3種類のラックを
  用意しています。いずれも軽量かつ高品質な仕上げで、高い強度を実現しています。</p>

  {rack_grid(plates)}
  <a class="kit-type-more" href="fitting_topcases.html" target="_blank">対応車種一覧を見る ›</a>
</div>

<div class="kit-type-section" id="sidesystem">
  <div class="kit-type-hero"><img src="{IMG['banner_sidesystem']}" loading="lazy" alt="">
    <h2>サイドケース用<br>フィッティングキット</h2></div>

  <div class="spec-columns">
    <div class="spec-block">
      <img class="logo" src="{IMG['logo_3p']}" loading="lazy" alt="3P SYSTEM">
      <img class="system-photo" src="{IMG['nav_3p']}" loading="lazy" alt="3P System">
      <h3>3Pシステム</h3>
      <p>SHADを代表する革新技術のひとつ。3Pシステムは以下の特徴を持つサイド取付システムです。
      一体型デザインで車体とのフィット感に優れ、軽量なため車体重心への影響が少なく安全性が高い上、組み立ても簡単です。</p>
      <table class="spec-table">
        <tr><th>素材</th><td>20mm径スチールフレーム（業界最大級）。粉体焼付塗装。</td></tr>
        <tr><th>デザイン</th><td>車体デザインへの影響を最小限に抑えるジャストフィット。</td></tr>
        <tr><th>対応ケース</th><td>SH38X, SH36, SH35, SH23, TR40, TR30, TR27</td></tr>
      </table>
    </div>
    <div class="spec-block">
      <img class="logo" src="{IMG['logo_4p']}" loading="lazy" alt="4P SYSTEM">
      <img class="system-photo" src="{IMG['nav_4p']}" loading="lazy" alt="4P System">
      <h3>4Pシステム</h3>
      <p>バルセロナで100%設計・製造。TERRAケース・サイドバッグ専用に開発されており、SH23/SH35/SH36/SH38Xにも対応します。
      20mm径（業界最厚クラス）の高強度スチール構造に加え、クロスバーで補強することで、過酷な走行にも耐える最大級の
      強度と安定性を実現しています。</p>
      <table class="spec-table">
        <tr><th>素材</th><td>20mm径スチールフレーム（業界最大級）。粉体焼付塗装。</td></tr>
        <tr><th>耐久性</th><td>過酷な使用を想定した設計。2つのケース間の強度を高めるクロスサポート付き。</td></tr>
        <tr><th>対応ケース</th><td>TR47, TR36, TR27, TR40, TR30, SH38X, SH36, SH35, SH23</td></tr>
      </table>
      <p class="spec-note">※SH23・TR27の装着にはD1TR27FIRアダプターが必要です。</p>
    </div>
  </div>

  {product_grid(sidecases)}
  <a class="kit-type-more" href="fitting_sidekits.html" target="_blank">対応車種一覧を見る ›</a>
</div>

<div class="kit-type-section" id="sidebagholder">
  <div class="kit-type-hero"><img src="{IMG['banner_sidebag']}" loading="lazy" alt="">
    <h2>サイドバッグ用<br>フィッティングキット</h2></div>

  <p class="kit-type-desc">SHADはサイドバッグを安全に固定しながら、車体本来のデザインを損なわない専用フィッティングキットを
  開発しています。いずれも着脱が簡単で、車体のデザインを保ったまま取り付けられます。
  SHADサドルバッグ用には、次の3種類のフィッティングキットを用意しています。</p>

  <div class="holder-columns">
    <div class="holder-card">
      <img src="{IMG['sidebag_se']}" loading="lazy" alt="SE specific">
      <div class="body">
        <h3>車種専用ホルダー（SE）</h3>
        <p>車種ごとに専用設計されたサイドバッグホルダーキットです。</p>
        <div class="compat">対応バッグ：<b>E48, SW42</b>（ストッパー：SL58）</div>
        <a class="holder-link" href="fitting_sidebagholders.html" target="_blank">対応車種一覧を見る ›</a>
      </div>
    </div>
    <div class="holder-card">
      <img src="{IMG['sidebag_universal']}" loading="lazy" alt="Universal">
      <div class="body">
        <h3>ユニバーサルホルダー</h3>
        <div class="code">D0SS5SE</div>
        <p>SHADトップマスターと併用して取り付ける汎用タイプ。車種を問わず装着できます。</p>
        <div class="compat">対応バッグ：<b>E48, SW42</b>（ストッパー：SL58）</div>
        <a class="holder-link" href="{UNIVERSAL_HOLDER_URL}" target="_blank">商品ページを見る ›</a>
      </div>
    </div>
    <div class="holder-card">
      <img src="{IMG['sidebag_sr']}" loading="lazy" alt="Specific SR">
      <div class="body">
        <h3>車種専用ホルダー（SR）</h3>
        <p>カフェレーサースタイルのサドルバッグ専用に設計された車種専用ホルダーキットです。</p>
        <div class="compat">対応バッグ：<b>E48SR, E48, SR38</b>（ストッパー：SL58, SW42）</div>
        <a class="holder-link" href="fitting_sidebagholders.html" target="_blank">対応車種一覧を見る ›</a>
      </div>
    </div>
  </div>

  {product_grid(sidebags)}
  <a class="kit-type-more" href="fitting_sidebagholders.html" target="_blank">対応車種一覧を見る ›</a>
</div>

<div class="kit-type-section" id="clicksystem">
  <div class="kit-type-hero"><img src="{IMG['banner_tankbag']}" loading="lazy" alt="">
    <h2>タンクバッグ用<br>フィッティングキット</h2></div>

  <p class="kit-type-desc">クリックシステムは、SHADのピンシステムを進化させたタンクバッグ用取付システムです。
  使いやすさと車体への統合性に優れ、プッシュボタンを押すだけでワンタッチに取り外せます。
  車種専用のクリックリング（フィッティングキット）をタンクに装着しておけば、対応するクリックシステム対応
  タンクバッグをどれでも共通して使用できます。</p>

  {product_grid(tankbags)}
  <a class="kit-type-more" href="fitting_clicksystem.html" target="_blank">キット一覧を見る ›</a>
</div>

</body>
</html>
"""

    out_path = os.path.join(DIST_DIR, "fitting_kits.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print("  ✓ dist/fitting_kits.html")


if __name__ == "__main__":
    main()
