#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — NEWS（一覧・詳細ページ）の生成
=============================================================================
記事データ site/data/news/news.json から、次を生成します。

    site/news/index.html          一覧（/news）※カテゴリで絞り込み
    site/news/<slug>.html         詳細（/news/<slug>）
    site/index.html の NEWS 枠     最新4件のカード（マーカー間を差し替え）

記事の追加・修正は **news.json だけ** を編集して、このスクリプトを実行します。
HTMLを直接触る必要はありません。

■ 使い方
    python3 tools/build_news.py

■ news.json の書き方
    {
      "categories": ["News", "Racing", "Event"],     ← 絞り込みチップの並び
      "articles": [
        {
          "slug":     "tr41-order-resume",           ← URL（/news/tr41-order-resume）
          "date":     "2026-06-10",                  ← 表示は 2026.06.10
          "category": "News",
          "title":    "TERRA TR41 受注を再開しました",
          "lead":     "一覧とOGPに出る1〜2文の要約",
          "image":    "/img/news_1.webp",            ← 空ならグレーのプレースホルダー
          "draft":    true,                          ← true = 本文準備中の表示
          "body": [                                  ← 本文（上から順に組まれます）
            {"type":"h",  "text":"見出し"},
            {"type":"p",  "text":"段落。改行は \\n で入れられます"},
            {"type":"ul", "items":["箇条書き1","箇条書き2"]},
            {"type":"img","src":"/img/news/xxx.webp","caption":"写真の説明"},
            {"type":"quote","text":"引用・コメント"}
          ],
          "products": ["TR41"]                       ← 関連商品（型番／任意）
        }
      ]
    }

    body を空にして draft:true にしておくと、詳細ページは
    「本文は準備中です」の案内を出します（リンク切れを作らずに公開できます）。
    本文を入れたら draft を false にしてください。
=============================================================================
"""

import html
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "data", "news", "news.json")
CARDS = os.path.join(SITE, "data", "catalog", "cards.json")
TEMPLATE = os.path.join(SITE, "fitment.html")     # nav / footer の雛形（同じ器）
OUT_DIR = os.path.join(SITE, "news")
INDEX = os.path.join(SITE, "index.html")
SITE_URL = "https://shad.customjapan.net"

TOP_START = "<!-- NEWS:START 生成 tools/build_news.py -->"
TOP_END = "<!-- NEWS:END -->"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def jp_date(iso):
    return iso.replace("-", ".")


def load_shell():
    """nav と footer を fitment.html から借りる（器を1本に保つ）。"""
    s = open(TEMPLATE, encoding="utf-8").read()
    head_open = s[:s.index("<title>")]
    head_tail = s[s.index("<link rel=\"preconnect\""):s.index("</head>")]
    nav = s[s.index("<body "):s.index('<div class="bg-ink2 text-white">')]
    foot = s[s.index("<footer "):]
    # 借り元は適合検索ページなので「For Your Motorcycle」が同一ページ内アンカー。
    # NEWSページでは行き先が無いので /fitment に直し、現在地のハイライトも外す。
    nav = nav.replace('href="#finder"', 'href="/fitment"')
    nav = nav.replace('<a class="text-white" href="/fitment">',
                      '<a class="hover:text-white transition" href="/fitment">')
    return head_open, head_tail, nav, foot


def page_head(title, desc, url, image):
    """<head> の共通部分＋OGP（実装ガイド2.5に従いルート相対）"""
    t, d = esc(title), esc(desc)
    return """<title>{t}</title>
<meta name="description" content="{d}">

