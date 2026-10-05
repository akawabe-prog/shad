#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — SEO 用ランディングページ（カテゴリ／用途／特長）を商品データから生成する
=============================================================================
    python3 tools/build_landing.py

生成するページ（商品名・ブランド名以外の検索語の受け皿）
  /top-cases          バイク用トップケース・リアボックス（容量帯別の全モデル＋選び方＋FAQ）
  /side-cases         サイドケース・サイドバッグ（3P/4P システムの説明＋全モデル＋サイドバッグの固定方法＋FAQ）
  /tank-bags          タンクバッグ（クリックシステムの説明＋選び方＋全モデル＋FAQ）
  /bags               サイドバッグ・タンクバッグ・シートバッグ（用途別＋FAQ）
  /guide/top-case-size  トップケースの容量の選び方（30L／40L／50L で入るもの）
  /waterproof         防水・耐水のバイク用バッグとケース（IPX 等級の説明＋該当モデル）
  /helmet-storage     ヘルメットが入るトップケース・サイドケース（収納数別）
  /locks              SHAD LOCKS：スクーター用ハンドルバーロックの仕組み・本体・車種専用キット一覧（マスターから生成）

・本文のコピーはこのファイル内（PAGES）。モデル一覧・容量・ヘルメット数・価格は
  site/data/catalog/products.json / cards.json / tools/product_tags.json から自動で入る。
