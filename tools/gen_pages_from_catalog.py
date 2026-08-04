#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 商品ページ生成（カタログJSONベース）
=============================================================================
site/data/catalog/products.json から、まだページが無いモデルの
site/product-<code>.html を生成します。

■ 使い方
    1. python3 tools/build_catalog.py            # カタログJSONを更新
    2. python3 tools/gen_pages_from_catalog.py   # 足りないページだけ生成
       --force を付けると既存ページも上書き（手を入れたページは消えるので注意）

■ 既存の tools/gen_product_pages.py との違い
    あちらは Excel＋アセットフォルダから、キャッチコピーや
    ストーリーブロックまで作り込むツール（初期26ページを生成）。
    こちらはマスターCSVの記載だけでページを作るため、
    独自コピーを入れずに商品を追加できます。

■ 生成内容
    ヘッダー / 適合確認 / フッターは既存ページ（TEMPLATE）から流用。
    ギャラリー・特徴アイコン・説明・スペックはマスターの値のみ。
    価格・カラー・対応アクセサリー・購入ボタンは purchase.js が実行時に描画。
=============================================================================
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
CATALOG = os.path.join(SITE, "data", "catalog", "products.json")
TEMPLATE = os.path.join(SITE, "product", "tr55.html")
PRODUCT_DIR = os.path.join(SITE, "product")
IMG_HOST = "https://img.customjapan.net"
FORCE = "--force" in sys.argv

SERIES_KICK = {
    "TERRA": "TERRA",
    "トップケース": "TOP CASE",
    "サイドケース": "SIDE CASE",
    "クリックシステム": "CLICK SYSTEM",
    "ソフトバッグ": "SOFT LUGGAGE",
    "システムバッグ": "SYSTEM BAG",
    "カフェレーサーバッグ": "CAFE RACER",
    "X-FRAME": "X-FRAME",
    "SHADロック": "SHAD LOCKS",
    "コンフォートシート": "COMFORT SEAT",
}

# マスターの商品名から機械的に作ると長くなるモデルの表示名（手当て）
DISPLAY_CODE = {"XFRAME": "X-FRAME", "SH40CG": "SH40 CARGO"}

# 容量欄が空でも、マスターの本文・寸法から確定できるモデル（根拠をコメントに残す）
CAP_OVERRIDES = {
    "SH45": "45",       # 商品説明サブ「実用性重視の超絶大容量45Lモデル」
    "SH59X": "46-58",   # 商品サイズ「46L/52L/58L(本体外寸)」の3段階
    "SH35": "35",       # 型番＝容量の命名規則（SH23=23L / SH36=36L と一致）。SH36より奥行30mm浅い
    "SH38X": "38",      # 拡張時・片側。説明「収縮時は40%収縮しSH23(23L)と同等」＝23÷0.6≒38L
}

JP_OVERRIDES = {
    "XFRAME": "スマートフォンホルダー",
    "SH40CG": "CARGO トップケース",
    "E02C": "クリックシステム タンクバッグ",
    "E03C": "クリックシステム タンクバッグ",
    "E09C": "クリックシステム タンクバッグ",
    "E09CM": "クリックシステム タンクバッグ",
    "E03CL": "クリックシステム タンクバッグ PRO",
    "E09CL": "クリックシステム タンクバッグ PRO",
    "TR15CL": "TERRA クリックシステム タンクバッグ",
    "E04": "タンクバッグ",
}

COLOR_WORDS = (
    "無塗装ブラック", "ピュアブラック", "マットブラック", "ブラックメタル", "ダークグレー",
    "アルミパネル", "チタニウム", "カーボン", "ガンメタ", "チタン", "シルバー", "ブラック",
    "ホワイト", "グレー", "レッド", "ブルー", "イエロー", "ベージュ", "ブラウン",
)


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def nl2br(s):
    return "<br>".join(esc(x) for x in str(s or "").split("\n") if x.strip())


def img_url(p):
    if not p:
        return ""
    return p if str(p).startswith("http") else IMG_HOST + p


