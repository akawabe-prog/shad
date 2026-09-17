/* =========================================================
   SHAD JAPAN — news_live.js
   TOPの NEWS 枠と /news 一覧を、表示時に CJ の CMS API から取り直して最新化する。
     API : https://cms.customjapan.net/wp-json/custom/v1/posts?categories=480 …
           （カテゴリ 90_SHAD ＝ site:SHAD。tools/fetch_news_api.py と同じ条件）
   ・HTMLには build_news.py が書き出した記事カードが入っているので、API に失敗しても表示は崩れない
   ・サイト内に記事ページがある記事（/news/cj-<id>）はそこへ、まだ無い新着記事は /news/article?id=<id>（APIから本文を表示）へ
   ・カテゴリの判定（タグ → News/Feature/Event/Media/Guide）は fetch_news_api.py と同じ
   ========================================================= */
(function () {
  var API = "https://cms.customjapan.net/wp-json/custom/v1/posts?categories=480&publish_codes=n&per_page=24&_embed"
          + "&_fields=id,date,title.rendered,excerpt.rendered,link,_embedded";
  var TAG_TO_CATEGORY = [["#出展", "Event"], ["#ニュース", "News"], ["#特集", "Feature"], ["#メディア", "Media"]];
  var ORDER = ["News", "Feature", "Event", "Racing", "Media", "Guide"];
  var CACHE_KEY = "shad-news-live-v1", CACHE_MIN = 10;

  var rail = document.querySelector(".news-rail");          // TOP
  var grid = document.getElementById("newsGrid");           // /news 一覧
  if (!rail && !grid) return;
  if (window.SHAD_NEWS_LIVE === false) return;

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function strip(s) { var d = document.createElement("div"); d.innerHTML = s || ""; return (d.textContent || "").replace(/\s*\[\s*…\s*\]\s*$/, "…").replace(/\s+/g, " ").trim(); }
  function jpDate(iso) { return (iso || "").slice(0, 10).replace(/-/g, "."); }
  function tagsOf(p) { return (((p._embedded || {}).tags) || []).map(function (t) { return t && t.name || ""; }); }
  function imageOf(p) {
    var fm = (p._embedded || {}).featured_media; if (Array.isArray(fm)) fm = fm[0];
    if (!fm || typeof fm !== "object") return "";
    var sizes = (fm.media_details || {}).sizes || {};
    var k = ["medium_large", "large", "full"].filter(function (x) { return sizes[x] && sizes[x].source_url; })[0];
    return k ? sizes[k].source_url : (fm.source_url || "");
  }
  function toItem(p) {
    var tags = tagsOf(p), cat = "Guide";
    for (var i = 0; i < TAG_TO_CATEGORY.length; i++) if (tags.indexOf(TAG_TO_CATEGORY[i][0]) >= 0) { cat = TAG_TO_CATEGORY[i][1]; break; }
    return { id: p.id, date: (p.date || "").slice(0, 10), category: cat, title: strip((p.title || {}).rendered),
             lead: strip((p.excerpt || {}).rendered).slice(0, 160), image: imageOf(p), url: p.link || "" };
  }
  function fetchPage(n) { return fetch(API + "&page=" + n).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json().then(function (j) { return { json: j, pages: +(r.headers.get("X-WP-TotalPages") || 1) }; }); }); }
  function load(all) {
    try { var c = JSON.parse(sessionStorage.getItem(CACHE_KEY) || "null"); if (c && c.all >= (all ? 1 : 0) && Date.now() - c.t < CACHE_MIN * 60000) return Promise.resolve(c.items); } catch (e) {}
    return fetchPage(1).then(function (r) {
      var posts = r.json, rest = [];
      if (all) for (var p = 2; p <= r.pages; p++) rest.push(fetchPage(p).then(function (x) { return x.json; }));
      return Promise.all(rest).then(function (more) {
        more.forEach(function (m) { posts = posts.concat(m); });
        var items = posts.map(toItem).sort(function (a, b) { return a.date < b.date ? 1 : -1; });
        try { sessionStorage.setItem(CACHE_KEY, JSON.stringify({ t: Date.now(), all: all ? 1 : 0, items: items })); } catch (e) {}
        return items;
      });
    });
  }

  /* サイト内に記事ページがある id（いま表示されているカードの href から拾う） */
  var local = {};
  document.querySelectorAll('a[href^="/news/cj-"]').forEach(function (a) { var m = a.getAttribute("href").match(/cj-(\d+)/); if (m) local[m[1]] = true; });

  function card(a) {
    var isLocal = !!local[String(a.id)];
    /* まだ静的ページを生成していない新着は、APIから本文を取るサイト内のライブ記事ページへ */
    var href = isLocal ? "/news/cj-" + a.id : "/news/article?id=" + a.id;
    var attrs = "";
    var thumb = a.image
      ? '<span class="block aspect-[4/3] overflow-hidden"><img src="' + esc(a.image) + '" alt="" loading="lazy" class="w-full h-full object-cover transition duration-300 hover:scale-105"></span>'
      : '<span class="block aspect-[4/3] bg-gradient-to-br from-[#E4E1DB] to-[#D5D2CA]"></span>';
    var mark = "";
    return '<a href="' + esc(href) + '" class="ncard"' + attrs + ' data-cat="' + esc(a.category) + '">' + thumb
      + '<span class="block px-5 py-4"><span class="flex items-center gap-2.5"><span class="ncard-cat">' + esc(a.category) + '</span>'
      + '<span class="font-disp text-[13.5px] tracking-[.14em] text-neutral-500">' + jpDate(a.date) + '</span>' + mark + '</span>'
      + '<span class="block text-[15.5px] font-medium mt-1.5 leading-relaxed">' + esc(a.title) + '</span></span></a>';
  }
  function idsOf(root) { return [].map.call(root.querySelectorAll("a.ncard"), function (a) { var m = (a.getAttribute("href") || "").match(/(?:cj-|archives\/|\/)(\d+)\/?$/); return m ? m[1] : a.getAttribute("href"); }).join(","); }
  function cats(items) { var have = {}; items.forEach(function (a) { have[a.category] = 1; }); return ORDER.filter(function (c) { return have[c]; }); }

  /* ---- TOP：最新4件とカテゴリチップ ---- */
  if (rail) {
    load(false).then(function (items) {
      var top = items.slice(0, 4);
      if (!top.length) return;
      if (idsOf(rail) === top.map(function (a) { return String(a.id); }).join(",")) return;   // 変化なし
      rail.innerHTML = top.map(card).join("");
      var sec = rail.closest("section");
      var tags = sec && sec.querySelectorAll("a.tag");
      if (tags && tags.length) {
        var cs = cats(items).slice(0, 3), host = tags[0].parentNode;
        tags.forEach(function (t) { t.remove(); });
        var view = host.querySelector('a[href="/news"]');
        cs.forEach(function (c) { var a = document.createElement("a"); a.href = "/news?cat=" + encodeURIComponent(c); a.className = "tag hover:border-shad hover:text-shad transition"; a.textContent = c; host.insertBefore(a, view); });
      }
    }).catch(function () {});
  }

  /* ---- /news 一覧：全件とチップ、絞り込み ---- */
  if (grid) {
    var filter = document.getElementById("newsFilter"), empty = document.getElementById("newsEmpty");
    function bind() {
      var chips = filter ? filter.querySelectorAll(".cat-chip") : [], cards = grid.querySelectorAll(".ncard");
      chips.forEach(function (chip) {
        chip.onclick = function () {
          var cat = chip.dataset.cat, shown = 0;
          chips.forEach(function (c) { c.classList.toggle("on", c === chip); });
          cards.forEach(function (cd) { var on = cat === "all" || cd.dataset.cat === cat; cd.style.display = on ? "" : "none"; if (on) shown++; });
          if (empty) empty.classList.toggle("hidden", shown > 0);
        };
      });
    }
    load(true).then(function (items) {
      if (!items.length) return;
      if (idsOf(grid) !== items.map(function (a) { return String(a.id); }).join(",")) {
        grid.innerHTML = items.map(card).join("");
        if (filter) {
          filter.innerHTML = '<button type="button" class="cat-chip on" data-cat="all">すべて</button>'
            + cats(items).map(function (c) { return '<button type="button" class="cat-chip" data-cat="' + esc(c) + '">' + esc(c) + "</button>"; }).join("");
        }
        bind();
        var q = new URLSearchParams(location.search).get("cat");
        if (q && filter) { var t = filter.querySelector('.cat-chip[data-cat="' + q + '"]'); if (t) t.click(); }
      }
    }).catch(function () {});
  }
})();
