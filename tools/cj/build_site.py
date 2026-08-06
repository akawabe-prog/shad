#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD × Custom Japan（shad.customjapan.net）— 新デザインへの統合ビルド
=============================================================================
デザインの原本は `site-cj/`（「White Studio」テンプレート。SP Connect の
フォルダで作成されたものを取り込んだもの）。そこへ、ブランドサイトで整備した
**商品データ・写真・映像・適合データ**を流し込んで、実データのサイトにします。

■ 入力
    site-cj/*.html                  デザインのテンプレート（原本）
    site-cj/data/catalog/*.json     商品マスター（build_catalog.py 生成）
    site-cj/data/catalog/cards.json 一覧カードの表示情報（コピー・特徴）
    site-cj/data/ec/api_prices.json 販売価格・在庫（fetch_api_prices.py 取得）
    site-cj/assets/img, media       最適化済みの写真・映像

■ 出力（dist/cj/ に生成。site-cj/ のテンプレートは書き換えません）
    index.html                      HERO・カテゴリー・人気製品を実データに
    top-cases / side-cases / bags   実商品のカード一覧（価格・在庫・絞り込み）
    helmets / phone                 マスターに該当SKUが無いため取扱準備中の案内
    product/<code>.html             全モデルの詳細ページ（写真・価格・在庫・仕様）
    data/products_cj.json           生成に使った正規化済み商品データ

■ 使い方
    python3 tools/fetch_api_prices.py     # 価格・在庫を最新化
    python3 tools/cj/build_site.py        # dist/cj/ を生成
=============================================================================
"""

import html
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "site-cj")
OUT = os.path.join(ROOT, "dist", "cj")
IMG_HOST = "https://img.customjapan.net"
EC_ITEM = "https://moto.customjapan.net/i/"
EC_TOP = "https://www.customjapan.net/"

# 新デザインのカテゴリ ← マスターのカテゴリ表記
CAT_RULES = [
    ("top-cases",  ("トップケース",)),
    ("side-cases", ("パニア", "サイドケース")),
    ("bags",       ("バッグ", "リュック")),
]
CAT_EN = {"top-cases": "Top Case", "side-cases": "Side Case", "bags": "Bag",
          "other": "Accessory"}
CAT_JA = {"top-cases": "トップケース", "side-cases": "サイド・パニアケース",
          "bags": "タンク・シートバッグ", "other": "アクセサリー"}
# 一覧ページのURL（other＝ロック・シートなどはアクセサリーページにまとめる）
CAT_PATH = {"top-cases": "top-cases", "side-cases": "side-cases",
            "bags": "bags", "other": "accessories"}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def yen(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return ""
    return "¥{:,}".format(n) if n > 0 else ""


def load():
    j = lambda *p: json.load(open(os.path.join(SRC, "data", *p), encoding="utf-8"))
    products = j("catalog", "products.json")
    cards = j("catalog", "cards.json")
    prices = j("ec", "api_prices.json").get("byCjCode", {})
    return products, cards, prices


def category_of(entry):
    c = entry["variants"][0].get("category", "")
    for cat, keys in CAT_RULES:
        if any(k in c for k in keys):
            return cat
    return "other"


def asset(p):
    """ブランドサイトのパス（/img /media）を新デザインの /assets 配下に読み替える"""
    p = str(p or "")
    if p.startswith("/img/"):
        return "/assets" + p
    if p.startswith("/media/"):
        return "/assets" + p
    return p


def img_url(p):
    if not p:
        return ""
    return p if p.startswith("http") else IMG_HOST + p


def build_db(products, cards, prices):
    """テンプレートに流し込むための正規化済み商品データ"""
    db = {}
    for code, entry in products.items():
        card = cards.get(code, {})
        cat = category_of(entry)
        variants = []
        for v in entry.get("variants", []):
            cj = str(v.get("cjCode") or "")
            pr = prices.get(cj, {})
            variants.append({
                "cjCode": cj,
                "color": v.get("color") or v.get("size") or "",
                "name": v.get("name") or "",
                "listTaxIn": pr.get("listTaxIn") or v.get("msrpTaxIn"),
                "saleTaxIn": pr.get("saleTaxIn"),
                "stock": pr.get("statusTxt") or "",
                "ecUrl": EC_ITEM + cj if cj else EC_TOP,
                "images": [img_url(x) for x in (v.get("images") or [])][:6],
            })
        sale = [v["saleTaxIn"] for v in variants if v["saleTaxIn"]]
        v0 = entry["variants"][0]
        db[code] = {
            "code": code,
            "label": card.get("label") or code,
            "cat": cat,
            "typeEn": CAT_EN[cat],
            "catJa": card.get("jp") or CAT_JA[cat],
            "series": card.get("series") or v0.get("series") or "",
            "sub": card.get("copy") or v0.get("catch") or "",
            "cap": card.get("cap") or v0.get("capacity") or "",
            "colors": card.get("colors") or len(variants),
            "features": [dict(f, oimg=asset(f.get("oimg"))) for f in (card.get("features") or [])],
            "status": card.get("status") or "",
            "new": bool(card.get("new")),
            "cardImg": asset(card.get("img") or ""),
            "minSale": min(sale) if sale else None,
            "listTaxIn": variants[0]["listTaxIn"] if variants else None,
            "stock": variants[0]["stock"] if variants else "",
            "variants": variants,
            "spec": {
                "容量": v0.get("capacitySpec") or v0.get("capacity") or "",
                "重量": v0.get("weight") or "",
                "サイズ": (v0.get("dimensions") or "").replace("\n", " ／ "),
                "素材": (v0.get("material") or "").replace("\n", " ／ "),
                "仕様": (v0.get("spec") or "").replace("\n", " ／ "),
                "JANコード": v0.get("jan") or "",
                "メーカー品番": v0.get("makerCode") or "",
            },
            "descSub": (v0.get("descSub") or "").strip(),
        }
    return db


# ---------------------------------------------------------------- カード

def card_html(p, with_desc=True):
    """カテゴリ一覧・関連製品のカード（デザインの .pcard に実データを流す）"""
    tag = ""
    if p["status"]:
        tag = '<span class="tag">%s</span>' % esc(p["status"])
    elif p["new"]:
        tag = '<span class="tag">New</span>'
    elif p["stock"].startswith("◯"):
        tag = '<span class="tag stock">在庫あり</span>'
    price = (yen(p["minSale"]) + '<small> 税込</small>') if p["minSale"] else '<small>価格はお問い合わせ</small>'
    img = ('<img src="%s" alt="%s %s" loading="lazy">' % (esc(p["cardImg"]), esc(p["label"]), esc(p["catJa"]))
           ) if p["cardImg"] else '<span class="ph" data-label="%s"></span>' % esc(p["label"])
    desc = ('<p class="desc">%s</p>' % esc(p["sub"])) if with_desc and p["sub"] else ""
    return ('<a class="pcard" href="/product/%s" data-series="%s" data-cap="%s">'
            '<div class="pi">%s%s</div>'
            '<div class="pb"><div class="ptype">%s</div><div class="pn">%s%s</div>%s'
            '<div class="foot"><div class="price">%s</div><span class="go">詳細 →</span></div>'
            '</div></a>'
            % (p["code"].lower(), esc(p["series"]), esc(p["cap"]),
               img, tag, esc(p["typeEn"]), esc(p["label"]),
               ('<span class="cap">%s</span>' % esc(p["cap"])) if p["cap"] else "",
               desc, price))


def sort_key(p):
    """容量の大きい順（可変容量は上限）。容量なしは末尾。"""
    nums = re.findall(r"\d+", p["cap"] or "")
    return (-(max(int(n) for n in nums) if nums else -1), p["code"])


# ---------------------------------------------------------------- ページ生成

def replace_div(s, cls, new_inner):
    """<div class="cls"> … </div> の中身を差し替える。
    ページによって改行や入れ子の書き方が違うので、div の深さを数えて閉じを探す。"""
    m = re.search(r'<div class="' + re.escape(cls) + r'"[^>]*>', s)
    if not m:
        raise ValueError("見つかりません: " + cls)
    start = m.end()
    depth, i = 1, start
    while depth and i < len(s):
        nxt_open = s.find("<div", i)
        nxt_close = s.find("</div>", i)
        if nxt_close < 0:
            raise ValueError("閉じが見つかりません: " + cls)
        if 0 <= nxt_open < nxt_close:
            depth += 1
            i = nxt_open + 4
        else:
            depth -= 1
            i = nxt_close + 6
    end = i - 6
    return s[:start] + new_inner + s[end:]


def replace_filters(s, new_inner):
    return re.sub(r'(<div class="filters">)[\s\S]*?(</div>)',
                  lambda m: m.group(1) + new_inner + m.group(2), s, count=1)


FILTERS = {
    "top-cases": [("all", "すべて"), ("TERRA", "TERRA"), ("EXPANDABLE", "EXPANDABLE"),
                  ("big", "大容量 46L+"), ("small", "コンパクト 〜35L")],
    "side-cases": [("all", "すべて"), ("TERRA", "TERRA"), ("EXPANDABLE", "EXPANDABLE"),
                   ("big", "大容量 36L+")],
    "bags": [("all", "すべて"), ("TERRA", "TERRA"), ("tank", "タンクバッグ"),
             ("side", "サイドバッグ")],
}


def filter_bar(cat):
    items = FILTERS.get(cat) or [("all", "すべて")]
    return "\n  ".join(
        '<button data-f="%s"%s>%s</button>' % (k, ' class="on"' if k == "all" else "", esc(v))
        for k, v in items)


FILTER_JS = """
<script>
/* カテゴリ内の絞り込み（シリーズ・容量で実データを絞る） */
(function(){
  var btns=document.querySelectorAll('.filters button');
  var cards=document.querySelectorAll('.grid .pcard');
  function capMax(s){var m=(s||'').match(/\\d+/g);return m?Math.max.apply(null,m.map(Number)):0}
  btns.forEach(function(b){b.addEventListener('click',function(){
    btns.forEach(function(x){x.classList.remove('on')});b.classList.add('on');
    var f=b.dataset.f,shown=0;
    cards.forEach(function(c){
      var series=c.dataset.series||'',cap=capMax(c.dataset.cap),ok=true;
      if(f==='big') ok=cap>=46; else if(f==='small') ok=cap>0&&cap<=35;
      else if(f==='tank') ok=/タンクバッグ/.test(c.textContent);
      else if(f==='side') ok=/サイドバッグ/.test(c.textContent);
      else if(f!=='all') ok=series===f;
      c.style.display=ok?'':'none'; if(ok)shown++;
    });
    var e=document.getElementById('noHit'); if(e) e.style.display=shown?'none':'block';
  })});
})();
</script>
"""


def build_category(cat, db, tpl):
    items = sorted([p for p in db.values() if p["cat"] == cat], key=sort_key)
    grid = "\n    ".join(card_html(p) for p in items)
    s = tpl
    # 絞り込みボタンを実データ用に
    s = replace_filters(s, "\n  " + filter_bar(cat) + "\n")
    # カード一覧
    s = replace_div(s, "grid",
                    "\n    " + grid + "\n"
                    '    <p id="noHit" style="display:none;color:var(--ink-2);font-size:14px">'
                    '条件に合う製品がありません。</p>\n  ')
    # デモ用のフィルタJSを実データ版に差し替え
    s = re.sub(r"<script>\s*/\*?\s*//?\s*フィルタUI[\s\S]*?</script>",
               lambda m: FILTER_JS.strip(), s)
    s = s.replace("</head>", '<link rel="stylesheet" href="/assets/css/shad-integrations.css">\n</head>', 1)
    return s, len(items)


EMPTY_NOTICE = """
    <div class="soon">
      <p class="t">現在、日本国内での取り扱い準備中です。</p>
      <p>%s は日本総代理店 Custom Japan での取り扱いが決まり次第ご案内します。
         取り扱い中の製品は <a href="/top-cases">トップケース</a>・<a href="/side-cases">サイド・パニアケース</a>・
         <a href="/bags">バッグ</a> よりご覧ください。</p>
      <a class="btn btn-outline" href="/contact">入荷について問い合わせる</a>
    </div>
