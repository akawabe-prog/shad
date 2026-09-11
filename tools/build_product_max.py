#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD — 商品ページを「MAXテンプレート」に組み替える
=============================================================================
既存の商品ページ（従来レイアウト／MAXレイアウトどちらでも）から、
価格・カラー・スペック・説明・ストーリー・FAQ・適合・Same Series を取り出し、
設定JSONで指定した素材（動画・画像・コピー）を当てて MAX レイアウトに組み替えます。

    python3 tools/build_product_max.py tools/product_max/tr41.json

■ 構成（TR46 で確定した並び）
    ①看板 → ②アンカーナビ（1行）＋右側Index → ③INDEX → ④SPEC/保証/FAQ（アコーディオン）
    → ⑤HERO映像 → ⑥イメージ画像（2枚組） → ⑦特徴（ストーリー3本＋構造図） → ⑧縦型映像
    → ⑨ギャラリー → ⑩適合 → ⑪関連商品

■ 設定JSONの項目
    code            "TR41"
    catch           メインキャッチ（省略時は現ページのものを維持）
    main_img / thumbs           看板の初期画像とサムネイル（/img/… のパス）
    gallery_override            { 品番: [画像…] } カラー選択時の看板画像（purchase.js が参照）
    hero            { video_pc, video_sp, poster_pc, poster_sp, kick, heading（<br>可）, sub, film, film_label }
                    film を省略すると「フル映像を見る」ボタンは出ません
    visual_pair     [ {src, alt, caption}, {src, alt, caption} ]   省略可
    features        { en, heading }  特徴セクションの見出し
    diagrams        [ {img, alt, b, span} … ]  構造図。空なら出さない
    reels           [ {src, poster, en, jp} … ]  縦型映像。空ならセクションごと出さない
    gallery         [ {src, cls} … ]  cls は "is-tall is-wide" など（省略可）
    userguide       取扱説明書PDFのパス（省略時は /docs/<code小文字>_userguide.pdf があれば使う）

■ 注意
    ・FAQ は <!-- FAQ:START/END --> のマーカーごと移設するので、build_faq.py の再実行に影響しません
    ・「Spec」「Same Series」の見出しは purchase.js の差し込み位置に使われるため必ず残します
    ・実行のたびに現ページから部品を取り直すので、何度でも組み直せます
=============================================================================
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")


def esc(s):
    return (s or "").replace("&", "&amp;").replace('"', "&quot;")


def grab(s, a, b):
    m = re.search(a + r".*?" + b, s, re.S)
    if not m:
        raise SystemExit("抽出できません: %s … %s" % (a, b))
    return m.group(0)


def extract(s):
    """現ページから使い回す部品を取り出す（従来レイアウト／MAXレイアウトの両対応）"""
    is_max = 'id="pdTop"' in s
    parts = {}
    parts["faq"] = grab(s, r"<!-- FAQ:START", r"<!-- FAQ:END -->")
    parts["fitment"] = grab(s, r'<section id="fitment"', r"</section>")
    m = re.search(r'(<div class="grid grid-cols-2 sm:grid-cols-3 gap-4 sm:gap-5 mt-6">.*?</a></div>)', s, re.S)
    parts["same_grid"] = m.group(1)
    if is_max:
        parts["spec_rows"] = re.search(r'<table class="pd-spec">(.*?)</table>', s, re.S).group(1)
        body = re.search(r'<table class="pd-spec">.*?</table></div>\s*<div><p class="text-\[14.5px\] leading-\[2\]">(.*?)</p><p class="pd-note">(.*?)</p>', s, re.S)
        parts["desc"], parts["notes"] = body.group(1), body.group(2)
        parts["story_inner"] = re.search(r'<div class="lp-story">(.*?)</div>\s*(?:<div class="pd-diagrams|</div>\s*</section>)', s, re.S).group(1)
        parts["warranty"] = re.search(r'1年保証</p>\s*<p[^>]*>(.*?)</p>', s, re.S).group(1)
        parts["info_col"] = re.search(r'<main id="pdTop"[^>]*>\s*<div>.*?</div>\s*(<div>.*?)</main>', s, re.S).group(1)
    else:
        rows = re.search(r'(<tr class="border-b border-black/10">.*?)</table>', s, re.S).group(1)
        rows = re.sub(r'<tr class="border-b border-black/10">', "<tr>", rows)
        parts["spec_rows"] = re.sub(r'<t([hd]) class="[^"]*">', r"<t\1>", rows)
        parts["desc"] = re.search(r'<h2 class="sec-ttl sec-ttl-quiet">Description</h2>\s*<p[^>]*>(.*?)</p>', s, re.S).group(1)
        m = re.search(r'<p class="text-\[12px\][^>]*>(.*?)</p>', s, re.S)
        parts["notes"] = m.group(1) if m else ""
        story = grab(s, r'<section class="lp-story">', r"</section>")
        parts["story_inner"] = re.search(r'<div class="max-w-site mx-auto px-7">(.*)</div></section>$', story, re.S).group(1)
        parts["warranty"] = re.search(r'<div class="warranty-body">(.*?)</div>', s, re.S).group(1)
        parts["info_col"] = re.search(r'<main class="max-w-site mx-auto px-7 py-8 grid md:grid-cols-2 gap-10 items-start">\s*<div>.*?</div>\s*(<div>.*?)</main>', s, re.S).group(1)
    return parts