def jp_subtitle(code, name):
    """商品名から型番とカラー名を落とした日本語の商品種別。"""
    if code in JP_OVERRIDES:
        return JP_OVERRIDES[code]
    s = re.sub(r"^\s*" + re.escape(code) + r"\s*", "", name or "", flags=re.I)
    s = re.sub(r"^\s*(CARGO|PRO)\s*", "", s, flags=re.I)
    for w in sorted(COLOR_WORDS, key=len, reverse=True):
        s = s.replace(w, "")
    s = re.sub(r"\s*\d+(?:[-–]\d+)?\s*L(?:\(.*?\))?", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" 　/・")
    return s or (name or code)


def capacity_of(entry, variant):
    """容量の取得順：手当て → 容量欄 → 仕様欄（「36L(片側)」等）→ 商品名。"""
    code = entry.get("code") or ""
    if code in CAP_OVERRIDES:
        return CAP_OVERRIDES[code]
    for src in (variant.get("capacity"), variant.get("spec"),
                variant.get("name"), entry.get("name")):
        m = re.search(r"(\d+(?:[-–]\d+)?)\s*L(?![a-zA-Z])", str(src or ""))
        if m:
            return m.group(1)
    return ""


def material_short(material):
    m = str(material or "")
    for key, label in (("アルミ", "アルミ"), ("ポリプロピレン", "ポリプロピレン"), ("PP", "ポリプロピレン"),
                       ("ターポリン", "ターポリン"), ("ポリエステル", "ポリエステル"),
                       ("ナイロン", "ナイロン"), ("ポリカーボネート", "ポリカーボネート")):
        if key in m:
            return label
    return ""


def helmet_count(text):
    t = str(text or "")
    m = re.search(r"(ジェット|フルフェイス|ヘルメット)[^\n。]{0,12}?([12])\s*個", t)
    if m:
        return "×" + m.group(2)
    # 「片側のみでフルフェイスが収まる」のように個数表記がない場合は1個として扱う
    if re.search(r"(フルフェイス|ジェット)[^\n。]{0,16}?(収納可能|収まる|収納できる)", t):
        return "×1"
    return ""


def max_load(spec):
    m = re.search(r"最大耐荷重[：: ]*([0-9.]+)\s*kg", str(spec or ""))
    return m.group(1) + "kg" if m else ""


HELMET_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"'
              ' stroke-linecap="round" stroke-linejoin="round" width="1em" height="1em">'
              '<path d="M3.5 14a8.5 8.5 0 0 1 17 0"/>'
              '<path d="M3.5 14h17v1.5a1.5 1.5 0 0 1-1.5 1.5h-3.2l-.9 2.4a1 1 0 0 1-.94.6H10a1 1 0 0'
              ' 1-.94-.6L8.2 17H5a1.5 1.5 0 0 1-1.5-1.5z"/></svg>')


def feat_cell(icon, label, value="", oimg=""):
    """既存ページと同じ特徴セル。
    icon='helmet' はカスタムSVG、oimg があれば公式ピクトグラムを使う。"""
    if oimg:
        mark = '<img src="%s" alt="" class="feat-oimg" loading="lazy">' % esc(oimg)
    elif icon == "helmet":
        mark = HELMET_SVG
    else:
        mark = '<i class="ti ti-%s" aria-hidden="true"></i>' % icon
    return ('<div class="feat-cell"><span class="feat-ic">' + mark + "</span>"
            + '<span class="feat-tx"><b>' + esc(label) + "</b>"
            + ("<span>" + esc(value) + "</span>" if value else "") + "</span></div>")


def _pict(name):
    """site/img/feat/ にピクトグラムがあればパスを返す。"""
    rel = "img/feat/%s.webp" % name
    return rel if os.path.exists(os.path.join(SITE, rel)) else ""


def water_grade(text):
    m = re.search(r"(IPX?\d)", str(text or ""))
    return m.group(1) if m else ""


