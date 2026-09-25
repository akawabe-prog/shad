/* =========================================================
   SHAD JAPAN — news_article.js
   /news/article?id=<CMS記事ID>（または /news/cj-<id> で静的ページが無いとき）
   CJ の CMS API から記事1本を取得し、サイト内のレイアウトで表示する。
   ・本文は build_news.py の ArticleCleaner と同じ規則で整える
     （残すタグ・属性を限定、script等は捨てる、EC商品リンクは /product/<code> へ）
   ・このページは noindex。検索に出すのは fetch→build で生成した静的ページ側
   ========================================================= */
(function () {
  var root = document.getElementById("liveArticle");
  if (!root) return;
  var q = new URLSearchParams(location.search);
  var id = q.get("id") || ((location.pathname.match(/cj-(\d+)/) || [])[1]);
  /* 記事1本は標準の wp/v2 で取る（custom/v1 は include= を受け付けないため）。カテゴリ 480（90_SHAD）以外は表示しない */
  var API = "https://cms.customjapan.net/wp-json/wp/v2/posts/";
  var SHAD_CATEGORY = 480;
  var TAG_TO_CATEGORY = [["#出展", "Event"], ["#ニュース", "News"], ["#特集", "Feature"], ["#メディア", "Media"]];
  var KEEP = ["p", "h2", "h3", "h4", "ul", "ol", "li", "strong", "em", "b", "i", "br", "blockquote", "figure", "figcaption", "img", "a", "iframe", "table", "thead", "tbody", "tr", "th", "td", "small", "hr"];
  var DROP = ["script", "style", "button", "svg", "path", "noscript", "form", "input", "template"];
  var KEEP_ATTRS = { img: ["src", "alt", "width", "height"], a: ["href"], iframe: ["src", "width", "height", "title"] };

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function strip(s) { var d = document.createElement("div"); d.innerHTML = s || ""; return (d.textContent || "").replace(/\s*\[\s*…\s*\]\s*$/, "…").replace(/\s+/g, " ").trim(); }
  function jpDate(iso) { return (iso || "").slice(0, 10).replace(/-/g, "."); }
  function fail(msg) {
    root.innerHTML = '<div class="max-w-site mx-auto px-7 py-20 text-center"><p class="text-[15px] text-neutral-600">' + esc(msg) + '</p>'
      + '<a href="/shad/news" class="btn border border-black/15 bg-white hover:border-shad hover:text-shad mt-6"><i class="ti ti-list"></i>NEWS一覧へ</a></div>';
  }
  if (!id) { fail("記事が指定されていません。"); return; }

  /* 品番 → 型番（EC商品リンクを自サイトの商品ページに向ける） */
  function codeMap() {
    return Promise.all(["/shad/data/catalog/cards.json", "/shad/data/catalog/products.json"].map(function (u) { return fetch(u).then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; }); }))
      .then(function (rs) {
        var m = {};
        Object.keys(rs[0] || {}).forEach(function (c) { m[c.toUpperCase()] = c; });
        Object.keys(rs[1] || {}).forEach(function (c) { ((rs[1][c] || {}).variants || []).forEach(function (v) { if (v.cjCode) m[String(v.cjCode).toUpperCase()] = c; }); });
        return m;
      });
  }
  function fixHref(href, codes) {
    var m = /^https?:\/\/moto\.customjapan\.net\/i\/([A-Za-z0-9]+)\/?$/.exec(href || "");
    if (m) { var code = codes[m[1].toUpperCase()]; if (code) return { href: "/shad/product/" + code.toLowerCase(), ext: false }; }
    return { href: href || "", ext: /^https?:/.test(href || "") };
  }
  /* CJ の WordPress 本文を、当サイトで安全に表示できる形に */
  function clean(html, codes) {
    var src = document.createElement("div"); src.innerHTML = html || "";
    function walk(node, out) {
      node.childNodes.forEach(function (n) {
        if (n.nodeType === 3) { out.appendChild(document.createTextNode(n.nodeValue)); return; }
        if (n.nodeType !== 1) return;
        var tag = n.tagName.toLowerCase();
        if (DROP.indexOf(tag) >= 0) return;
        if (tag === "iframe" && !/^https:\/\/(www\.)?(youtube(-nocookie)?\.com|youtu\.be)\//.test(n.getAttribute("src") || "")) return;
        if (KEEP.indexOf(tag) < 0) { walk(n, out); return; }        // タグは外して中身だけ
        var el = document.createElement(tag);
        (KEEP_ATTRS[tag] || []).forEach(function (a) { var v = n.getAttribute(a); if (v != null) el.setAttribute(a, v); });
        if (tag === "a") { var f = fixHref(el.getAttribute("href"), codes); el.setAttribute("href", f.href); if (f.ext) { el.setAttribute("target", "_blank"); el.setAttribute("rel", "noopener"); } }
        if (tag === "img") { el.setAttribute("loading", "lazy"); if (/^https?:\/\/[^/]*customjapan\.net\//.test(el.getAttribute("src") || "")) {} }
        if (tag === "iframe") { el.setAttribute("loading", "lazy"); el.setAttribute("allowfullscreen", ""); }
        walk(n, el);
        if (["p", "li", "h2", "h3", "h4"].indexOf(tag) >= 0 && !el.textContent.trim() && !el.querySelector("img,iframe")) return;   // 空段落は捨てる
        out.appendChild(el);
      });
    }
    var out = document.createElement("div"); walk(src, out); return out.innerHTML;
  }

  Promise.all([fetch(API + encodeURIComponent(id) + "?_embed&_fields=id,date,title,excerpt,content,link,categories,_embedded").then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }), codeMap()])
    .then(function (rs) {
      var p = rs[0], codes = rs[1];
      if (!p || !p.id) { fail("記事が見つかりませんでした。"); return; }
      if ((p.categories || []).indexOf(SHAD_CATEGORY) < 0) { fail("この記事は SHAD JAPAN のニュース対象ではありません。"); return; }
      var terms = []; ((p._embedded || {})["wp:term"] || []).forEach(function (g) { (g || []).forEach(function (t) { if (t && t.taxonomy === "post_tag") terms.push(t.name || ""); }); });
      var tags = terms, cat = "Guide";
      for (var i = 0; i < TAG_TO_CATEGORY.length; i++) if (tags.indexOf(TAG_TO_CATEGORY[i][0]) >= 0) { cat = TAG_TO_CATEGORY[i][1]; break; }
      var fm = (p._embedded || {})["wp:featuredmedia"]; if (Array.isArray(fm)) fm = fm[0];
      var sizes = (fm && fm.media_details && fm.media_details.sizes) || {};
      var img = (sizes.large || sizes.full || sizes.medium_large || {}).source_url || (fm && fm.source_url) || "";
      var title = strip((p.title || {}).rendered), lead = strip((p.excerpt || {}).rendered), date = (p.date || "").slice(0, 10);
      var origin = "https://www.customjapan.net/a/moto/" + p.id;
      document.title = title + "｜NEWS｜SHAD JAPAN";
      var link = document.querySelector('link[rel="canonical"]'); if (link) link.setAttribute("href", origin);
      root.innerHTML =
        '<section class="bg-ink2 text-white pt-[54px] pb-[58px] md:pt-[70px] md:pb-[74px]"><div class="max-w-site mx-auto px-7">'
        + '<p class="flex items-center gap-3"><span class="w-9 h-px bg-shad"></span><span class="font-disp text-[12px] tracking-[.26em] uppercase text-shad">News</span></p>'
        + '<h1 class="font-disp font-semibold text-[clamp(30px,5.4vw,54px)] leading-[1.06] tracking-[.03em] uppercase mt-3">' + esc(title) + '</h1>'
        + '<p class="flex items-center gap-3 mt-5 text-white/70"><span class="news-cat">' + esc(cat) + '</span><span class="font-disp text-[14px] tracking-[.16em]">' + jpDate(date) + '</span></p>'
        + '</div></section>'
        + '<div class="max-w-site mx-auto px-7 pt-7"><a href="/shad/news" class="inline-flex items-center gap-2 text-[13px] text-neutral-500 hover:text-shad transition"><i class="ti ti-arrow-left"></i>NEWS一覧</a></div>'
        + '<main class="pb-[70px]">' + (img ? '<div class="news-hero-img"><img src="' + esc(img) + '" alt="' + esc(title) + '"></div>' : "")
        + '<article class="news-body"><p class="news-lead">' + esc(lead) + '</p>' + clean((p.content || {}).rendered, codes) + '</article></main>'
        + '<section class="max-w-site mx-auto px-7 pb-[80px]"><div class="mt-9 text-center"><a href="/shad/news" class="btn border border-black/15 bg-white hover:border-shad hover:text-shad"><i class="ti ti-list"></i>NEWS一覧へ</a></div></section>';
      if (window.gsap) window.dispatchEvent(new Event("resize"));
    })
    .catch(function () { fail("記事を読み込めませんでした。時間をおいて再度お試しください。"); });
})();
