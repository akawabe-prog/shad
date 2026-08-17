/* =========================================================
   SHAD JAPAN — faq.js
   商品ページのFAQを、CJのAPIから最新に差し替える（任意・段階的強化）。

   ページには tools/build_faq.py が生成した静的なFAQが既に入っています。
   このスクリプトは取得できたときだけ中身を更新し、失敗すれば静的なままにします。
   （検索エンジン向け・JS無効時のためにも、静的HTMLは必ず残す）

   ■ 動く条件（2026-08-14 実測）
   CJ側で https://www.shad-japan.com が許可オリジンに入り、**セッション不要**で
   取得できるようになりました（Cookie無しで 200 / プリフライトも 204）。

       許可: https://www.shad-japan.com   … 200
       不可: https://shad-japan.com（www無し）, localhost, github.io … いずれも 403

   許可オリジンは www 付きの1つだけなので、**本番ドメインで開かれたときだけ**
   実行します。ローカル確認やGitHub Pagesではリクエストを送らず、
   ビルド時に埋め込んだ静的FAQをそのまま表示します（コンソールも汚しません）。
   確認用に window.SHAD_FAQ_LIVE = true / false で上書きできます。
   ========================================================= */
(function () {
  "use strict";

  var ALLOWED_HOST = "www.shad-japan.com";   // CJ側が許可しているオリジン
  var LIVE = (typeof window.SHAD_FAQ_LIVE === "boolean")
    ? window.SHAD_FAQ_LIVE
    : location.hostname === ALLOWED_HOST;
  var FAQ_API = "https://api-f.customjapan.net/api/v1/faq?slug=shad";

  var sec = document.querySelector("#faq[data-faq-code]");
  if (!LIVE || !sec || !window.fetch) return;

  var CODE = sec.getAttribute("data-faq-code") || "";
  var JP = sec.getAttribute("data-faq-jp") || "";

  /* answer は <span style> 付きで返ってくる。<br> と <a> だけ許可して組み直す。 */
  function clean(html) {
    var doc = document.implementation.createHTMLDocument("");
    doc.body.innerHTML = html || "";
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 1) {
          var tag = n.tagName.toLowerCase();
          if (tag === "br") return;
          if (tag === "a") {
            var href = n.getAttribute("href") || "";
            Array.prototype.slice.call(n.attributes).forEach(function (a) {
              n.removeAttribute(a.name);
            });
            if (/^(https?:|\/)/.test(href)) {
              n.setAttribute("href", rewrite(href, n));
              if (/^https?:/.test(n.getAttribute("href"))) {
                n.setAttribute("target", "_blank");
                n.setAttribute("rel", "noopener");
              }
            }
            walk(n);
            return;
          }
          walk(n);
          // 許可外のタグ（span 等）は中身だけ残す
          while (n.firstChild) n.parentNode.insertBefore(n.firstChild, n);
          n.parentNode.removeChild(n);
        }
      });
    })(doc.body);
    return doc.body.innerHTML.trim().replace(/(<br\s*\/?>\s*)+$/, "");
  }

  /* 旧サイト・ECへのリンクは自サイトのパスへ（tools/fetch_faq.py と同じ対応） */
  function rewrite(href, a) {
    if (/^https?:\/\/(www\.)?shad-japan\.com\/shad_base\/?$/.test(href)) {
      if (/^\s*https?:\/\//.test(a.textContent)) a.textContent = "取扱店・SHAD BASEを探す";
      return "/store-locator";
    }
    var m = href.match(/^https?:\/\/moto\.customjapan\.net\/i\/([A-Za-z0-9]+)\/?$/);
    if (m && document.querySelector('a[href="/product/' + m[1].toLowerCase() + '"]')) {
      if (/^\s*https?:\/\//.test(a.textContent)) a.textContent = m[1].toUpperCase() + "の商品ページ";
      return "/product/" + m[1].toLowerCase();
    }
    return href;
  }

  function codesOf(it) {
    var out = [], m = /^shad-(.+)$/.exec(it.slug || "");
    if (m) out.push(m[1].toUpperCase());
    (it.relItems || "").split("_").forEach(function (t) {
      if (t) out.push(t.toUpperCase());
    });
    return out;
  }

  /* build_faq.py と同じグループ分け：この商品 → カテゴリ → 全般 */
  function grouped(items) {
    var used = {}, groups = [];
    function take(rows, title) {
      rows = rows.filter(function (x) { return !used[x.id]; });
      if (!rows.length) return;
      rows.forEach(function (x) { used[x.id] = 1; });
      groups.push({ title: title, rows: rows });
    }
    take(items.filter(function (x) {
      return codesOf(x).indexOf(CODE.toUpperCase()) >= 0;
    }), "この商品について");

    var cats = [];
    items.forEach(function (x) {
      var c = (x.classS || "").trim();
      if (!c || c === "全般" || cats.indexOf(c) >= 0) return;
      if (JP.indexOf(c) >= 0) cats.push(c);
    });
    cats.forEach(function (c) {
      take(items.filter(function (x) { return (x.classS || "").trim() === c; }), c + "について");
    });
    take(items.filter(function (x) { return (x.classS || "").trim() === "全般"; }), "SHADについて");
    return groups;
  }

  function paint(groups) {
    if (!groups.length) return;
    var host = sec.querySelector("[data-faq-list]");
    if (!host) return;
    var frag = document.createDocumentFragment();
    var first = true;
    groups.forEach(function (g) {
      var h = document.createElement("h3");
      h.className = "faq-group";
      h.textContent = g.title;
      frag.appendChild(h);
      g.rows.forEach(function (x) {
        var d = document.createElement("details");
        d.className = "faq-item";
        if (first) { d.open = true; first = false; }
        var s = document.createElement("summary");
        s.className = "faq-q";
        var q = document.createElement("span");
        q.className = "qmark";
        q.textContent = "Q";
        s.appendChild(q);
        s.appendChild(document.createTextNode(x.question || ""));
        var i = document.createElement("i");
        i.className = "ti ti-chevron-down chev";
        s.appendChild(i);
        d.appendChild(s);
        var a = document.createElement("div");
        a.className = "faq-a";
        a.innerHTML = clean(x.answer);
        d.appendChild(a);
        frag.appendChild(d);
      });
    });
    host.innerHTML = "";
    host.appendChild(frag);
  }

  // セッション不要なので Cookie は送らない（credentials: omit）
  fetch(FAQ_API, { credentials: "omit", headers: { "Cache-Control": "no-cache" } })
    .then(function (r) {
      if (!r.ok) throw new Error(String(r.status));
      return r.json();
    })
    .then(function (items) {
      if (Array.isArray(items) && items.length) paint(grouped(items));
    })
    .catch(function () { /* 取得できなければ静的FAQのまま（APIの障害時も表示は崩れない） */ });
})();