<!-- OGP / Twitter -->
<meta property="og:type" content="article">
<meta property="og:site_name" content="SHAD JAPAN">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{img}">
<link rel="canonical" href="{url}">
""".format(t=t, d=d, url=esc(url), img=esc(image or "/img/og_default.jpg"))


def hero(kicker, title, date=None, category=None, desc=None):
    meta = ""
    if date:
        meta = ('<p class="flex items-center gap-3 mt-5 text-white/70">'
                '<span class="news-cat">%s</span>'
                '<span class="font-disp text-[14px] tracking-[.16em]">%s</span></p>'
                % (esc(category), jp_date(date)))
    elif desc:
        meta = ('<p class="text-white/70 text-[14.5px] mt-4 max-w-[680px] leading-[1.95]">%s</p>'
                % esc(desc))
    return """<section class="bg-ink2 text-white pt-[54px] pb-[58px] md:pt-[70px] md:pb-[74px]">
  <div class="max-w-site mx-auto px-7">
    <p class="flex items-center gap-3"><span class="w-9 h-px bg-shad"></span>
      <span class="font-disp text-[12px] tracking-[.26em] uppercase text-shad">%s</span></p>
    <h1 class="font-disp font-semibold text-[clamp(30px,5.4vw,54px)] leading-[1.06] tracking-[.03em] uppercase mt-3">%s</h1>
    %s
  </div>
</section>""" % (esc(kicker), esc(title), meta)


# ---------- 本文ブロック ----------

def body_html(blocks):
    out = []
    for b in blocks:
        kind = b.get("type")
        if kind == "h":
            out.append('<h2>%s</h2>' % esc(b.get("text")))
        elif kind == "p":
            out.append('<p>%s</p>' % esc(b.get("text")).replace("\n", "<br>"))
        elif kind == "ul":
            out.append('<ul>%s</ul>'
                       % "".join('<li>%s</li>' % esc(i) for i in b.get("items", [])))
        elif kind == "img":
            cap = ('<figcaption>%s</figcaption>' % esc(b["caption"])) if b.get("caption") else ""
            out.append('<figure><img src="%s" alt="%s" loading="lazy">%s</figure>'
                       % (esc(b.get("src")), esc(b.get("caption") or ""), cap))
        elif kind == "quote":
            out.append('<blockquote>%s</blockquote>' % esc(b.get("text")))
    return "\n".join(out)


def related_products(codes, cards):
    if not codes:
        return ""
    items = []
    for code in codes:
        c = cards.get(code)
        if not c:
            continue
        cap = ('<span class="rp-cap">%s</span>' % esc(c["cap"])) if c.get("cap") else ""
        items.append(
            '<a href="/product/%s" class="rp-card">'
            '<span class="rp-thumb"><img src="%s" alt="%s" loading="lazy"></span>'
            '<span class="rp-body"><span class="rp-code">%s</span>%s'
            '<span class="rp-jp">%s</span></span></a>'
            % (code.lower(), esc(c.get("img")), esc(code),
               esc(c.get("label") or code), cap, esc(c.get("jp") or ""))
        )
    if not items:
        return ""
    return """<section class="max-w-site mx-auto px-7 pb-[10px]">
  <h2 class="sec-ttl sec-ttl-quiet">Related Products</h2>
  <div class="rp-grid mt-5">%s</div>
</section>""" % "".join(items)


def prev_next(articles, i):
    """新しい順に並んだ配列での前後（前＝より新しい記事）"""
    links = []
    if i > 0:
        a = articles[i - 1]
        links.append('<a href="/news/%s" class="pn-link"><span class="pn-lb">'
                     '<i class="ti ti-arrow-left"></i>新しい記事</span>'
                     '<span class="pn-ttl">%s</span></a>'
                     % (esc(a["slug"]), esc(a["title"])))
    else:
        links.append('<span></span>')
    if i < len(articles) - 1:
        a = articles[i + 1]
        links.append('<a href="/news/%s" class="pn-link pn-next"><span class="pn-lb">'
                     '古い記事<i class="ti ti-arrow-right"></i></span>'
                     '<span class="pn-ttl">%s</span></a>'
                     % (esc(a["slug"]), esc(a["title"])))
    else:
        links.append('<span></span>')
    return '<div class="pn-row">%s</div>' % "".join(links)


# ---------- 詳細ページ ----------

DETAIL = """{nav}
{hero}