NAV_ITEMS = [("#spec", "01", "スペック"), ("#faq", "02", "FAQ"), ("#movie", "03", "ムービー"),
             ("#feature", "04", "特徴"), ("#gallery", "05", "ギャラリー"),
             ("#fitment", "06", "適合車種"), ("#related", "07", "関連商品")]
INDEX_ITEMS = [("#spec", "01", "スペック・保証", "Specifications"), ("#faq", "02", "よくあるご質問", "FAQ"),
               ("#movie", "03", "ムービー", "Movie"), ("#feature", "04", "商品の特徴", "Features"),
               ("#gallery", "05", "ギャラリー", "Gallery"), ("#fitment", "06", "装着できる車種", "Fitment"),
               ("#related", "07", "関連商品", "Related")]


def render(cfg, P):
    code = cfg["code"]
    name_jp = cfg.get("name_jp", "")
    hero = cfg["hero"]
    thumbs = "".join(
        '<button class="g-thumb%s" data-src="%s"><img src="%s" alt=""></button>'
        % (" on" if i == 0 else "", t, t) for i, t in enumerate(cfg["thumbs"]))
    nav = "".join('    <a href="%s" class="pd-nav-a"><small>%s</small>%s</a>\n' % x for x in NAV_ITEMS)
    side = "".join('  <a href="%s" class="pd-side-a"><small>%s</small><span>%s</span></a>\n' % x for x in NAV_ITEMS)
    index = "".join(
        '      <a href="%s"><span class="pd-index-num">%s</span><span><span class="pd-index-jp">%s</span>'
        '<span class="pd-index-en">%s</span></span></a>\n' % x for x in INDEX_ITEMS)
    guide = cfg.get("userguide") or ("/docs/%s_userguide.pdf" % code.lower())
    guide_btn = ('<a href="%s" target="_blank" class="btn bg-ink text-white hover:bg-black !py-3 !px-6 !text-[14px]">'
                 '<i class="ti ti-file-type-pdf"></i>ユーザーガイド（PDF）</a>' % guide) \
        if os.path.exists(os.path.join(SITE, guide.lstrip("/"))) else ""
    play = ('<button type="button" class="pd-play" data-video="%s" data-poster="%s">'
            '<i class="ti ti-player-play-filled"></i>%s</button>'
            % (hero["film"], hero.get("poster_film", hero.get("poster_pc", "")), hero.get("film_label", "フル映像を見る"))) if hero.get("film") else ""
    visual = ""
    if cfg.get("visual_pair"):
        figs = "".join('    <figure><img src="%s" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>\n'
                       % (v["src"], esc(v.get("alt")), v.get("caption", "")) for v in cfg["visual_pair"])
        visual = ('<!-- ===== ⑥ イメージ画像 ===== -->\n<section class="pd-visual pt-1.5" data-reveal>\n'
                  '  <div class="pd-visual-pair">\n%s  </div>\n</section>\n\n' % figs)
    diagrams = ""
    if cfg.get("diagrams"):
        diagrams = '    <div class="pd-diagrams mt-10" data-reveal>\n' + "".join(
            '      <div class="pd-diagram"><img src="%s" alt="%s" loading="lazy"><div class="pd-diagram-cap"><b>%s</b><span>%s</span></div></div>\n'
            % (d["img"], esc(d.get("alt")), d["b"], d.get("span", "")) for d in cfg["diagrams"]) + "    </div>\n"
    reels = ""
    if cfg.get("reels"):
        items = "".join(
            '      <div class="pd-reel"><div class="pd-reel-v"><video src="%s" poster="%s" muted loop playsinline preload="none" data-inview></video></div>'
            '<p class="pd-reel-cap"><b>%s</b>%s</p></div>\n' % (r["src"], r.get("poster", ""), r["en"], r["jp"]) for r in cfg["reels"])
        reels = ('<!-- ===== ⑧ 縦型映像 ===== -->\n<section class="pd-reels">\n  <div class="max-w-site mx-auto px-7">\n'
                 '    <div class="pd-sec-head !mb-0" data-reveal>\n      <div><p class="pd-sec-en">Reels</p><h2 class="pd-sec-h is-disp">%s in motion</h2></div>\n'
                 '      <a href="/movies" class="font-disp text-[14px] tracking-[.16em] uppercase text-white/55 inline-flex items-center gap-2 hover:text-white transition shrink-0">View All <i class="ti ti-arrow-right"></i></a>\n'
                 '    </div>\n    <div class="pd-reel-row">\n%s    </div>\n  </div>\n</section>\n\n' % (code, items))
    gallery = "".join('      <figure%s><img src="%s" alt="" loading="lazy"></figure>\n'
                      % ((' class="%s"' % g["cls"]) if g.get("cls") else "", g["src"]) for g in cfg["gallery"])
    feat = cfg.get("features", {})
    sp_poster = hero.get("poster_sp") or hero.get("poster_pc", "")
    ov = json.dumps(cfg.get("gallery_override", {}), ensure_ascii=False, indent=2)

    return f'''<!-- =====================================================================
     商品ページ MAXテンプレート（tools/build_product_max.py で生成）
     ①看板 → ②アンカーナビ → ③INDEX → ④SPEC/保証/FAQ → ⑤HERO映像 → ⑥イメージ画像
     → ⑦特徴 → ⑧縦型映像 → ⑨ギャラリー → ⑩適合 → ⑪関連商品
     ===================================================================== -->
<div class="max-w-site mx-auto px-7 pt-6">
  <a href="/products" class="inline-flex items-center gap-2 text-[13px] text-neutral-500 hover:text-shad transition"><i class="ti ti-arrow-left"></i>製品一覧</a>
</div>

<!-- ===== ① 看板（商品ビジュアル＋購入情報） ===== -->
<main id="pdTop" class="max-w-site mx-auto px-7 py-8 grid md:grid-cols-2 gap-10 items-start">
  <div>
    <div class="g-main"><img id="gMain" src="{cfg["main_img"]}" alt="{esc(code + " " + name_jp)}"></div>
    <div class="flex flex-wrap gap-2.5 mt-3">{thumbs}</div>
  </div>
  {P["info_col"]}
</main>
<script>
/* カラー選択で看板画像を切り替える（purchase.js が参照） */
window.SHAD_GALLERY = {ov};
</script>

<!-- ===== ② アンカーナビ（1行固定。スクロールで見えなくなると右側の pd-side に切り替わる） ===== -->
<nav class="pd-nav" id="pdNav" aria-label="ページ内ナビゲーション">
  <div class="pd-nav-in">
{nav}  </div>
</nav>
<nav class="pd-side" id="pdSide" aria-label="ページ内Index">
  <p class="pd-side-lb">Index</p>
{side}</nav>

<!-- ===== ③ INDEX ===== -->
<section class="pd-index py-12">
  <div class="max-w-site mx-auto px-7">
    <p class="pd-index-lb">Index</p>
    <div class="pd-index-list">
{index}    </div>
  </div>
</section>

<!-- ===== ④ SPEC / 保証 / FAQ（アコーディオン） ===== -->
<section id="spec" class="scroll-mt-[132px] max-w-site mx-auto px-7 pt-14 pb-4">
  <details class="pd-acc" open>
    <summary>Specifications<small>スペック・商品説明</small><span class="pd-acc-mark"><i class="ti ti-plus"></i></span></summary>
    <div class="pd-acc-body grid md:grid-cols-2 gap-10">
      <div><h2 class="sr-only">Spec</h2><table class="pd-spec">{P["spec_rows"]}</table></div>
      <div><p class="text-[14.5px] leading-[2]">{P["desc"]}</p><p class="pd-note">{P["notes"]}</p></div>
    </div>
  </details>
  <details class="pd-acc">
    <summary>Warranty &amp; Support<small>保証・取付サポート</small><span class="pd-acc-mark"><i class="ti ti-plus"></i></span></summary>
    <div class="pd-acc-body grid md:grid-cols-2 gap-10">
      <div>
        <p class="font-bold text-[15px]"><i class="ti ti-shield-check text-shad mr-1.5"></i>1年保証</p>
        <p class="text-[13.5px] leading-[1.95] text-neutral-600 mt-2">{P["warranty"]}</p>
      </div>
      <div>
        <p class="font-bold text-[15px]"><i class="ti ti-tool text-shad mr-1.5"></i>取り付けは、説明書とプロにお任せ。</p>
        <p class="text-[13.5px] leading-[1.95] text-neutral-600 mt-2">公式ユーザーガイドで取付手順を確認できます。装着は適合確認のうえ、最寄りの取扱店でも承ります。</p>
        <div class="flex flex-wrap gap-3 mt-4">
          {guide_btn}
          <a href="/store-locator" class="btn border border-black/25 text-ink hover:bg-mist !py-3 !px-6 !text-[14px]">取扱店を探す</a>
        </div>
      </div>
    </div>
  </details>
  <details class="pd-acc" id="faqAcc">
    <summary>FAQ<small>よくあるご質問</small><span class="pd-acc-mark"><i class="ti ti-plus"></i></span></summary>
    <div class="pd-acc-body">
{P["faq"]}
    </div>
  </details>
</section>

<!-- ===== ⑤ HERO映像（フルブリード） ===== -->
<section id="movie" class="pd-hero scroll-mt-[132px] mt-14" data-reveal>
  <video id="pdHeroVideo" autoplay muted loop playsinline preload="metadata" poster="{hero.get("poster_pc","")}"
         data-src-pc="{hero["video_pc"]}" data-src-sp="{hero.get("video_sp") or hero["video_pc"]}" data-poster-sp="{sp_poster}"></video>
  <div class="pd-hero-shade"></div>
  <div class="pd-hero-in">
    <p class="lp-kick">{hero.get("kick","Movie")}</p>
    <h2 class="pd-hero-h is-jp">{hero["heading"]}</h2>
    <p class="pd-hero-sub">{hero.get("sub","")}</p>
    {play}
  </div>
</section>

{visual}<!-- ===== ⑦ 商品の特徴 ===== -->
<section id="feature" class="scroll-mt-[132px] pd-sec">
  <div class="max-w-site mx-auto px-7">
    <div class="pd-sec-head" data-reveal>
      <div><p class="pd-sec-en">{feat.get("en","Features")}</p><h2 class="pd-sec-h">{feat.get("heading","")}</h2></div>
      <a href="/engineered-for-riding" class="font-disp text-[14px] tracking-[.16em] uppercase text-neutral-500 inline-flex items-center gap-2 hover:text-shad transition shrink-0">SHAD Technology <i class="ti ti-arrow-right"></i></a>
    </div>
    <div class="lp-story">{P["story_inner"]}</div>
{diagrams}  </div>
</section>

{reels}<!-- ===== ⑨ ギャラリー ===== -->
<section id="gallery" class="scroll-mt-[132px] pd-sec">
  <div class="max-w-site mx-auto px-7">
    <div class="pd-sec-head" data-reveal><div><p class="pd-sec-en">Gallery</p><h2 class="pd-sec-h is-disp">{code} on the road</h2></div></div>
    <div class="pd-gallery" data-reveal>
{gallery}    </div>
  </div>
</section>

<!-- ===== ⑩ 適合 ===== -->
{P["fitment"]}

<!-- ===== ⑪ 関連商品（他商品への誘導） ===== -->
<section id="related" class="scroll-mt-[132px] bg-mist py-12 mt-8">
  <div class="max-w-site mx-auto px-7">
    <h2 class="sec-ttl sec-ttl-quiet">Same Series</h2>
    {P["same_grid"]}
    <div class="pd-cta" data-reveal>
      <a href="/terra"><span><b>TERRAシリーズをすべて見る</b><span>トップケース・サイドケース・バッグのラインアップ</span></span><i class="ti ti-arrow-right"></i></a>
      <a href="/fitment"><span><b>車種から探す</b><span>あなたのバイクに合うケースと必要なキットを確認</span></span><i class="ti ti-search"></i></a>
      <a href="/fitting-kits"><span><b>フィッティングキットとは</b><span>装着の仕組みとキットの種類</span></span><i class="ti ti-tool"></i></a>
      <a href="/products"><span><b>すべての製品</b><span>カテゴリ・容量から選ぶ</span></span><i class="ti ti-layout-grid"></i></a>
    </div>
  </div>
</section>

<script>
/* ---- MAXテンプレート共通の小さな挙動 ---- */
(function(){{
  /* ② アンカーナビ／右側Index：現在地のハイライトと、Indexの表示切替 */
  var links=[].slice.call(document.querySelectorAll(".pd-nav-a, .pd-side-a")), secs=[];
  var navBar=document.getElementById("pdNav"), side=document.getElementById("pdSide");
  links.forEach(function(a){{ var t=document.querySelector(a.getAttribute("href")); if(t) secs.push({{a:a,sec:t}}); }});
  function sync(){{
    var line=160, cur=null;
    secs.forEach(function(o){{ var r=o.sec.getBoundingClientRect(); if(r.top<=line && r.bottom>line) cur=o.sec; }});
    links.forEach(function(a){{ a.classList.toggle("is-current", !!cur && document.querySelector(a.getAttribute("href"))===cur); }});
    if(navBar && side){{
      var gone=navBar.getBoundingClientRect().bottom<0;
      var foot=document.querySelector("footer"); var nearFoot=foot && foot.getBoundingClientRect().top<window.innerHeight*0.6;
      side.classList.toggle("is-on", gone && !nearFoot);
    }}
  }}
  var last=0, waiting=false;
  window.addEventListener("scroll",function(){{ var n=Date.now(); if(n-last>120){{last=n;sync();}} else if(!waiting){{waiting=true;setTimeout(function(){{waiting=false;sync();}},120);}} }},{{passive:true}});
  window.addEventListener("resize",sync); sync();
  window.__pdNavSync=sync;

  /* アンカーで FAQ に飛んだとき、閉じたアコーディオンを開く */
  function openFor(hash){{ if(!hash||hash.length<2) return; var t=document.querySelector(hash); if(!t) return;
    var d=t.closest("details"); if(d && !d.open) d.open=true; }}
  document.addEventListener("click",function(e){{ var a=e.target.closest('a[href^="#"]'); if(a) openFor(a.getAttribute("href")); }});
  openFor(location.hash);

  /* ⑤ HERO映像：スマホは縦型を使う */
  var v=document.getElementById("pdHeroVideo");
  if(v){{ var sp=window.matchMedia("(max-width:760px)").matches;
    v.src=v.getAttribute(sp?"data-src-sp":"data-src-pc");
    if(sp && v.getAttribute("data-poster-sp")) v.poster=v.getAttribute("data-poster-sp");
    v.play().catch(function(){{}}); }}

  /* ⑧ 縦型映像：画面に入ったら再生、外れたら停止 */
  var vids=[].slice.call(document.querySelectorAll("video[data-inview]"));
  if("IntersectionObserver" in window && vids.length){{
    var io=new IntersectionObserver(function(es){{ es.forEach(function(e){{ e.isIntersecting ? e.target.play().catch(function(){{}}) : e.target.pause(); }}); }},{{threshold:.35}});
    vids.forEach(function(x){{ io.observe(x); }});
  }}
}})();
</script>

'''


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    code = cfg["code"]
    path = os.path.join(SITE, "product", code.lower() + ".html")
    s = open(path, encoding="utf-8").read()
    P = extract(s)

    # メインキャッチ（本文＋meta 3箇所）
    if cfg.get("catch"):
        m = re.search(r'<p class="text-\[17px\] font-bold mt-5 leading-relaxed">([^<]*)</p>', s)
        if m and m.group(1) != cfg["catch"]:
            s = s.replace(m.group(1), cfg["catch"])
            P["info_col"] = P["info_col"].replace(m.group(1), cfg["catch"])
    if "name_jp" not in cfg:
        m = re.search(r'<p class="text-\[15px\] text-neutral-500 mt-1.5">([^<]*)</p>', s)
        cfg["name_jp"] = m.group(1) if m else ""

    s = re.sub(r"\n<style>.*?</style>", "", s, count=1, flags=re.S)   # 看板系CSSは custom.css に集約済み
    a = s.index('<div class="max-w-site mx-auto px-7 pt-6">')
    b = s.index("<footer ")
    s = s[:a] + render(cfg, P) + s[b:]
    if "/js/main.js" not in s:
        s = s.replace('<script src="/js/nav.js"></script>', '<script src="/js/nav.js"></script>\n<script src="/js/main.js"></script>', 1)
    open(path, "w", encoding="utf-8").write(s)

    # 参照アセットの実在チェック
    miss = sorted(u for u in set(re.findall(r'(?:src|href|poster|data-src-pc|data-src-sp|data-poster-sp|data-video|data-poster)="(/(?:img|media|docs)/[^"#]+)"', s))
                  if not os.path.exists(os.path.join(SITE, u.lstrip("/"))))
    print("生成: site/product/%s.html（%d行）" % (code.lower(), s.count("\n")))
    print("  欠落アセット:", miss or "なし")
    for t in ("section", "div", "details", "video", "figure"):
        o, c = len(re.findall(r"<%s[\s>]" % t, s)), s.count("</%s>" % t)
        if o != c:
            print("  ⚠ タグ不整合 <%s> open=%d close=%d" % (t, o, c))


if __name__ == "__main__":
    main()