"""


def build_empty_category(label, tpl):
    s = tpl
    s = re.sub(r'<div class="filters">[\s\S]*?</div>\s*', "", s, count=1)
    s = replace_div(s, "grid", EMPTY_NOTICE % label)
    s = s.replace("</head>", '<link rel="stylesheet" href="/assets/css/shad-integrations.css">\n</head>', 1)
    return s


# ---------------------------------------------------------------- 商品詳細

def shell_of(tpl):
    """テンプレートを <head>／ヘッダー部／フッター部 に分解して使い回す"""
    head = tpl[:tpl.index("</head>")]
    top = tpl[tpl.index('<div class="promo">'):tpl.index('<div class="crumb">')]
    foot = tpl[tpl.index("<footer>"):]
    # 末尾のデモ用スクリプトは使わない
    foot = re.sub(r"<script type=\"module\">[\s\S]*?</script>", "", foot)
    return head, top, foot


def gallery_html(p):
    imgs = p["variants"][0]["images"] or ([p["cardImg"]] if p["cardImg"] else [])
    if not imgs:
        return ('<div class="mainwrap"><div class="ph" data-label="%s"></div></div>' % esc(p["label"]))
    main = ('<div class="mainwrap"><img id="mainImg" src="%s" alt="%s %s"></div>'
            % (esc(imgs[0]), esc(p["label"]), esc(p["catJa"])))
    thumbs = "".join(
        '<button class="th%s" data-src="%s"><img src="%s" alt="" loading="lazy"></button>'
        % (" on" if i == 0 else "", esc(u), esc(u)) for i, u in enumerate(imgs[:6]))
    return main + '<div class="thumbs">%s</div>' % thumbs


def price_block(p):
    v = p["variants"][0]
    sale, lst = v["saleTaxIn"], v["listTaxIn"]
    off = ""
    if sale and lst and sale < lst:
        off = '<span class="off" id="pOff">%d%% OFF</span>' % round((1 - sale / lst) * 100)
    return ('<div class="price" id="pPrice">%s<small> 税込</small>%s</div>'
            '<p class="listp" id="pList">%s</p>'
            % (yen(sale) or "価格はお問い合わせください", off,
               ("定価 <s>%s</s>（税込）" % yen(lst)) if lst else ""))


def stock_html(p):
    txt = p["stock"] or "在庫は公式通販でご確認ください"
    cls = "ok"
    if "取寄" in txt or "予約" in txt:
        cls = "order"
    elif "△" in txt or "★" in txt:
        cls = "few"
    elif "×" in txt or "完売" in txt:
        cls = "out"
    return '<div class="stock %s" id="pStock">%s</div>' % (cls, esc(txt))


def variant_chips(p):
    if len(p["variants"]) < 2:
        return ""
    chips = "".join(
        '<button class="chip%s" data-vi="%d">%s</button>'
        % (" on" if i == 0 else "", i, esc(v["color"] or v["name"]))
        for i, v in enumerate(p["variants"]))
    return ('<div class="opt"><div class="lab">カラー・仕様を選ぶ'
            '<span style="font-weight:400;color:var(--ink-3)">（%d種）</span></div>'
            '<div class="chips" id="vChips">%s</div></div>' % (len(p["variants"]), chips))


def features_html(p):
    if not p["features"]:
        return ""
    lis = "".join('<li><b>%s</b>%s</li>'
                  % (esc(f.get("label")), (" " + esc(f.get("val"))) if f.get("val") else "")
                  for f in p["features"][:4])
    return '<ul class="featlist">%s</ul>' % lis


def spec_rows(p):
    rows = [('型番', p["label"]), ('カテゴリー', p["catJa"])]
    rows += [(k, v) for k, v in p["spec"].items() if v]
    rows.append(('品番', '<span id="sSku">%s</span>' % esc(p["variants"][0]["cjCode"])))
    rows.append(('保証', 'メーカー保証1年（日本総代理店 Custom Japan）'))
    return "".join('<tr><th>%s</th><td>%s</td></tr>' % (esc(k), v if k in ("品番",) else esc(v))
                   for k, v in rows)


def related_html(p, db):
    same = [x for x in db.values() if x["cat"] == p["cat"] and x["code"] != p["code"]]
    same.sort(key=lambda x: abs((_cap(x) or 0) - (_cap(p) or 0)))
    return "\n    ".join(card_html(x, with_desc=False) for x in same[:4])


def _cap(p):
    nums = re.findall(r"\d+", p["cap"] or "")
    return max(int(n) for n in nums) if nums else None


PRODUCT_JS = """
<script>
/* カラー・仕様の切り替え：価格／在庫／品番／写真／購入リンクを差し替える */
(function(){
  var V = %(variants)s;
  var chips = document.querySelectorAll('#vChips .chip');
  var main = document.getElementById('mainImg');
  var thumbs = document.querySelector('.thumbs');
  function yen(n){ return n>0 ? '¥'+Number(n).toLocaleString('ja-JP') : ''; }
  function apply(i){
    var v = V[i]; if(!v) return;
    var p = document.getElementById('pPrice');
    var l = document.getElementById('pList');
    var s = document.getElementById('pStock');
    var sku = document.getElementById('sSku');
    var off = v.listTaxIn && v.saleTaxIn && v.saleTaxIn < v.listTaxIn
            ? Math.round((1 - v.saleTaxIn/v.listTaxIn)*100) : 0;
    if(p) p.innerHTML = (yen(v.saleTaxIn)||'価格はお問い合わせください')
      + '<small> 税込</small>' + (off?'<span class="off">'+off+'%% OFF</span>':'');
    if(l) l.innerHTML = v.listTaxIn ? '定価 <s>'+yen(v.listTaxIn)+'</s>（税込）' : '';
    if(s) s.textContent = v.stock || '在庫は公式通販でご確認ください';
    if(sku) sku.textContent = v.cjCode || '—';
    document.querySelectorAll('[data-buy]').forEach(function(a){ a.href = v.ecUrl; });
    var sb = document.getElementById('sbPrice');
    if(sb) sb.textContent = yen(v.saleTaxIn) || '';
    if(main && v.images && v.images.length){
      main.src = v.images[0];
      if(thumbs) thumbs.innerHTML = v.images.slice(0,6).map(function(u,k){
        return '<button class="th'+(k?'':' on')+'" data-src="'+u+'"><img src="'+u+'" alt="" loading="lazy"></button>';
      }).join('');
      bindThumbs();
    }
  }
  function bindThumbs(){
    document.querySelectorAll('.thumbs .th').forEach(function(b){
      b.addEventListener('click', function(){
        if(main) main.src = b.dataset.src;
        document.querySelectorAll('.thumbs .th').forEach(function(x){x.classList.remove('on')});
        b.classList.add('on');
      });
    });
  }
  chips.forEach(function(c){ c.addEventListener('click', function(){
    chips.forEach(function(x){x.classList.remove('on')}); c.classList.add('on');
    apply(Number(c.dataset.vi));
  })});
  bindThumbs();
})();
</script>
"""


def build_product(p, db, head, top, foot):
    v0 = p["variants"][0]
    title = "%s %s | SHAD 日本総代理店 Custom Japan" % (p["label"], p["catJa"])
    desc = p["sub"] or v0["name"]
    url = "https://shad.customjapan.net/product/%s" % p["code"].lower()
    og = v0["images"][0] if v0["images"] else "/assets/img/products/cards/%s.webp" % p["code"].lower()

    h = head
    h = re.sub(r"<title>[\s\S]*?</title>", "<title>%s</title>" % esc(title), h, count=1)
    h = re.sub(r'<meta name="description" content="[^"]*"',
               '<meta name="description" content="%s"' % esc(desc), h, count=1)
    h = re.sub(r'<link rel="canonical" href="[^"]*"',
               '<link rel="canonical" href="%s"' % esc(url), h, count=1)
    h = re.sub(r'(<meta property="og:(?:title|url|image)" content=")[^"]*"',
               lambda m: m.group(1) + {"og:title": esc(title), "og:url": esc(url),
                                       "og:image": esc(og)}[m.group(0).split('"')[1]] + '"', h)
    h += '<link rel="stylesheet" href="/assets/css/shad-integrations.css">\n</head>\n'

    body = """<div class="crumb"><a href="/">Home</a> / <a href="/%(cat)s">%(catEn)s</a> / <b>%(label)s</b></div>