<div class="max-w-site mx-auto px-7 pt-7">
  <a href="/news" class="inline-flex items-center gap-2 text-[13px] text-neutral-500 hover:text-shad transition"><i class="ti ti-arrow-left"></i>NEWS一覧</a>
</div>

<main class="pb-[70px]">
  {figure}
  <article class="news-body">
    <p class="news-lead">{lead}</p>
    {body}
  </article>
</main>
{related}
<section class="max-w-site mx-auto px-7 pb-[80px]">
  {pn}
  <div class="mt-9 text-center">
    <a href="/news" class="btn border border-black/15 bg-white hover:border-shad hover:text-shad"><i class="ti ti-list"></i>NEWS一覧へ</a>
  </div>
</section>
{foot}"""

DRAFT_NOTE = ('<div class="news-draft"><i class="ti ti-info-circle"></i>'
              'この記事の本文は準備中です。詳細は追ってお知らせします。</div>')


def build_detail(a, i, articles, cards, shell):
    head_open, head_tail, nav, foot = shell
    title = "%s｜NEWS｜SHAD JAPAN" % a["title"]
    url = "%s/news/%s" % (SITE_URL, a["slug"])
    figure = ""
    if a.get("image"):
        figure = ('<div class="news-hero-img"><img src="%s" alt="%s"></div>'
                  % (esc(a["image"]), esc(a["title"])))
    body = body_html(a.get("body") or [])
    if not body:
        body = DRAFT_NOTE if a.get("draft") else ""
    page = DETAIL.format(
        nav=nav,
        hero=hero("News", a["title"], a["date"], a.get("category")),
        figure=figure,
        lead=esc(a.get("lead") or ""),
        body=body,
        related=related_products(a.get("products") or [], cards),
        pn=prev_next(articles, i),
        foot=foot,
    )
    return (head_open + page_head(title, a.get("lead") or a["title"], url, a.get("image"))
            + head_tail + "</head>\n" + page)


# ---------- 一覧ページ ----------

def card_html(a, reveal=True):
    if a.get("image"):
        thumb = ('<span class="block aspect-[4/3] overflow-hidden">'
                 '<img src="%s" alt="" loading="lazy" class="w-full h-full object-cover transition duration-300 hover:scale-105"></span>'
                 % esc(a["image"]))
    else:
        thumb = '<span class="block aspect-[4/3] bg-gradient-to-br from-[#E4E1DB] to-[#D5D2CA]"></span>'
    return ('<a href="/news/%s" class="ncard"%s data-cat="%s">%s'
            '<span class="block px-5 py-4">'
            '<span class="flex items-center gap-2.5">'
            '<span class="ncard-cat">%s</span>'
            '<span class="font-disp text-[13.5px] tracking-[.14em] text-neutral-500">%s</span></span>'
            '<span class="block text-[15.5px] font-medium mt-1.5 leading-relaxed">%s</span>'
            '</span></a>'
            % (esc(a["slug"]), ' data-reveal' if reveal else '', esc(a.get("category")),
               thumb, esc(a.get("category")), jp_date(a["date"]), esc(a["title"])))


LIST = """{nav}
{hero}

<main class="bg-mist py-[52px]">
  <div class="max-w-site mx-auto px-7">
    <div class="cat-filter" id="newsFilter">
      <button type="button" class="cat-chip on" data-cat="all">すべて</button>
      {chips}
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-7 mt-7" id="newsGrid">
      {cards}
    </div>
    <p class="text-[13.5px] text-neutral-500 mt-8 hidden" id="newsEmpty">このカテゴリの記事はまだありません。</p>
  </div>
</main>