def feature_cells(entry, variant, cap, series):
    """既存ページと同じ並び・粒度で特徴アイコンを組む（最大4つ）。
    値スロットに入れるのは 41L / ×2 / 5kg のような短い値だけ。"""
    v, cells = variant, []
    blob = " ".join(str(v.get(k) or "") for k in ("descSub", "catch", "spec", "material", "name"))

    if cap:
        cells.append(feat_cell("box", "容量", cap + "L"))

    hc = helmet_count(blob)
    if hc:
        cells.append(feat_cell("helmet", "ヘルメット", hc, _pict("2CI" if hc == "×2" else "1CI")))

    ml = max_load(v.get("spec"))
    if ml:
        cells.append(feat_cell("weight", "耐荷重", ml, _pict("MaxLoad" + ml.replace("kg", ""))))

    if "防水" in blob or "ウォータープルーフ" in blob:
        cells.append(feat_cell("droplet", "防水", water_grade(blob)))

    if "クリックシステム" in series or "クリックシステム" in blob:
        cells.append(feat_cell("click", "クリックシステム", "", _pict("CS")))

    if "ステンレス" in (v.get("material") or ""):
        cells.append(feat_cell("lock", "ステンレスロック"))
    elif "キーロック" in blob or "施錠" in blob:
        cells.append(feat_cell("lock", "キーロック"))

    mat = material_short(v.get("material"))
    if mat:
        cells.append(feat_cell("shield", mat))

    if "3P" in blob or "4P" in blob:
        cells.append(feat_cell("tool", "3P/4Pマウント", "", _pict("3P")))

    if len(cells) < 3 and v.get("weight"):
        w = re.sub(r"^本体[：:]\s*", "", str(v["weight"])).split("\n")[0]
        w = re.sub(r"(\d)\.(?=kg)", r"\1", w.replace("..", "."))
        cells.append(feat_cell("weight", "質量", w))

    # 同じラベルが重複しないように整えて4つまで
    out, seen = [], set()
    for c in cells:
        key = re.search(r"<b>(.*?)</b>", c).group(1)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out[:4]


def spec_row(th, td):
    return ('<tr class="border-b border-black/10">'
            '<th class="text-left align-top py-3 pr-6 font-medium text-neutral-500 w-[140px] whitespace-nowrap">'
            + esc(th) + '</th><td class="py-3 text-[14px] leading-relaxed">' + nl2br(td) + "</td></tr>")


STORY_KICKS = (
    ("可変", "EXPANDABLE"), ("拡大", "EXPANDABLE"),
    ("ロック", "SECURITY"), ("セキュリティ", "SECURITY"), ("防犯", "SECURITY"),
    ("防水", "WATERPROOF"), ("雨", "WATERPROOF"),
    ("クリックシステム", "CLICK SYSTEM"), ("ワンタッチ", "QUICK RELEASE"),
    ("脱着", "QUICK RELEASE"), ("取り付け", "MOUNTING"), ("装着", "MOUNTING"),
    ("ヘルメット", "CAPACITY"), ("容量", "CAPACITY"), ("収納", "CAPACITY"),
    ("デザイン", "DESIGN"), ("受賞", "AWARDED"), ("アルミ", "MATERIAL"),
    ("軽", "LIGHTWEIGHT"), ("ツーリング", "TOURING"), ("タンデム", "TOURING"),
)


def _kick_for(text):
    for word, kick in STORY_KICKS:
        if word in text:
            return kick
    return "FEATURE"