<section class="detail">
  <div class="gallery">%(gallery)s</div>
  <div class="info">
    <div class="ptype">%(typeEn)s</div>
    <h1>%(label)s</h1>
    <p class="sub">%(sub)s</p>
    %(stock)s
    %(price)s
    <p class="taxnote">価格・在庫は日本総代理店 Custom Japan 公式通販の最新情報です（%(fetched)s 時点）。</p>
    %(feats)s
    %(chips)s
    <div class="buybar">
      <a class="btn btn-red" data-buy href="%(ec)s" target="_blank" rel="noopener">公式通販で購入 ↗</a>
      <a class="btn btn-outline" href="/fitting?code=%(codeLower)s">適合を確認</a>
    </div>
    <p class="note">この製品は <b>日本総代理店 Custom Japan</b> の正規品です。ご購入・在庫確認・車種適合のご相談は公式通販にて承ります。</p>
  </div>
</section>

<div style="background:var(--paper-2);border-top:1px solid var(--line);border-bottom:1px solid var(--line)">
<section class="spectable"><h2>Specifications</h2>
  <table>%(spec)s</table>
  %(descSub)s
</section>
</div>

<section class="band rel"><div class="wrap">
  <div class="band-head"><div class="t"><span class="eyebrow">Related</span><h2 class="h-section">関連製品</h2></div><a class="more" href="/%(cat)s">一覧へ →</a></div>
  <div class="grid">
    %(related)s
  </div>