<script>
/* カテゴリ絞り込み（記事はページ内にあるので即時に切り替わる） */
(function(){{
  var chips=document.querySelectorAll('#newsFilter .cat-chip');
  var cards=document.querySelectorAll('#newsGrid .ncard');
  var empty=document.getElementById('newsEmpty');
  chips.forEach(function(chip){{
    chip.addEventListener('click',function(){{
      var cat=chip.dataset.cat, shown=0;
      chips.forEach(function(c){{ c.classList.toggle('on', c===chip); }});
      cards.forEach(function(card){{
        var on = (cat==='all' || card.dataset.cat===cat);
        card.style.display = on ? '' : 'none';
        if(on) shown++;
      }});
      empty.classList.toggle('hidden', shown>0);
    }});
  }});
}})();
</script>
{foot}"""


def build_list(articles, shell):
    head_open, head_tail, nav, foot = shell
    cats = json.load(open(DATA, encoding="utf-8")).get("categories", [])
    chips = "".join('<button type="button" class="cat-chip" data-cat="%s">%s</button>'
                    % (esc(c), esc(c)) for c in cats)
    cards = "\n      ".join(card_html(a) for a in articles)
    title = "NEWS｜SHAD JAPAN — 新商品・イベント・レースの最新情報"
    desc = "SHAD JAPAN の新商品情報、イベント出展、レース活動のお知らせをご案内します。"
    page = LIST.format(nav=nav,
                       hero=hero("Information", "News", desc=desc),
                       chips=chips, cards=cards, foot=foot)
    return (head_open + page_head(title, desc, SITE_URL + "/news", "/img/news_1.webp")
            + head_tail + "</head>\n" + page)


# ---------- TOPページの NEWS 枠 ----------

def update_top(articles):
    s = open(INDEX, encoding="utf-8").read()
    cards = "\n      ".join(card_html(a) for a in articles[:4])
    block = "%s\n      %s\n      %s" % (TOP_START, cards, TOP_END)
    if TOP_START in s and TOP_END in s:
        s = re.sub(re.escape(TOP_START) + r".*?" + re.escape(TOP_END), block, s, flags=re.S)
    else:
        # 初回のみ：既存の手書きカード（grid の中身）をマーカー付きブロックに置き換える
        m = re.search(r'(<div class="grid grid-cols-2 lg:grid-cols-4 gap-5 md:gap-7">)(.*?)(</div>\s*</div>\s*</section>)',
                      s, flags=re.S)
        if not m:
            print("⚠ TOPページの NEWS 枠が見つかりませんでした（手動で確認してください）")
            return False
        s = s[:m.start(2)] + "\n      " + block + "\n    " + s[m.end(2):]
    open(INDEX, "w", encoding="utf-8").write(s)
    return True


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    cards = json.load(open(CARDS, encoding="utf-8")) if os.path.exists(CARDS) else {}
    articles = sorted(data["articles"], key=lambda a: a["date"], reverse=True)
    shell = load_shell()

    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    for i, a in enumerate(articles):
        path = os.path.join(OUT_DIR, a["slug"] + ".html")
        open(path, "w", encoding="utf-8").write(build_detail(a, i, articles, cards, shell))

    open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8").write(
        build_list(articles, shell))

    top = update_top(articles)
    drafts = [a["slug"] for a in articles if a.get("draft")]
    print("=" * 62)
    print("NEWS を生成しました")
    print("=" * 62)
    print("一覧            : /news")
    print("詳細            : %d 記事" % len(articles))
    for a in articles:
        print("    /news/%-24s %s  %s" % (a["slug"], jp_date(a["date"]), a["title"]))
    print("TOPページの NEWS: %s" % ("最新4件に更新" if top else "更新できませんでした"))
    if drafts:
        print("\n⚠ 本文が準備中（draft:true）の記事: %s" % " / ".join(drafts))
        print("  news.json の body を書いて draft を false にすると本文が出ます")


if __name__ == "__main__":
    main()