def appeal_section(variant, imgs, catch):
    """既存ページと同じ「大きな写真＋文章」の交互ブロックで訴求セクションを作る。
    文章はマスターの記載のまま（独自コピーは足さない）。
    説明が短い商品は写真を多めに使って、見た目のボリュームを揃える。"""
    raw = str(variant.get("descSub") or "")
    bullets = []
    for part in re.split(r"\n+", raw):
        t = re.sub(r"^[・\s]*(?:【\d+】)?\s*", "", part).strip()
        t = re.sub(r"\s+", " ", t)
        if len(t) < 8:
            continue
        bullets.append(t)
    if not imgs and not bullets:
        return ""

    # 1枚目は商品単体カットなので、訴求ブロックには2枚目以降を優先して使う
    pool = (imgs[1:] + imgs[:1]) if len(imgs) > 1 else list(imgs)
    blocks, used = [], 0

    def block(kick, head, body, img, rev):
        return ('<div class="lp-block%s">' % (" lp-rev" if rev else "")
                + ('<div class="lp-block-img"><img src="%s" alt="%s" loading="lazy"></div>'
                   % (esc(img), esc(head)) if img else "")
                + '<div class="lp-block-tx"><span class="lp-block-kick">%s</span>' % esc(kick)
                + '<h3 class="lp-block-h">%s</h3>' % esc(head)
                + ('<p class="lp-block-p">%s</p>' % esc(body) if body else "")
                + "</div></div>")

    # ① 先頭ブロック：キャッチコピーを見出しに、最初の説明を本文に
    lead_body = bullets[0] if bullets else ""
    if catch:
        blocks.append(block("Highlights", catch, lead_body, pool[0] if pool else "", False))
        used = 1
        rest = bullets[1:]
    else:
        rest = bullets

    # ② 以降のブロック：説明ごとに写真を交互配置（先頭の一文を見出しに）
    for i, text in enumerate(rest[:3]):
        head = re.split(r"(?<=。)", text)[0].rstrip("。").strip()
        body = text[len(head) + 1:].strip() if len(text) > len(head) + 1 else ""
        if len(head) > 40:                      # 長い一文は見出しにせず本文に回す
            head, body = re.split(r"(?<=、)", head)[0].rstrip("、"), text
        img = pool[used % len(pool)] if pool else ""
        used += 1
        blocks.append(block(_kick_for(text), head, body, img, (len(blocks) % 2) == 1))

    # ③ 残りの写真はギャラリーとして並べる（説明が短い商品ほどここが効く）
    strip = ""
    left = [p for p in pool[used:] if p][:4]
    if len(left) >= 2:
        cols = "grid-cols-2 md:grid-cols-%d" % min(4, len(left))
        strip = ('<div class="grid %s gap-3.5 md:gap-5 pt-2">' % cols
                 + "".join('<div class="lp-shot"><img src="%s" alt="" loading="lazy"></div>' % esc(p)
                           for p in left) + "</div>")

    # ④ ブロックに使いきれなかった説明は箇条書きで補足
    extra = rest[3:]
    list_html = ""
    if extra:
        list_html = ('<ul class="grid md:grid-cols-2 gap-x-10 gap-y-3.5 pt-9">'
                     + "".join('<li class="flex gap-2.5"><i class="ti ti-circle-check text-shad '
                               'text-[18px] shrink-0 mt-[3px]" aria-hidden="true"></i>'
                               '<span class="text-[14.5px] leading-[1.95] text-neutral-700">%s</span></li>'
                               % esc(b) for b in extra[:4]) + "</ul>")

    return ('<section class="lp-story"><div class="max-w-site mx-auto px-7">'
            + "".join(blocks) + strip + list_html + "</div></section>")


def load_template():
    s = open(TEMPLATE, encoding="utf-8").read()
    head = s[:s.index("</head>")]
    nav = s[s.index("<body "):s.index('<div class="max-w-site mx-auto px-7 pt-6">')]
    i = s.index('<section id="fitment"')
    fit = s[i:s.index("\n</section>\n", i) + len("\n</section>\n")]
    foot = s[s.index("<footer "):]
    # 生成ページには LP ヒーロー動画・縦リールが無いので、その制御スクリプトは外す
    foot = re.sub(r"// ヒーロー動画は確実に再生.*?\n}\n</script>", "</script>", foot, flags=re.S)
    return head, nav, fit, foot


PAGE = """<div class="max-w-site mx-auto px-7 pt-6">
  <a href="products" class="inline-flex items-center gap-2 text-[13px] text-neutral-500 hover:text-shad transition"><i class="ti ti-arrow-left"></i>製品一覧</a>
</div>

<main class="max-w-site mx-auto px-7 py-8 grid md:grid-cols-2 gap-10 items-start">
  <div>
    <div class="g-main"><img id="gMain" src="{main_img}" alt="{code} {jp}"></div>
    <div class="flex flex-wrap gap-2.5 mt-3">{thumbs}</div>
  </div>
  <div>
    <p class="flex items-center gap-2"><span class="font-disp text-[13px] tracking-[.22em] uppercase text-neutral-400">{kick}</span></p>
    <div class="flex items-end justify-between gap-4 mt-2">
      <h1 class="font-disp font-semibold text-[52px] leading-none tracking-[.04em] uppercase">{code}</h1>
      {cap_html}
    </div>
    <p class="text-[15px] text-neutral-500 mt-1.5">{jp}</p>
    <div data-variant-slot class="mt-4"></div>
    {catch_html}
    {feat_grid}
    {warranty}
    <a href="#fitment" data-fit-jump class="btn w-full justify-center mt-5 border border-black/15 bg-white hover:border-shad hover:text-shad"><i class="ti ti-search"></i>適合確認はこちら</a>
    <p class="text-[12px] text-neutral-400 mt-2 text-center">メーカー・車種・年式から、必要なフィッティングキットを確認できます。</p>
  </div>
</main>

{story}

<section class="max-w-site mx-auto px-7 py-10 grid md:grid-cols-2 gap-10">
  <div>
    <h2 class="sec-ttl sec-ttl-quiet">Spec</h2>
    {spec_table}
  </div>
  <div class="min-w-0">
    {note_html}
  </div>
</section>
{fit}
{same_sec}
"""