</div></section>

<div class="stickybuy"><div class="p" id="sbPrice">%(sbPrice)s</div><a class="btn btn-red" data-buy href="%(ec)s" target="_blank" rel="noopener">公式通販で購入 ↗</a></div>
""" % {
        "cat": CAT_PATH[p["cat"]], "catEn": esc(CAT_EN[p["cat"]]), "label": esc(p["label"]),
        "gallery": gallery_html(p), "typeEn": esc(p["typeEn"]), "sub": esc(p["sub"]),
        "stock": stock_html(p), "price": price_block(p), "feats": features_html(p),
        "chips": variant_chips(p), "ec": esc(v0["ecUrl"]), "codeLower": p["code"].lower(),
        "spec": spec_rows(p),
        "descSub": ('<div class="descsub">%s</div>'
                    % "".join("<p>%s</p>" % esc(t) for t in p["descSub"].split("\n") if t.strip())
                    ) if p["descSub"] else "",
        "related": related_html(p, db),
        "sbPrice": yen(p["minSale"]),
        "fetched": FETCHED,
    }

    js = PRODUCT_JS % {"variants": json.dumps(p["variants"], ensure_ascii=False)}
    return h + top + body + foot.replace("</body>", js + "</body>")


# ---------------------------------------------------------------- トップページ

HERO_VISUAL = ('<video src="/assets/media/hero_brand.mp4" poster="/assets/img/hero_poster.webp"'
               ' autoplay muted loop playsinline preload="metadata" aria-hidden="true"></video>')

CAT_TILES = [
    ("/top-cases", "Top Cases", "トップケース", "/assets/img/products/cards/tr55.webp"),
    ("/side-cases", "Side / Panniers", "サイド・パニアケース", "/assets/img/products/cards/tr47.webp"),
    ("/bags", "Bags", "タンク・シートバッグ", "/assets/img/products/cards/tr30.webp"),
    ("/fitting", "Fitting / 3P System", "取付キット・適合", "/assets/img/fitting/plate_l.webp"),
    ("/helmets", "Helmets", "ヘルメット", ""),
    ("/phone", "Phone Holders", "スマホホルダー", ""),
]


def build_index(db, tpl):
    s = tpl
    # HERO のプレースホルダーを本国撮影の映像に
    s = s.replace('<div class="ph" data-label="Hero Visual（要 SHAD 画像）"></div>', HERO_VISUAL, 1)
    # カテゴリータイルに実写を入れる
    tiles = []
    for href, en, ja, img in CAT_TILES:
        media = ('<div class="ci"><img src="%s" alt="%s" loading="lazy"></div>' % (esc(img), esc(ja))
                 ) if img else '<div class="ci ph" data-label="%s"></div>' % esc(en)
        tiles.append('<a class="cat" href="%s">%s<div class="cb"><div><div class="en">%s</div>'
                     '<h3>%s</h3></div><span class="ar">→</span></div></a>'
                     % (href, media, esc(en), esc(ja)))
    s = replace_div(s, "cats", "\n    " + "\n    ".join(tiles) + "\n  ")
    # 人気の製品：容量の大きいトップケースとサイドケースから
    pop = [db[c] for c in ("TR55", "SH58X", "TR47", "SH38X") if c in db]
    s = replace_div(s, "prods",
                    "\n    " + "\n    ".join(card_html(p, with_desc=False) for p in pop) + "\n  ")
    s = s.replace("</head>", '<link rel="stylesheet" href="/assets/css/shad-integrations.css">\n</head>', 1)
    return s


# ---------------------------------------------------------------- 追加CSS

INTEGRATIONS_CSS = """/* =========================================================
   実データ統合ぶんの追加スタイル
   （デザイン原本 site-cj/ のトークン・作法に合わせた最小限の追加）
   写真・価格・在庫・容量表示など、プレースホルダーを実データに置き換えた
   部分だけを補う。tools/cj/build_site.py が生成時に読み込ませる。
   ========================================================= */