・ヘッダー／フッターは site/terra.html のものを流用（デザインの一貫性のため）。
・各ページに BreadcrumbList／ItemList／FAQPage の JSON-LD を入れる。
・新しいページを足したら tools/build_sitemap.py を実行して sitemap に載せる。
=============================================================================
"""
import os, re, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
BASE = "https://www.shad-japan.com"
P = json.load(open(os.path.join(SITE, "data/catalog/products.json"), encoding="utf-8"))
C = json.load(open(os.path.join(SITE, "data/catalog/cards.json"), encoding="utf-8"))
T = json.load(open(os.path.join(ROOT, "tools/product_tags.json"), encoding="utf-8"))["products"]

# ---------- 商品データの読み出し ----------
def v0(code): return P[code]["variants"][0]
def cat(code): return v0(code).get("category") or ""
def cap_num(code):
    m = re.search(r"(\d+)", v0(code).get("capacity") or ""); return int(m.group(1)) if m else 0
def cap_max(code):
    nums = [int(x) for x in re.findall(r"(\d+)", v0(code).get("capacity") or "")]; return max(nums) if nums else 0
def helmets(code):
    f = next((f for f in C.get(code, {}).get("features", []) if f.get("label") == "ヘルメット"), None)
    return int(f["val"].replace("×", "")) if f and f.get("val") else 0
def helmet_note(code):
    t = v0(code).get("spec") or ""
    m = re.search(r"([^\n。]*ヘルメット[^\n。]*)", t)
    return m.group(1).strip("※ ") if m else ""
def ipx(code):
    t = " ".join(str(v0(code).get(k) or "") for k in ("spec", "descSub", "remarks", "catch", "note"))
    m = sorted(set(re.findall(r"IPX\s?(\d)", t))); return ("IPX" + m[-1]) if m else ""
def sys_support(code):
    t = (v0(code).get("note") or "") + (v0(code).get("spec") or "")
    s = []
    if "3Pシステム" in t: s.append("3P")
    if "4Pシステム" in t: s.append("4P")
    return "／".join(s)
def price(code):
    p = P[code].get("priceMin"); return "¥{:,}".format(p) if p else ""
def tags(code): return T.get(code, [])
TOP = [c for c in P if "トップケース" in cat(c)]
SIDE = [c for c in P if "サイドケース" in cat(c)]
SIDEBAG = [c for c in P if "サイドバッグ" in cat(c) and "クラッシュバー" not in v0(c)["name"]]
TANK = [c for c in P if "タンクバッグ" in cat(c)]
SEATBAG = [c for c in P if "シートバッグ" in cat(c)]
OTHERBAG = [c for c in P if c in ("SC25", "IB20", "TR08")]
def by_cap(codes, desc=True): return sorted(codes, key=lambda c: (-cap_max(c) if desc else cap_max(c), c))

# ---------- 共通部品 ----------
TERRA = open(os.path.join(SITE, "terra.html"), encoding="utf-8").read()
NAV = TERRA[TERRA.index("<!-- ===== NAV ====="):TERRA.index("<!-- ===== ① HERO")]
FOOTER = TERRA[TERRA.index("<footer"):TERRA.index("</footer>") + len("</footer>")]
HEAD_TOP = TERRA[:TERRA.index("<title>")]          # GTM・charset・viewport
HEAD_ASSETS = TERRA[TERRA.index('<link rel="preconnect"'):TERRA.index("</head>")]

def esc(s): return html.escape(s, quote=True)

def card(code):
    c = C.get(code) or {}
    jp = c.get("jp") or v0(code)["name"]
    capv = c.get("cap") or v0(code).get("capacity") or ""
    m = re.match(r"^([\d\-–]+)(L)$", capv)
    cap_html = ('<span class="cap-num%s">%s<small>%s</small></span>' % (" cap-long" if m and len(m.group(1)) >= 4 else "", m.group(1), m.group(2))) if m else ('<span class="cap-num cap-long">%s</span>' % esc(capv) if capv else "")
    feats = ""
    for f in c.get("features", [])[:3]:
        ic = ('<img class="oimg" src="%s" alt="">' % f["oimg"]) if f.get("oimg") else ('<i class="ti ti-%s"></i>' % f.get("ic", "check"))
        feats += '<span class="feat"><span class="fi">%s</span>%s%s</span>' % (ic, esc(f.get("label", "")), (" <b>%s</b>" % esc(f["val"])) if f.get("val") else "")
    pr = price(code)
    return ('<a href="/product/%s" class="pcard group bg-white rounded-[14px] overflow-hidden border border-black/10 transition hover:-translate-y-1 hover:shadow-[0_18px_40px_rgba(0,0,0,.10)]">'
            '<div class="relative aspect-square bg-white overflow-hidden flex items-center justify-center p-3">'
            '<img src="%s" alt="%s %s" loading="lazy" class="w-full h-full object-contain transition duration-300 group-hover:scale-[1.04]"></div>'
            '<div class="px-5 pt-4 pb-5"><div class="pcard-head"><h3 class="font-disp font-semibold text-[24px] tracking-[.05em] uppercase leading-none">%s</h3>%s</div>'
            '<p class="pcard-jp text-[12.5px] text-neutral-500 mt-1.5 leading-[1.45]">%s%s</p>'
            '<p class="text-[13.5px] font-medium mt-3 leading-relaxed">%s</p>'
            '<div class="feat-row">%s</div>'
            '%s'
            '<span class="inline-flex items-center gap-1.5 mt-3 text-[13px] text-neutral-500 group-hover:text-shad transition">詳しく見る <i class="ti ti-arrow-right"></i></span>'
            '</div></a>') % (code.lower(), c.get("img") or "/img/products/%s.webp" % code.lower(), esc(code), esc(jp), esc(c.get("label") or code), cap_html, esc(jp),
                             ("　<span class='text-[12px] text-neutral-400'>%d色</span>" % c["colors"]) if c.get("colors", 0) > 1 else "",
                             esc(c.get("copy") or ""), feats, ('<p class="text-[12.5px] text-neutral-500 mt-2.5">定価 %s（税込）</p>' % pr) if pr else "")

def grid(codes):
    return '<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-5">%s</div>' % "".join(card(c) for c in codes)

def group(title, sub, codes):
    if not codes: return ""
    return ('<div class="mt-10"><h3 class="font-disp font-semibold text-[22px] tracking-[.06em] uppercase flex items-baseline gap-3">%s<span class="font-sans normal-case tracking-normal text-[13px] text-neutral-500 font-normal">%s</span></h3>'
            '<div class="mt-4">%s</div></div>') % (esc(title), esc(sub), grid(codes))

def faq_html(items):
    out = []
    for q, a in items:
        out.append('<details class="faq-item"><summary class="faq-q"><span class="qmark">Q</span><span>%s</span><i class="ti ti-chevron-down chev"></i></summary><div class="faq-a">%s</div></details>' % (esc(q), a))
    return "".join(out)

def faq_ld(items):
    return json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in items]}, ensure_ascii=False)

def itemlist_ld(name, codes):
    return json.dumps({"@context": "https://schema.org", "@type": "ItemList", "name": name, "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": "%s %s" % (c, (C.get(c) or {}).get("jp", "")), "url": "%s/product/%s" % (BASE, c.lower())} for i, c in enumerate(codes)]}, ensure_ascii=False)

def crumbs_ld(path, name, parent=None):
    items = [{"@type": "ListItem", "position": 1, "name": "ホーム", "item": BASE + "/"}]
    if parent:
        items.append({"@type": "ListItem", "position": 2, "name": parent[0], "item": BASE + parent[1]})
    items.append({"@type": "ListItem", "position": len(items) + 1, "name": name, "item": BASE + path})
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}, ensure_ascii=False)

def section(kick, h2, body, cls="py-14 md:py-20"):
    return ('<section class="%s"><div class="max-w-site mx-auto px-7">'
            '<p class="font-disp font-semibold text-[13px] tracking-[.3em] uppercase text-shad flex items-center gap-3"><span class="inline-block w-[26px] h-[2px] bg-shad"></span>%s</p>'
            '<h2 class="text-[clamp(24px,3vw,34px)] font-bold leading-[1.4] mt-3">%s</h2>%s</div></section>') % (cls, esc(kick), h2, body)

def p(t): return '<p class="text-[15px] leading-[2] text-neutral-700 mt-4 max-w-[820px]">%s</p>' % t
def ul(items): return '<ul class="mt-4 space-y-2 max-w-[820px]">%s</ul>' % "".join('<li class="flex gap-3 text-[14.5px] leading-[1.9] text-neutral-700"><i class="ti ti-check text-shad mt-1.5 shrink-0"></i><span>%s</span></li>' % i for i in items)
def table(head, rows):
    return ('<div class="overflow-x-auto mt-6 max-w-[900px]"><table class="w-full text-[14px] border-collapse"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % ("".join('<th class="text-left font-semibold py-3 px-3 border-b-2 border-black/15 whitespace-nowrap">%s</th>' % esc(h) for h in head),
               "".join("<tr>%s</tr>" % "".join('<td class="py-3 px-3 border-b border-black/10 align-top leading-[1.8]">%s</td>' % c for c in r) for r in rows)))
def links(items):
    return '<div class="flex flex-wrap gap-3 mt-8">%s</div>' % "".join('<a href="%s" class="inline-flex items-center gap-2 border border-black/15 rounded-full px-5 py-2.5 text-[14px] hover:border-shad hover:text-shad transition">%s<i class="ti ti-arrow-right"></i></a>' % (h, esc(t)) for t, h in items)

def hero(kick, h1, lead, img):
    return ('<section class="relative bg-ink text-white overflow-hidden"><img src="%s" alt="" class="absolute inset-0 w-full h-full object-cover opacity-45" loading="eager">'
            '<div class="absolute inset-0 bg-gradient-to-r from-black/85 via-black/55 to-black/20"></div>'
            '<div class="relative max-w-site mx-auto px-7 py-[clamp(64px,9vw,120px)]">'
            '<p class="font-disp font-semibold text-[13px] tracking-[.3em] uppercase text-shad flex items-center gap-3"><span class="inline-block w-[26px] h-[2px] bg-shad"></span>%s</p>'
            '<h1 class="text-[clamp(30px,4.4vw,52px)] font-bold leading-[1.25] mt-4 max-w-[760px]">%s</h1>'
            '<p class="text-[15.5px] leading-[2] text-white/85 mt-5 max-w-[680px]">%s</p>'
            '<div class="flex flex-wrap gap-3 mt-8"><a href="/fitment" class="btn bg-shad text-white hover:bg-[#c4151b]"><i class="ti ti-search"></i>車種から適合を探す</a><a href="/products" class="btn border border-white/45 text-white hover:border-white">製品一覧</a></div>'
            '</div></section>') % (img, esc(kick), h1, lead)

def cta():
    return ('<section class="bg-ink text-white py-16"><div class="max-w-site mx-auto px-7 text-center">'
            '<h2 class="text-[clamp(22px,3vw,32px)] font-bold">あなたのバイクに付くモデルを、車種から確認できます。</h2>'
            '<p class="text-white/75 mt-3 text-[15px]">メーカー・車種・年式を選ぶだけで、適合モデルと必要なフィッティングキットを表示します。</p>'
            '<div class="flex flex-wrap gap-3 mt-7 justify-center"><a href="/fitment" class="btn bg-shad text-white hover:bg-[#c4151b]"><i class="ti ti-search"></i>車種から探す</a><a href="/store-locator" class="btn border border-white/45 text-white hover:border-white">取扱店を探す</a></div>'
            '</div></section>')

def page(path, title, desc, body, lds, og_img="/img/og_default.jpg"):
    url = BASE + path
    head = (HEAD_TOP + "<title>%s</title>\n<meta name=\"description\" content=\"%s\">\n\n"
            "<meta property=\"og:type\" content=\"article\">\n<meta property=\"og:site_name\" content=\"SHAD JAPAN\">\n<meta property=\"og:title\" content=\"%s\">\n<meta property=\"og:description\" content=\"%s\">\n<meta property=\"og:url\" content=\"%s\">\n<meta property=\"og:image\" content=\"%s%s\">\n<meta property=\"og:locale\" content=\"ja_JP\">\n"
            "<meta name=\"twitter:card\" content=\"summary_large_image\">\n<meta name=\"twitter:title\" content=\"%s\">\n<meta name=\"twitter:description\" content=\"%s\">\n<meta name=\"twitter:image\" content=\"%s\">\n"
            % (esc(title), esc(desc), esc(title), esc(desc), url, BASE, og_img, esc(title), esc(desc), og_img))
    head += HEAD_ASSETS + "<link rel=\"canonical\" href=\"%s\">\n" % url
    head += "".join('<script type="application/ld+json">%s</script>\n' % ld for ld in lds)
    head += "<style>.pcard-head{display:flex;align-items:baseline;justify-content:space-between;gap:10px;}.pcard-head .cap-num{font-family:\"Barlow Condensed\",sans-serif;font-weight:600;color:#E31E24;font-size:30px;white-space:nowrap;}.pcard-head .cap-num small{font-size:16px;}.pcard-head .cap-num.cap-long{font-size:22px;}.pcard-head .cap-num.cap-long small{font-size:14px;}.feat-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px;}.feat{display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#5F5E5A;background:#F4F3F1;border-radius:6px;padding:3px 8px;line-height:1.4;}.feat .fi{color:#0E0E0E;font-size:13px;display:inline-flex;align-items:center;}.feat .fi .oimg{width:16px;height:16px;object-fit:contain;display:block;}.feat b{font-family:\"Barlow Condensed\",sans-serif;font-weight:600;color:#E31E24;letter-spacing:.02em;font-size:12.5px;}</style>\n</head>\n"
    body_html = ('<body class="font-sans text-[15px] leading-relaxed text-neutral-900 bg-white antialiased">\n'
                 '<!-- Google Tag Manager (noscript) -->\n<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-WR5JQJ8" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n<!-- End Google Tag Manager (noscript) -->\n'
                 + NAV + body + cta() + FOOTER + '\n<script src="/js/nav.js"></script>\n</body>\n</html>\n')
    out = os.path.join(SITE, path.lstrip("/") + ".html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(head + body_html)
    return out

# ---------- ページ定義 ----------
def build_top_cases():
    path = "/top-cases"; name = "トップケース・リアボックス"
    big = [c for c in by_cap(TOP) if cap_max(c) >= 50]; mid = [c for c in by_cap(TOP) if 40 <= cap_max(c) < 50]; small = [c for c in by_cap(TOP) if cap_max(c) < 40]
    faq = [
        ("トップケースの取り付けには何が必要ですか？", "<p>ケース本体のほかに、車種ごとに形が違う<a href='/fitting-kits'>フィッティングキット（トップマスター）</a>が必要です。ベースプレートはケースに付属するモデルと別売のモデルがあります。<a href='/fitment'>車種から探す</a>で、お使いのバイクに合うキットが分かります。</p>"),
        ("リアボックスの容量はどのくらいが目安ですか？", "<p>通勤・買い物中心ならジェットヘルメットが入る30〜40L、ツーリングやタンデムでフルフェイスを2個入れたいなら45L以上が目安です。詳しくは<a href='/guide/top-case-size'>容量の選び方</a>をご覧ください。</p>"),
        ("アルミとPP（樹脂）はどう違いますか？", "<p>アルミ（TERRA シリーズ）は硬化アルミ合金の 1.2mm 薄肉で、堅牢さと質感が特長です。PP（ポリプロピレン）は軽く、価格も抑えられ、転倒時の割れにも強い素材です。どちらもロック機構はステンレス製です。</p>"),
        ("雨の日でも中身は濡れませんか？", "<p>ハードケースはラバーシールで雨水の侵入を抑える構造です（完全防水ではありません）。長時間の豪雨や高圧洗浄では浸水することがあるため、電子機器などは防水インナーバッグに入れることをおすすめします。</p>"),
        ("トップケースとサイドケースの鍵をひとつにできますか？", "<p>対応モデルの組み合わせであれば、キーシリンダーを入れ替えて1本の鍵にまとめられます。組み合わせごとの可否は<a href='/lock-guide'>ワンキー化ガイド</a>で確認できます。</p>"),
    ]
    body = hero("Top Cases", "バイク用トップケース・リアボックス", "通勤の荷物からタンデムのヘルメット2個まで。SHAD のトップケースは 26L から 58L まで %d モデル。すべて車種専用のフィッティングキットで、純正のように取り付けられます。" % len(TOP), "/img/products/sh58x/off_ride.webp")
    body += section("How to choose", "トップケースの選び方",
        p("最初に決めるのは<b>容量</b>です。入れたいものがヘルメットなら、ジェットは 30L 前後から、フルフェイス1個は 40L 前後から、フルフェイス2個は 45L 以上が目安になります。次に<b>素材</b>（アルミか PP か）、最後に<b>ロックや機能</b>（スマートロック、可変容量、TERRA Lock）で絞り込みます。")
        + ul(["<b>〜39L</b>：日常使いの軽量クラス。車体の幅を超えにくく、すり抜けの多い街乗りに。", "<b>40〜49L</b>：ツーリングの定番。フルフェイス1個＋雨具やカメラが入る。", "<b>50L〜</b>：タンデムやロングツーリング。ヘルメット2個や大きな荷物に。"])
        + links([("容量の選び方を詳しく", "/guide/top-case-size"), ("ヘルメットが入るモデル", "/helmet-storage"), ("TERRA（アルミ）シリーズ", "/terra"), ("可変容量 Expandable", "/expandable")]))
    body += section("Lineup", "全モデル（容量順）", group("50L〜", "タンデム・ロングツーリング", big) + group("40〜49L", "ツーリングの定番", mid) + group("〜39L", "日常使いの軽量クラス", small), "pb-14 md:pb-20")
    body += section("FAQ", "よくあるご質問", '<div class="mt-6 max-w-[860px]">%s</div>' % faq_html(faq), "pb-16 md:pb-24")
    page(path, "バイク用トップケース・リアボックス｜容量・ヘルメット収納数で選ぶ — SHAD JAPAN",
         "バイク用トップケース（リアボックス）%dモデルを容量順に掲載。ジェット・フルフェイスのヘルメット収納数、アルミ／PP素材、スマートロックや可変容量で選べます。車種専用フィッティングキットで純正のように取付。SHAD日本公式サイト。" % len(TOP),
         body, [crumbs_ld(path, name), itemlist_ld("SHAD トップケース", by_cap(TOP)), faq_ld(faq)], "/img/products/sh58x/off_ride.webp")

def build_side_cases():
    path = "/side-cases"; name = "サイドケース・サイドバッグ"
    alu = [c for c in by_cap(SIDE) if "alu" in tags(c)]; pp = [c for c in by_cap(SIDE) if "alu" not in tags(c)]
    bags = by_cap(SIDEBAG)
    rows = [(("<a href='/product/%s' class='text-shad font-semibold'>%s</a>" % (c.lower(), c)), esc((C.get(c) or {}).get("jp", "")), esc(v0(c).get("capacity") or ""), esc(sys_support(c) or "—"), "アルミ" if "alu" in tags(c) else "PP", esc(price(c))) for c in by_cap(SIDE)]
    BAG_MOUNT = {"TR30": "4P システム（一部 3P）", "TR40": "4P システム（一部 3P）", "E48": "SR キット／サイドバッグホルダー／汎用ストラップ", "E48SR": "SR フィッティングキット", "SL58": "サイドバッグホルダー／汎用ストラップ", "SR38": "SR フィッティングキット"}
    bag_rows = [(("<a href='/product/%s' class='text-shad font-semibold'>%s</a>" % (c.lower(), c)), esc((C.get(c) or {}).get("jp", "")), esc(v0(c).get("capacity") or ""), esc(BAG_MOUNT.get(c, "—")), esc(ipx(c) or ("防水" if "waterproof" in tags(c) else "レインカバー等")), esc(price(c))) for c in bags]
    faq = [
        ("サイドケースの取り付けには何が必要ですか？", "<p>車種専用の<a href='/fitting-kits'>サイドケース用フィッティングキット</a>（3P システムまたは 4P システム）が必要です。3P はケースを外すとステーがほとんど目立たない SHAD 特許の方式、4P は TERRA アルミケースなど重量のあるケース向けの4点支持です。</p>"),
        ("3P システムと 4P システムの違いは？", "<p>3P システムは3点でケースを支え、取り外すと車体がすっきり見えるのが特長です。4P システムは4点支持で TERRA のアルミサイドケースのような大型・高積載のケースに対応します。モデルごとの対応は上の表と<a href='/fitment'>適合検索</a>で確認できます。</p>"),
        ("サイドケースとサイドバッグ、どちらを選べばよいですか？", "<p>鍵をかけて荷物を置いて離れたい、ヘルメットを入れたい、長期間使いたいならハードのサイドケース。軽さ、価格、外したときの身軽さを優先するならサイドバッグです。TERRA の TR30／TR40 はバッグでも鍵1本で固定と開口部を守るダブルロックを備えています。</p>"),
        ("サイドバッグはどうやって車体に固定しますか？", "<p>モデルによって異なります。TR30／TR40 は 4P システムのキット、E48SR／SR38 は車種別の SR フィッティングキット、E48／SL58 はサイドバッグホルダーまたは付属の汎用ストラップで固定します。ストラップのみの場合も、ホルダーを併用するとマフラーやタイヤへの接触を防げます。</p>"),
        ("すり抜けを考えると幅はどのくらいになりますか？", "<p>SH23・SH36・TR36 のようなスリム設計のモデルは張り出しを抑えています。車種とキットの組み合わせで全幅が変わるため、商品ページの寸法と適合情報をご確認ください。</p>"),
        ("トップケースと鍵をひとつにできますか？", "<p>対応する組み合わせであればキーシリンダーの入れ替えで1本の鍵にまとめられます。<a href='/lock-guide'>ワンキー化ガイド</a>で組み合わせごとの可否を確認できます。</p>"),
    ]
    body = hero("Side Cases & Bags", "バイク用サイドケース・サイドバッグ", "左右に振り分けて、重心を低く、積載を大きく。硬化アルミ合金の TERRA、軽量な PP、走行中に容量を変えられる Expandable のハードケース %d モデルと、軽さと身軽さで選ぶサイドバッグ %d モデル。" % (len(SIDE), len(bags)), "/img/terra/corner.webp")
    body += section("How to choose", "サイドケースの選び方",
        p("サイドケースは<b>取り付け方式（3P／4P）</b>と<b>素材</b>で選びます。街乗りでケースを外す機会が多いなら、外したときに目立たない 3P システム対応のモデル。アドベンチャーや長距離で重い荷物を積むなら、4P システムで支える TERRA アルミサイドケース（TR36／TR47）が向きます。")
        + table(["モデル", "名称", "容量（片側）", "取付方式", "素材", "定価（税込）"], rows)
        + links([("フィッティングキットとは", "/fitting-kits"), ("TERRA（アルミ）シリーズ", "/terra"), ("ワンキー化ガイド", "/lock-guide")]))
    body += section("Side Cases", "サイドケース 全モデル", group("アルミ（TERRA）", "4P システム対応", alu) + group("PP（樹脂）", "軽量・3P システム対応モデルを含む", pp), "pb-10")
    body += section("Side Bags", "サイドバッグ（サドルバッグ）",
        p("ハードケースほど大げさにしたくない日や、オフロードで軽さが欲しい日はサイドバッグ。TERRA の TR30（IPX6 防水）と TR40 は、鍵1本で固定と開口部の両方を守るダブルロックシステムを備え、ケースに近い安心感があります。E48SR は ABS 樹脂のハードシェルにダイヤルロック、SR38 はクラシック車に合う合成皮革。E48／SL58 は容量を変えられる定番のソフトバッグです。")
        + table(["モデル", "名称", "容量", "固定方法", "防水", "定価（税込）"], bag_rows)
        + '<div class="mt-6">%s</div>' % grid(bags)
        + links([("防水・耐水バッグ", "/waterproof"), ("バッグ全モデル（タンク・シート含む）", "/bags")]), "pb-14 md:pb-20")
    body += section("FAQ", "よくあるご質問", '<div class="mt-6 max-w-[860px]">%s</div>' % faq_html(faq), "pb-16 md:pb-24")
    page(path, "バイク用サイドケース・サイドバッグ｜3P／4Pシステムで車種専用に取付 — SHAD JAPAN",
         "バイク用サイドケース（パニアケース）%dモデルとサイドバッグ%dモデル。硬化アルミ合金のTERRA、軽量PP、可変容量のExpandable、防水サドルバッグTR30／TR40。SHAD特許の3Pシステム／4Pシステムの車種専用フィッティングキットで取り付け。容量・取付方式・定価の一覧表付き。" % (len(SIDE), len(bags)),
         body, [crumbs_ld(path, name), itemlist_ld("SHAD サイドケース・サイドバッグ", by_cap(SIDE) + bags), faq_ld(faq)], "/img/terra/corner.webp")

def build_bags():
    path = "/bags"; name = "バイク用バッグ"
    allb = SIDEBAG + TANK + SEATBAG + OTHERBAG
    faq = [
        ("サイドバッグは車体に固定できますか？", "<p>SHAD のサイドバッグは専用のサポートやフィッティングキットで固定します。TERRA のサドルバッグ（TR30／TR40）は鍵1本で固定と開口部の両方を守るダブルロックシステム、E48 はクリックシステムで1秒で着脱できます。</p>"),
        ("タンクバッグの取り付けにタンクの加工は必要ですか？", "<p>クリックシステムのタンクバッグは、車種別のタンクリング（PIN SYSTEM）を給油口のボルトに共締めして取り付けます。磁石を使わないので塗装を傷めず、ワンタッチで着脱できます。対応するタンクリングは<a href='/fitment'>適合検索</a>で確認できます。</p>"),
        ("防水のバッグはどれですか？", "<p>TR30（IPX6）、TR10CL（IPX5）、TR08（IPX4）、IB20 が防水仕様です。TR40 は防水インナーバッグで荷物を守ります。詳しくは<a href='/waterproof'>防水・耐水バッグの一覧</a>をご覧ください。</p>"),
        ("シートバッグにヘルメットは入りますか？", "<p>TR50（40L）はフルフェイスヘルメット2個まで収納でき、ロック機能も備えています。</p>"),
    ]
    body = hero("Bags", "バイク用サイドバッグ・タンクバッグ・シートバッグ", "ハードケースほど大げさにしたくない日、オフロードで軽さが欲しい日。防水のサドルバッグ、1秒で着脱できるクリックシステムのタンクバッグ、ヘルメット2個が入るシートバッグまで %d モデル。" % len(allb), "/img/terra/urban.webp")
    body += section("How to choose", "用途から選ぶ",
        ul(["<b>サイドバッグ・サドルバッグ</b>：左右に振り分けて積載。TERRA のアドベンチャー用（TR30／TR40）と、街乗り向けのスリムなもの（E48／SR38／SL58）。", "<b>タンクバッグ</b>：地図やスマホ、財布など取り出す頻度の高いものに。クリックシステムなら給油のたびに1秒で外せます。", "<b>シートバッグ・ツーリングバッグ</b>：タンデムシートに載せる大容量。TR50 はロック付きでヘルメット2個。", "<b>そのほか</b>：スクーター用のSC25、クラッシュバーに付ける TR08、荷物を水から守る IB20。"])
        + links([("防水・耐水バッグ", "/waterproof"), ("TERRA バッグの特長", "/terra"), ("適合するフィッティングを確認", "/fitment")]))
    body += section("Lineup", "全モデル", group("サイドバッグ・サドルバッグ", "", by_cap(SIDEBAG)) + group("タンクバッグ", "クリックシステム対応モデルを含む", by_cap(TANK)) + group("シートバッグ・ツーリングバッグ", "", by_cap(SEATBAG)) + group("そのほかのバッグ", "", by_cap(OTHERBAG)), "pb-14 md:pb-20")
    body += section("FAQ", "よくあるご質問", '<div class="mt-6 max-w-[860px]">%s</div>' % faq_html(faq), "pb-16 md:pb-24")
    page(path, "バイク用サイドバッグ・タンクバッグ・シートバッグ｜防水・ロック付き — SHAD JAPAN",
         "バイク用バッグ%dモデル。防水のサドルバッグ（TR30／TR40）、1秒で着脱できるクリックシステムのタンクバッグ、フルフェイス2個が入るロック付きシートバッグ TR50。用途別の選び方と全モデル一覧。SHAD日本公式サイト。" % len(allb),
         body, [crumbs_ld(path, name), itemlist_ld("SHAD バッグ", by_cap(allb)), faq_ld(faq)], "/img/terra/urban.webp")

def build_size_guide():
    path = "/guide/top-case-size"; name = "トップケースの容量の選び方"
    rows = []
    for lo, hi, lb, use in ((0, 35, "26〜35L", "ジェットヘルメット1個、またはレインウェア＋小物。通勤・買い物の定番サイズ"), (36, 44, "36〜44L", "フルフェイス1個（モデルによる）＋小物。日帰りツーリングに"), (45, 49, "45〜49L", "フルフェイス1個＋ジェット1個、または1泊分の荷物。タンデムにも"), (50, 99, "50L〜", "フルフェイス2個、または数日分の荷物。ロングツーリング・キャンプ")):
        ms = [c for c in by_cap(TOP, desc=False) if lo <= cap_max(c) <= hi]
        rows.append((lb, use, " ".join("<a href='/product/%s' class='text-shad font-semibold whitespace-nowrap'>%s</a>" % (c.lower(), c) for c in ms)))
    faq = [
        ("フルフェイスヘルメットが入る最小の容量は？", "<p>ヘルメットのサイズや形状で変わりますが、SHAD では 40L 前後からフルフェイス1個を想定しています。各モデルの収納目安は<a href='/helmet-storage'>ヘルメットが入るモデル一覧</a>にまとめています。</p>"),
        ("大きいほど良いですか？", "<p>大きいケースは重心が高く後ろになり、取り回しや高速走行時の安定性に影響します。普段入れるものの量で選び、たまの長旅はサイドケースやシートバッグで足す方が走りは軽く保てます。</p>"),
        ("容量を途中で変えられるケースはありますか？", "<p>あります。<a href='/expandable'>Expandable</a> の SH58X／SH59X（46〜58L）、SH38X（23〜32L）は、走行中でも荷物に合わせて容量を変えられます。</p>"),
        ("ケースの重さはどのくらいですか？", "<p>PP（樹脂）のモデルで約3〜5.5kg、アルミの TERRA でも約5〜5.5kg です。最大積載量はモデルごとに決まっています（TERRA アルミケースは 10kg）。商品ページのスペックをご確認ください。</p>"),
    ]
    body = hero("Guide", "トップケースの容量の選び方｜30L・40L・50Lで何が入る？", "リアボックスは「何を入れるか」で容量が決まります。ヘルメットの種類と個数、1泊分の荷物、通勤の荷物。容量帯ごとに入るものの目安と、該当する SHAD のモデルをまとめました。", "/img/products/sh58x/off_helmets.webp")
    body += section("Capacity", "容量帯ごとの目安", table(["容量", "入るものの目安・向いている使い方", "該当モデル"], rows)
        + p("数字が同じでも、ケースの形（深さ・幅）で入るものは変わります。ヘルメットは「収納個数」の表示を、キャンプ道具や長物は「内寸」を商品ページで確認してください。")
        + links([("トップケース全モデル", "/top-cases"), ("ヘルメットが入るモデル", "/helmet-storage"), ("車種から適合を探す", "/fitment")]))
    body += section("Tips", "容量以外に見るポイント",
        ul(["<b>幅</b>：すり抜けが多いなら車体幅を超えにくいモデルを。SH26〜SH40 クラスはスリムです。", "<b>重さと最大積載量</b>：ケース本体＋荷物の合計がリアキャリアの許容荷重を超えないように。", "<b>開け方</b>：鍵を差したままにしないプッシュボタン式（SH48・SH58X・SH59X のスマートロック）は、荷物の出し入れが多い人に便利です。", "<b>サイドケースとの併用</b>：鍵をひとつにまとめたいなら<a href='/lock-guide' class='text-shad'>ワンキー化ガイド</a>で組み合わせを確認。"]), "pb-14 md:pb-20")
    body += section("FAQ", "よくあるご質問", '<div class="mt-6 max-w-[860px]">%s</div>' % faq_html(faq), "pb-16 md:pb-24")
    page(path, "トップケースの容量の選び方｜30L・40L・50Lで何が入る？ — SHAD JAPAN",
         "バイク用トップケース（リアボックス）の容量の選び方。ジェット・フルフェイスのヘルメットが入る容量の目安、通勤・ツーリング・タンデム別のおすすめ容量、容量帯ごとのSHADモデル一覧。幅・重さ・最大積載量のチェックポイントも解説。",
         body, [crumbs_ld(path, name, ("トップケース", "/top-cases")), faq_ld(faq)], "/img/products/sh58x/off_helmets.webp")

def build_waterproof():
    path = "/waterproof"; name = "防水・耐水バッグとケース"
    wp = [c for c in P if "waterproof" in tags(c)]
    rows = [("<a href='/product/%s' class='text-shad font-semibold'>%s</a>" % (c.lower(), c), esc((C.get(c) or {}).get("jp", "")), esc(v0(c).get("capacity") or ""), esc(ipx(c) or ("インナーバッグで防水" if c == "TR40" else "防水")), esc(price(c))) for c in by_cap(wp)]
    faq = [
        ("IPX6・IPX5・IPX4 の違いは何ですか？", "<p>数字が大きいほど水への強さが上です。IPX4 は雨の飛沫、IPX5 はあらゆる方向からの噴流水、IPX6 は強い噴流水（豪雨や水しぶき）に耐える目安です。TR30 は IPX6、TR10CL は IPX5、TR08 は IPX4 です。</p>"),
        ("ハードケース（トップケース・サイドケース）は防水ですか？", "<p>ラバーシールで雨水の侵入を抑えますが、完全防水ではありません。TERRA の TR41／TR46／TR27 は IPX5 相当の耐水性を持ちます。濡れて困るものは IB20 のような防水インナーバッグに入れてから収納することをおすすめします。</p>"),
        ("TR40 は防水ではないのですか？", "<p>TR40 本体は高密度ポリエステルで耐候性がありますが、防水は付属のインナーバッグが担います。荷物をインナーバッグに入れて使うことで水から守る設計です。</p>"),
        ("洗車機や高圧洗浄機を当てても大丈夫ですか？", "<p>IPX の等級は高圧洗浄を想定していません。バッグ・ケースともに高圧の水は避けてください。</p>"),
    ]
    body = hero("Waterproof", "バイク用の防水・耐水バッグとケース", "IPX6 の完全防水サドルバッグから、雨をはじくタンクバッグ、ラバーシールで雨水を防ぐハードケースまで。「どこまで水に強いか」を等級ごとに整理しました。", "/img/terra/ride2.webp")
    body += section("Lineup", "防水・耐水のモデル一覧", table(["モデル", "名称", "容量", "防水等級", "定価（税込）"], rows)
        + p("ハードケース（トップケース・サイドケース）はラバーシールで雨水の侵入を抑える構造です。TERRA の TR41・TR46・TR27 は IPX5 相当の耐水性を持ちます。")
        + links([("バッグ全モデル", "/bags"), ("TERRA バッグの特長", "/terra"), ("適合するフィッティングを確認", "/fitment")]))
    body += section("IPX", "IPX 等級の読み方", table(["等級", "目安", "SHAD のモデル"], [("IPX6", "強い噴流水に耐える。豪雨や水しぶきでも中身を守る", "TR30"), ("IPX5", "あらゆる方向からの噴流水に耐える。雨天走行に十分", "TR10CL、SR38、IB20（TR41／TR46／TR27 は相当）"), ("IPX4", "飛沫に耐える。通り雨に対応", "TR08")]), "pb-14 md:pb-20")
    body += section("FAQ", "よくあるご質問", '<div class="mt-6 max-w-[860px]">%s</div>' % faq_html(faq), "pb-16 md:pb-24")
    page(path, "バイク用の防水・耐水バッグとケース｜IPX6／IPX5／IPX4 等級別一覧 — SHAD JAPAN",
         "バイク用の防水バッグ・耐水ケースをIPX等級別に一覧。IPX6の防水サドルバッグTR30、IPX5の防水タンクバッグTR10CL、IPX4のTR08、防水インナーバッグIB20。ハードケースの耐水性とIPX等級の読み方も解説。SHAD日本公式サイト。",
         body, [crumbs_ld(path, name), itemlist_ld("SHAD 防水バッグ", by_cap(wp)), faq_ld(faq)], "/img/terra/ride2.webp")

def build_helmet():
    path = "/helmet-storage"; name = "ヘルメットが入るトップケース・サイドケース"
    cases = TOP + SIDE
    two = [c for c in by_cap(cases) if helmets(c) >= 2]; one = [c for c in by_cap(cases) if helmets(c) == 1]
    rows = [("<a href='/product/%s' class='text-shad font-semibold'>%s</a>" % (c.lower(), c), esc((C.get(c) or {}).get("jp", "")), esc(v0(c).get("capacity") or ""), "×%d" % helmets(c), esc(helmet_note(c) or "—")) for c in two + one]
    faq = [
        ("フルフェイスは何リットルから入りますか？", "<p>目安は 40L 前後からです。ただしヘルメットのサイズ（L／XL）や形状、ケースの深さで変わります。各モデルの「ヘルメット」表示と商品ページの内寸をご確認ください。</p>"),
        ("ヘルメット2個が入るトップケースはどれですか？", "<p>%s です。フルフェイス2個かフルフェイス＋ジェットかはモデルで異なります。</p>" % "、".join(c for c in two if c in TOP)),
        ("サイドケースにヘルメットは入りますか？", "<p>%s はヘルメット1個を収納できます。TERRA の TR47 はトレイル1個、またはフリップアップ＋ジェットの2個を収納できます。</p>" % "、".join(c for c in one if c in SIDE)),
        ("ヘルメットを入れると他の荷物は入りませんか？", "<p>ヘルメットの周りの隙間にグローブや雨具は入ります。ヘルメット2個と1泊分の荷物を一緒に積みたい場合は、サイドケースやシートバッグとの併用をおすすめします。</p>"),
    ]
    body = hero("Helmet Storage", "ヘルメットが入るトップケース・サイドケース", "停めたら、ヘルメットごと鍵をかけたい。フルフェイス2個が入る大容量から、ジェット1個の軽量クラスまで、収納数別に %d モデルをまとめました。" % len(two + one), "/img/products/sh58x/off_helmets.webp")
    body += section("Lineup", "収納できるヘルメットの数で選ぶ", table(["モデル", "名称", "容量", "ヘルメット", "収納の目安"], rows)
        + p("ヘルメット収納数はメーカー公表の目安です。XL サイズやバイザー付きのモデルは入らないことがあります。")
        + links([("容量の選び方", "/guide/top-case-size"), ("トップケース全モデル", "/top-cases"), ("サイドケース全モデル", "/side-cases")]))
    body += section("Models", "ヘルメット2個が入るモデル", '<div class="mt-6">%s</div>' % grid(two), "pb-10")
    body += section("Models", "ヘルメット1個が入るモデル", '<div class="mt-6">%s</div>' % grid(one), "pb-14 md:pb-20")
    body += section("FAQ", "よくあるご質問", '<div class="mt-6 max-w-[860px]">%s</div>' % faq_html(faq), "pb-16 md:pb-24")
    page(path, "ヘルメットが入るトップケース・サイドケース｜フルフェイス2個・1個の収納数別一覧 — SHAD JAPAN",
         "バイク用トップケース・サイドケースをヘルメット収納数別に一覧。フルフェイス2個が入る大容量モデル、フルフェイス1個、ジェット1個の軽量モデル。各モデルの収納目安と容量、フルフェイスが入る容量の目安を解説。SHAD日本公式サイト。",
         body, [crumbs_ld(path, name), itemlist_ld("ヘルメットが入る SHAD ケース", two + one), faq_ld(faq)], "/img/products/sh58x/off_helmets.webp")

def build_tank_bags():
    path = "/tank-bags"; name = "タンクバッグ"
    click = [c for c in by_cap(TANK, desc=False) if "click" in tags(c)]
    std = [c for c in click if c in ("E02C", "E03C", "E09C", "E09CM")]
    pro = [c for c in click if c in ("E03CL", "E09CL")]
    terra = [c for c in click if c in ("TR15CL", "TR10")]
    uni = [c for c in by_cap(TANK, desc=False) if "click" not in tags(c)]
    LOCKS = {"E02C": "—", "E03C": "—", "E09C": "—", "E09CM": "—", "E03CL": "キーロック＋ファスナーロック", "E09CL": "キーロック＋ファスナーロック", "TR15CL": "キーロック", "TR10": "キーロック", "E04": "—"}
    EXTRA = {"E03CL": "容量拡張 3→4L", "E09CL": "容量拡張 5→8L", "E09CM": "約8cm 前方のミドルポジション", "TR10": "防水 IPX5", "TR15CL": "TERRA デザイン", "E04": "ユニバーサルタンクベースで固定（クリックシステム不要）"}
    rows = [(("<a href='/product/%s' class='text-shad font-semibold'>%s</a>" % (c.lower(), c)), esc((C.get(c) or {}).get("jp", "")), esc(v0(c).get("capacity") or ""), esc(LOCKS.get(c, "—")), esc(EXTRA.get(c, "")), esc(price(c))) for c in click + uni]
    faq = [
        ("クリックシステムとは何ですか？", "<p>タンクキャップのボルトに車種専用のアタッチメント（タンクリング）を共締めし、そこにバッグ側の受け部をはめ込む SHAD の取付方式です。ワンタッチで着脱でき、磁石や吸盤を使わないので塗装を傷めません。給油のたびに外す手間が数秒で済みます。</p>"),
        ("バッグだけ買えば取り付けられますか？", "<p>クリックシステムのバッグは、車種ごとに形が違う<b>クリックシステム フィッティングキット（別売）</b>が必要です。お使いの車種に合うキットは<a href='/fitment'>適合検索</a>で確認できます。E04 は付属のユニバーサルタンクベースで固定するので、キットは不要です。</p>"),
        ("雨に濡れても大丈夫ですか？", "<p>TR10CL は IPX5 相当の防水仕様です。そのほかのモデルは防水ではないため、付属のレインカバーを掛けてください。PRO モデルのスマートフォン用ポケットは防水を考慮していますが完全防水ではありません。</p>"),
        ("スマートフォンは操作できますか？", "<p>上面に透明窓を備えたモデルは、収納したままタッチ操作ができます。使えるかどうかは機種や保護フィルムによるため、商品ページの仕様をご確認ください。</p>"),
        ("タンクに傷はつきませんか？", "<p>アタッチメントは金属製と樹脂製があり、車種に合わせて使い分けます。バッグの底が当たる位置が気になる場合は、市販のタンク用プロテクションシートの併用をおすすめします。</p>"),
    ]
    body = hero("Tank Bags", "バイク用タンクバッグ", "地図、スマホ、財布。走りながら取り出したいものは、タンクの上に。SHAD のタンクバッグは、車種専用のアタッチメントにワンタッチで着脱できるクリックシステムが中心。3L のミニから、鍵と防水を備えた TERRA の 13L まで %d モデル。" % len(TANK), "/img/products/cards/tr15cl.webp")
    body += section("Click System", "1秒で着脱。磁石を使わない固定方式。",
        p("クリックシステムは、タンクキャップを留めているボルトに車種専用のアタッチメントを共締めし、そこにバッグをはめ込む方式です。給油のときはバッグをつまんで持ち上げるだけ。磁石や吸盤ではないので塗装を傷めず、走行中にずれることもありません。アタッチメントはキャップの見た目を損なわない小さなリングで、バッグを外した状態でも目立ちません。")
        + ul(["<b>着脱は1秒</b>：工具もストラップも不要。給油・駐車のたびのストレスがなくなります。", "<b>車種専用</b>：ボルトの配置に合わせたアタッチメントを使うため、確実に固定できます。対応車種は<a href='/fitment' class='text-shad'>適合検索</a>で。", "<b>塗装にやさしい</b>：磁石・吸盤を使わないので、タンクに跡が残りません。"])
        + links([("フィッティングキットの仕組み", "/fitting-kits"), ("車種から適合を探す", "/fitment")]))
    body += section("How to choose", "タンクバッグの選び方", table(["モデル", "名称", "容量", "ロック", "特長", "定価（税込）"], rows)
        + p("容量は、スマホと財布なら 3L、レインウェアや補給食まで入れるなら 5L 以上が目安です。駐車中にバッグを置いて離れることが多いなら、キーロック付きの PRO（E03CL／E09CL）か TERRA（TR15CL／TR10CL）を。雨の日も使うなら防水の TR10CL が安心です。E09CM はタンクの手前側に座るライダー向けに、通常より約8cm 前方に付くモデルです。"), "pb-6")
    body += section("Lineup", "全モデル", group("クリックシステム スタンダード", "ワンタッチ着脱の基本モデル", std) + group("クリックシステム PRO", "キーロック＋ファスナーロック、容量拡張", pro) + group("TERRA クリックシステム", "キーロック、TR10CL は防水 IPX5", terra) + group("ユニバーサル", "タンクベースで固定（キット不要）", uni), "pb-14 md:pb-20")
    body += section("FAQ", "よくあるご質問", '<div class="mt-6 max-w-[860px]">%s</div>' % faq_html(faq), "pb-16 md:pb-24")
    page(path, "バイク用タンクバッグ｜クリックシステムで1秒着脱・キーロック・防水 — SHAD JAPAN",
         "バイク用タンクバッグ%dモデル。車種専用アタッチメントにワンタッチで着脱できるクリックシステム、キーロック付きのPRO、防水IPX5のTERRA TR10CL、キット不要のユニバーサルE04。容量・ロック・特長・定価の一覧と選び方。" % len(TANK),
         body, [crumbs_ld(path, name), itemlist_ld("SHAD タンクバッグ", click + uni), faq_ld(faq)], "/img/products/cards/tr15cl.webp")


# ---------- SHAD LOCKS（スクーター用ハンドルバーロック）：本体＋車種専用キット一覧 ----------
import csv as _csv
CSV_PATH = os.path.join(ROOT, "data-source", "ItemList_SHAD.csv")
LOCK_LEN = {"203": "38cm", "205": "44cm", "207": "49cm"}   # 対応SHADロック C0S2xxH → 長さ（本国：size3/5/7）
MAKER_FIX = {"VOGE": "Voge", "PEUGEOT": "Peugeot", "Vespa": "PIAGGIO（Vespa）"}
MAKER_ORDER = ["ホンダ", "ヤマハ", "スズキ", "BMW", "PIAGGIO", "PIAGGIO（Vespa）", "Aprilia", "KYMCO", "SYM", "QJ Motor", "Voge", "ZONTES", "Peugeot"]
def lock_kits():
    if not os.path.exists(CSV_PATH):
        return []
    rows = list(_csv.DictReader(open(CSV_PATH, encoding="cp932", newline="")))
    out = []
    for r in rows:
        if "ロックフィッティングキット" not in r["商品名"] or r["CJ廃番"] == "1" or r["商品ステータスコード"].startswith("DC") or r.get("Web非表示") == "1":
            continue
        codes = sorted(set(re.findall(r"C0S(20[357])H", r.get("仕様") or "")))
        mk = MAKER_FIX.get(r["対応メーカー"], r["対応メーカー"])
        out.append({"cj": r["品番"], "maker": mk, "name": r["商品名"].replace("SHADロックフィッティングキット ", ""),
                    "bikes": r["代表適合車種"].replace("\n", " ").replace("｜", "／"), "len": "／".join(LOCK_LEN.get(c, c) for c in codes) or "—",
                    "price": r.get("希望小売価格(税込)") or ""})
    out.sort(key=lambda k: (MAKER_ORDER.index(k["maker"]) if k["maker"] in MAKER_ORDER else 99, k["name"]))
    return out

def build_locks():
    path = "/locks"; name = "SHAD LOCKS（ハンドルバーロック）"
    kits = lock_kits()
    lock = P.get("LOCK"); pr = price("LOCK") if lock else ""
    by_mk = []
    for k in kits:
        if not by_mk or by_mk[-1][0] != k["maker"]:
            by_mk.append((k["maker"], []))
        by_mk[-1][1].append(k)
    def kit_rows(ks):
        return table(["車種（年式）", "キット品番", "対応するロック本体", "キット定価（税込）"],
                     [(esc(k["name"]), "<a href='https://www.customjapan.net/i/%s' target='_blank' rel='noopener' class='text-shad font-semibold'>%s</a>" % (k["cj"], k["cj"]), esc(k["len"]), ("¥{:,}".format(int(k["price"])) if k["price"].isdigit() else esc(k["price"]))) for k in ks])
    kits_html = "".join('<div class="mt-8"><h3 class="font-disp font-semibold text-[22px] tracking-[.06em] uppercase">%s<span class="font-sans normal-case tracking-normal text-[13px] text-neutral-500 font-normal ml-3">%d 車種</span></h3>%s</div>' % (esc(mk), len(ks), kit_rows(ks)) for mk, ks in by_mk)
    faq = [
        ("ロック本体だけで取り付けられますか？", "<p>いいえ。本体を固定するブラケットは車種ごとに形が違うため、<b>車種専用の SHAD ロックフィッティングキット（別売）</b>が必要です。キットには本体は付属しません。</p>"),
        ("38cm と 44cm のどちらを選べばよいですか？", "<p>車種ごとにキットが指定するロック本体が決まっています。上の表の「対応するロック本体」をご確認ください。49cm（本国 サイズ7）が指定されている車種は、日本では本体の取り扱いがないため販売店にご相談ください。</p>"),
        ("ヘルメットも固定できますか？", "<p>はい。ハンドルとシートの間に掛けたロックに、ヘルメットの D リングを通して固定できます。ケースを付けていないスクーターでも、ヘルメットを車体に残して離れられます。</p>"),
        ("鍵をなくしたら？", "<p>ロック本体にはリバーシブルキーが付属します。紛失に備えてスペアキーは別の場所に保管してください。シリンダーは 30,000 回の開閉に耐える耐久試験をクリアしています。</p>"),
        ("他社のロックやブラケットと組み合わせられますか？", "<p>他社製品との互換性は確認していません。取り付けは専門知識のある販売店へのご依頼をおすすめします。</p>"),
    ]
    body = hero("SHAD Locks", "スクーター用ハンドルバーロック", "降りて数秒、屈まず、手を汚さずに。ハンドルとシートをつないで車体を固定し、ヘルメットも一緒にロックできる SHAD のスクーター専用ハンドルバーロック。使わないときはシート下のブラケットに収納しておけます。", "/img/locks/hero.webp")
    body += section("How it works", "ハンドルとシートを、1本でつなぐ。",
        p("ロック本体は車種専用ブラケットでシート下に収納しておき、停めたら引き出してハンドルバーに掛けるだけ。ハンドルが切れなくなるので車体を動かせず、ディスクロックのように屈んで地面近くで作業する必要もありません。鍵穴は 360° 回転するヘッドにあり、どの向きからでも施錠・解錠できます。")
        + '<div class="grid sm:grid-cols-3 gap-4 mt-8 max-w-[1000px]">%s</div>' % "".join('<figure class="rounded-[14px] overflow-hidden bg-mist"><img src="%s" alt="%s" loading="lazy" class="w-full aspect-square object-cover"><figcaption class="text-[13px] text-neutral-600 px-4 py-3 leading-[1.7]">%s</figcaption></figure>' % (src, esc(alt), esc(cap)) for src, alt, cap in (("/img/locks/use_mounted.webp", "ハンドルとシートをつないだ状態", "ハンドルとシートをつないで固定。ハンドルが切れないので車体を動かせません"), ("/img/locks/use_head.webp", "360°回転するロックヘッド", "360°回転ヘッド。鍵穴の向きを気にせず、立ったまま施錠できます"), ("/img/locks/use_helmet.webp", "ヘルメットをロックに掛けた状態", "ヘルメットの D リングを通せば、ヘルメットも車体に残せます")))
        + ul(["<b>5mm 径の亜鉛メッキスチールケーブル</b>をボールジョイントで覆った構造。切断や曲げに強く、車体を傷つけません。", "<b>30,000 回の開閉</b>に耐える高品質シリンダーと、表裏どちらでも差せる<b>リバーシブルキー</b>。", "本体は <b>38cm（シリーズ2 レギュラー）と 44cm</b> の 2 サイズ。どちらを使うかは車種専用キットで決まります。", "設計は 100% ヨーロッパ（SHAD／スペイン）。REACH 規制に適合。"])
        + links([("ロック本体の商品ページ", "/product/lock"), ("フィッティングキットの考え方", "/fitting-kits#locks")]))
    if lock:
        body += section("Product", "ロック本体", '<div class="mt-6 max-w-[520px]">%s</div>' % card("LOCK") + p("定価 %s（税込）。38cm・44cm とも同価格です。" % pr if pr else ""), "pb-6")
    body += section("Fitting Kits", "車種専用フィッティングキット（%d 車種）" % len(kits),
        p("SHAD ロックは、車種ごとに専用のブラケット（フィッティングキット）でシート下に取り付けます。お使いの車種の行にある「対応するロック本体」の長さを選んでください。年式はキット登録時点のもので、同じ車名でも年式が外れる場合は適合しないことがあります。")
        + kits_html
        + p("表にない車種は順次追加されます。適合が不明な場合は<a href='/contact' class='text-shad underline underline-offset-4'>お問い合わせ</a>ください。"), "pb-14 md:pb-20")
    body += section("FAQ", "よくあるご質問", '<div class="mt-6 max-w-[860px]">%s</div>' % faq_html(faq), "pb-16 md:pb-24")
    page(path, "SHAD LOCKS｜スクーター用ハンドルバーロック・車種専用フィッティングキット — SHAD JAPAN",
         "スクーターのハンドルとシートをつないで固定し、ヘルメットも一緒にロックできる SHAD ハンドルバーロック。5mm 亜鉛メッキケーブル、360°回転ヘッド、30,000回耐久シリンダー。38cm／44cm と、%d 車種の専用フィッティングキット一覧。" % len(kits),
         body, [crumbs_ld(path, name), faq_ld(faq)], "/img/locks/hero.webp")

def main():
    for f in (build_top_cases, build_side_cases, build_bags, build_tank_bags, build_size_guide, build_waterproof, build_helmet, build_locks):
        f()
    print("ランディングページ 8 ページを生成（/top-cases /side-cases /bags /tank-bags /guide/top-case-size /waterproof /helmet-storage /locks）")

if __name__ == "__main__":
    main()