def main():
    products = json.load(open(CATALOG, encoding="utf-8"))
    head, nav, fit_tpl, foot = load_template()

    by_series = {}
    for code, e in products.items():
        by_series.setdefault(e.get("series") or "", []).append(code)

    os.makedirs(PRODUCT_DIR, exist_ok=True)
    made, skipped = [], []
    for code, entry in products.items():
        path = os.path.join(PRODUCT_DIR, "%s.html" % code.lower())
        if os.path.exists(path):
            existing = open(path, encoding="utf-8").read()
            generated = "generated-by: tools/gen_pages_from_catalog.py" in existing
            # --force でも、手作業で作ったページは上書きしない
            if not (FORCE and generated):
                skipped.append(code)
                continue

        v = entry["variants"][0]
        series = entry.get("series") or ""
        kick = SERIES_KICK.get(series, series or "SHAD")
        jp = jp_subtitle(code, entry.get("name"))
        label = DISPLAY_CODE.get(code, code)
        cap = capacity_of(entry, v)
        catch = v.get("catch") or ""
        descsub = v.get("descSub") or ""

        imgs = [img_url(p) for p in (v.get("images") or [])][:6]
        if not imgs and v.get("thumb"):
            imgs = [v["thumb"]]
        thumbs = "".join(
            '<button class="g-thumb%s" data-src="%s"><img src="%s" alt="" loading="lazy"></button>'
            % (" on" if i == 0 else "", esc(s), esc(s)) for i, s in enumerate(imgs)
        )

        cells = feature_cells(entry, v, cap, series)
        feat_grid = ('<div class="feat-grid">' + "".join(cells) + "</div>") if cells else ""

        rows = []
        for th, key in (("容量", "capacitySpec"), ("質量", "weight"), ("材質", "material"),
                        ("サイズ", "dimensions"), ("仕様", "spec"), ("セット内容・付属品", "included")):
            if v.get(key):
                rows.append(spec_row(th, v[key]))
        spec_table = ('<table class="w-full mt-5 text-[14px] table-fixed">' + "".join(rows) + "</table>"
                      ) if rows else '<p class="text-[13.5px] text-neutral-500 mt-5">仕様は準備中です。詳細はお問い合わせください。</p>'

        # 保証は見出しだけ見せて、クリックで内容を開く（内容はマスターの備考そのまま）
        warranty = ""
        remarks = v.get("remarks") or ""
        if "保証期間：1年" in remarks:
            warranty = ('<details class="warranty mt-7"><summary>'
                        '<i class="ti ti-shield-check" aria-hidden="true"></i>'
                        '<span>1年保証</span><i class="ti ti-chevron-down warranty-mark" aria-hidden="true"></i>'
                        "</summary><div class=\"warranty-body\">" + nl2br(remarks) + "</div></details>")

        same_cards = ""
        for c in [x for x in by_series.get(series, []) if x != code][:3]:
            e2 = products[c]
            # 一覧・同シリーズは大きさを統一したカード画像を使う
            # （生成： python3 tools/build_card_images.py）
            card = "/img/products/cards/%s.webp" % c.lower()
            local = "/img/products/%s.webp" % c.lower()
            if os.path.exists(os.path.join(SITE, card.lstrip("/"))):
                src = card
            elif os.path.exists(os.path.join(SITE, local.lstrip("/"))):
                src = local
            else:
                src = e2["variants"][0].get("thumb") or ""
            same_cards += (
                '<a href="/product/%s" class="pcard group bg-white rounded-[14px] overflow-hidden border border-black/10 transition hover:-translate-y-1 hover:shadow-[0_18px_40px_rgba(0,0,0,.10)]">'
                '<span class="block aspect-square overflow-hidden bg-white"><img src="%s" alt="%s" loading="lazy" class="w-full h-full object-cover transition duration-300 group-hover:scale-[1.04]"></span>'
                '<span class="block px-5 py-4"><span class="font-disp font-semibold text-[20px] tracking-[.05em] uppercase">%s</span>'
                '<span class="block text-[12.5px] text-neutral-500 mt-0.5">%s</span></span></a>'
                % (c.lower(), esc(src), esc(c), esc(c), esc(jp_subtitle(c, e2.get("name"))))
            )
        same_sec = ""
        if same_cards:
            same_sec = ('<section class="bg-mist py-12 mt-8"><div class="max-w-site mx-auto px-7">'
                        '<h2 class="sec-ttl sec-ttl-quiet">Same Series</h2>'
                        '<div class="grid grid-cols-2 sm:grid-cols-3 gap-4 sm:gap-5 mt-6">'
                        + same_cards + "</div></div></section>")

        # OGP / Twitterカード（実装ガイド2.5：画像はルート相対）
        og_img = "/img/products/%s.webp" % code.lower()
        if not os.path.exists(os.path.join(SITE, og_img.lstrip("/"))):
            og_img = "/img/og_default.jpg"
        og = ("\n<!-- OGP / Twitter（画像パスは実装ガイド2.5に従いルート相対）-->\n"
              '<meta property="og:type" content="article">\n'
              '<meta property="og:site_name" content="SHAD JAPAN">\n'
              '<meta property="og:title" content="%s｜%s — SHAD JAPAN">\n'
              '<meta property="og:description" content="%s">\n'
              '<meta property="og:url" content="https://shad.customjapan.net/product/%s">\n'
              '<meta property="og:image" content="%s">\n'
              '<meta property="og:locale" content="ja_JP">\n'
              '<meta name="twitter:card" content="summary_large_image">\n'
              '<meta name="twitter:title" content="%s｜%s — SHAD JAPAN">\n'
              '<meta name="twitter:description" content="%s">\n'
              '<meta name="twitter:image" content="%s">\n'
              % (esc(label), esc(jp), esc(catch or jp), code.lower(), esc(og_img),
                 esc(label), esc(jp), esc(catch or jp), esc(og_img)))

        page_head = (head
                     .replace("<title>TR55｜TERRA トップケース — SHAD JAPAN</title>",
                              "<title>%s｜%s — SHAD JAPAN</title>" % (esc(label), esc(jp)))
                     .replace('<meta name="description" content="シリーズ最大55L。長旅のための容量。">',
                              '<meta name="description" content="%s">' % esc(catch or jp)))

        # テンプレート（TR55）のOGPを、このページ用に差し替える
        page_head = re.sub(r"\n<!-- OGP / Twitter.*?(?=<link rel=\"preconnect\")", "", page_head, flags=re.S)
        page_head = page_head.replace('<link rel="preconnect" href="https://fonts.googleapis.com">',
                                      og + '<link rel="preconnect" href="https://fonts.googleapis.com">', 1)

        html = page_head + "\n<!-- generated-by: tools/gen_pages_from_catalog.py -->\n</head>\n" + nav + PAGE.format(
            main_img=esc(imgs[0] if imgs else ""), thumbs=thumbs, code=esc(label), jp=esc(jp), kick=esc(kick),
            cap_html=('<div class="text-right shrink-0"><span class="cap-num" style="font-size:56px;">'
                      '%s<small style="font-size:28px;">L</small></span></div>' % esc(cap)) if cap else "",
            catch_html=('<p class="text-[17px] font-bold mt-5 leading-relaxed">%s</p>' % esc(catch)) if catch else "",
            feat_grid=feat_grid, warranty=warranty,
            note_html=('<h2 class="sec-ttl sec-ttl-quiet">Notes</h2>'
                       '<p class="text-[12.5px] leading-[1.95] text-neutral-500 mt-5">%s</p>'
                       % nl2br(v.get("note"))) if v.get("note") else "",
            spec_table=spec_table, story=appeal_section(v, imgs, catch),
            fit=fit_tpl.replace('data-product-code="TR55"', 'data-product-code="%s"' % code),
            same_sec=same_sec,
        ) + foot

        open(path, "w", encoding="utf-8").write(html)
        made.append(code)

    print("生成: %d ページ" % len(made))
    for c in made:
        print("   product/%s.html" % c.lower())
    print("既存のためスキップ: %d ページ" % len(skipped))


if __name__ == "__main__":
    main()