/* 一覧カード：写真＋容量＋価格 */
.pcard .pi{background:#fff}
.pcard .pi img{width:100%;height:100%;object-fit:contain;padding:10px}
.pcard .pn .cap{font-family:var(--font-en);font-weight:900;color:var(--red);margin-left:7px;font-size:13px}
.pcard .price small{white-space:nowrap}

/* HERO：映像 */
.hero .visual video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}

/* カテゴリータイル：写真 */
.cat .ci{position:relative;background:var(--paper-2)}
.cat .ci img{width:100%;height:100%;object-fit:contain;padding:12px}

/* 商品詳細：ギャラリー */
.gallery .mainwrap img{width:100%;height:100%;object-fit:contain;background:#fff;padding:14px}
.gallery .thumbs .th{padding:0;background:#fff;border:1px solid var(--line)}
.gallery .thumbs .th img{width:100%;height:100%;object-fit:contain;padding:5px}

/* 商品詳細：価格・在庫・特徴 */
.info .price .off{font-family:var(--font-ja);font-size:12px;font-weight:800;letter-spacing:.02em;
  background:var(--red);color:#fff;border-radius:4px;padding:4px 9px;margin-left:10px;vertical-align:middle}
.info .listp{font-size:12.5px;color:var(--ink-3);margin:0 0 4px}
.info .listp s{color:var(--ink-3)}
.info .stock.few{color:#B26A00}.info .stock.few::before{background:#B26A00}
.info .stock.order{color:var(--ink-2)}.info .stock.order::before{background:var(--ink-3)}
.info .stock.out{color:#A11}.info .stock.out::before{background:#A11}
.featlist{list-style:none;display:flex;flex-wrap:wrap;gap:8px;padding:0;margin:0 0 18px}
.featlist li{font-size:12px;color:var(--ink-2);background:var(--paper-2);
  border:1px solid var(--line);border-radius:999px;padding:6px 13px}
.featlist li b{color:var(--ink);font-weight:800}

/* 仕様表の下に本国の解説文 */
.descsub{margin-top:22px;max-width:76ch}
.descsub p{font-size:14px;color:var(--ink-2);line-height:1.95;margin:0 0 10px}

/* 取扱準備中の案内 */
.soon{grid-column:1/-1;text-align:center;background:var(--paper-2);border:1px solid var(--line);
  border-radius:12px;padding:clamp(30px,5vw,56px) 24px}
.soon .t{font-size:17px;font-weight:800;margin:0 0 10px}
.soon p{color:var(--ink-2);font-size:14px;max-width:60ch;margin:0 auto 18px}
.soon a.btn{margin-top:4px}
"""


# ---------------------------------------------------------------- main

def main():
    global FETCHED
    prices_path = os.path.join(SRC, "data", "ec", "api_prices.json")
    import datetime
    FETCHED = datetime.datetime.fromtimestamp(
        os.path.getmtime(prices_path)).strftime("%Y.%m.%d")

    products, cards, prices = load()
    db = build_db(products, cards, prices)

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT, ignore=shutil.ignore_patterns(".DS_Store", ".claude"))

    css_dir = os.path.join(OUT, "assets", "css")
    os.makedirs(css_dir, exist_ok=True)
    open(os.path.join(css_dir, "shad-integrations.css"), "w", encoding="utf-8").write(INTEGRATIONS_CSS)

    read = lambda name: open(os.path.join(SRC, name), encoding="utf-8").read()
    write = lambda name, s: open(os.path.join(OUT, name), "w", encoding="utf-8").write(s)

    # ① トップ
    write("index.html", build_index(db, read("index.html")))

    # ② カテゴリー
    counts = {}
    for cat, fname in (("top-cases", "top-cases.html"), ("side-cases", "side-cases.html"),
                       ("bags", "bags.html")):
        s, n = build_category(cat, db, read(fname))
        write(fname, s)
        counts[cat] = n
    # ロック・シートなどのアクセサリー
    acc, n_acc = build_category("other", db, read("bags.html"))
    acc = acc.replace("<title>バッグ", "<title>アクセサリー")
    acc = re.sub(r'<span class="eyebrow">[^<]*</span>\s*<h1>[^<]*</h1>',
                 '<span class="eyebrow">Accessories — アクセサリー</span><h1>Accessories</h1>',
                 acc, count=1)
    acc = re.sub(r'<p class="lead">[\s\S]*?</p>',
                 '<p class="lead">ハンドルロックやコンフォートシートなど、SHAD の周辺アイテム。</p>',
                 acc, count=1)
    acc = acc.replace('<a href="/">Home</a> / <b>Bags</b>',
                      '<a href="/">Home</a> / <b>Accessories</b>')
    write("accessories.html", acc)
    counts["other"] = n_acc

    write("helmets.html", build_empty_category("ヘルメット", read("helmets.html")))
    write("phone.html", build_empty_category("スマホホルダー", read("phone.html")))

    # ③ 商品詳細（テンプレートは product.html。生成後は使わないので削除）
    head, top, foot = shell_of(read("product.html"))
    pdir = os.path.join(OUT, "product")
    os.makedirs(pdir, exist_ok=True)
    made = []
    for code, p in sorted(db.items()):
        open(os.path.join(pdir, code.lower() + ".html"), "w", encoding="utf-8").write(
            build_product(p, db, head, top, foot))
        made.append(code)
    os.remove(os.path.join(OUT, "product.html"))

    # ④ 生成に使ったデータも置いておく（他ページからの参照用）
    json.dump(db, open(os.path.join(OUT, "data", "products_cj.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

    print("=" * 66)
    print("SHAD × Custom Japan サイトを生成: dist/cj/")
    print("=" * 66)
    print("デザイン原本      : site-cj/（White Studio）")
    print("価格・在庫        : %s 時点（%d品番）" % (FETCHED, len(prices)))
    print("カテゴリー        : トップケース %d / サイド %d / バッグ %d"
          % (counts["top-cases"], counts["side-cases"], counts["bags"]))
    print("商品詳細ページ    : %d件（/product/<型番>）" % len(made))
    print("取扱準備中の案内  : helmets / phone（マスターに該当SKUなし）")
    print("アクセサリー      : %d件（/accessories）" % counts.get("other", 0))


FETCHED = ""

if __name__ == "__main__":
    main()
