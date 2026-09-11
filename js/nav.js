/* =========================================================
   SHAD JAPAN — nav.js
   ① スマートフォン用ナビゲーション（ハンバーガーメニュー）の開閉
   ② PCヘッダー「PRODUCTS」のホバーメニュー（カテゴリのサムネイル表示）
   全ページ共通で読み込む。
   ========================================================= */
(function () {
  var btn = document.getElementById("navToggle");
  var panel = document.getElementById("navMobile");
  if (!btn || !panel) return;

  function open() {
    panel.classList.remove("hidden");
    btn.setAttribute("aria-expanded", "true");
    btn.setAttribute("aria-label", "メニューを閉じる");
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24"'
      + ' fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true">'
      + '<path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>';
    document.documentElement.style.overflow = "hidden";
  }
  function close() {
    panel.classList.add("hidden");
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-label", "メニューを開く");
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24"'
      + ' fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true">'
      + '<path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/></svg>';
    document.documentElement.style.overflow = "";
  }
  function isOpen() { return !panel.classList.contains("hidden"); }

  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    isOpen() ? close() : open();
  });

  // メニュー内のリンクを押したら閉じる（同一ページ内リンクでも確実に閉じる）
  panel.addEventListener("click", function (e) {
    if (e.target.closest("a")) close();
  });

  // 外側タップ / ESC で閉じる
  document.addEventListener("click", function (e) {
    if (isOpen() && !panel.contains(e.target) && !btn.contains(e.target)) close();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && isOpen()) close();
  });

  // PC幅に広がったら閉じてスクロールロックを解除
  window.addEventListener("resize", function () {
    if (window.innerWidth >= 1024 && isOpen()) close();
  });
})();

/* =========================================================
   PCヘッダー：PRODUCTS のホバーメニュー
   シリーズ（TERRA / EXPANDABLE）とカテゴリをサムネイルで見せる。
   マークアップは全ページ共通なのでここで生成する（HTMLは変更不要）。
   ========================================================= */
(function () {
  var nav = document.getElementById("nav");
  if (!nav) return;

  // PC用メニューの中から「Products」のリンクを探す
  var link = null;
  nav.querySelectorAll("ul a").forEach(function (a) {
    if (a.textContent.trim().toLowerCase() === "products") link = a;
  });
  if (!link) return;
  var item = link.closest("li") || link;

  var SERIES = [
    { href: "/shad/terra", img: "/shad/img/banner_terra.webp", en: "Terra",
      jp: "旅の道具の、最高峰。" },
    { href: "/shad/expandable", img: "/shad/img/story_sh38x.webp", en: "Expandable",
      jp: "容量が、変わる。" }
  ];
  var CATEGORIES = [
    { href: "/shad/products?cat=TOP", img: "/shad/img/products/sh48.webp", label: "トップケース" },
    { href: "/shad/products?cat=SIDE", img: "/shad/img/products/sh38x.webp", label: "サイドケース" },
    { href: "/shad/products?cat=SIDEBAG", img: "/shad/img/products/tr30.webp", label: "サイドバッグ" },
    { href: "/shad/products?cat=TANK", img: "/shad/img/products/tr10.webp", label: "タンクバッグ" },
    { href: "/shad/products?cat=FITTING", img: "/shad/img/fitting/plate_l.webp", label: "フィッティングキット" }
  ];

  var panel = document.createElement("div");
  panel.className = "mega";
  panel.id = "megaProducts";
  panel.setAttribute("aria-hidden", "true");
  panel.innerHTML =
    '<div class="mega-in">'
    + '<div class="mega-col">'
    +   '<p class="mega-lb">Series</p>'
    +   '<div class="mega-series">'
    +     SERIES.map(function (s) {
            return '<a href="' + s.href + '" class="mega-feat">'
              + '<img src="' + s.img + '" alt="" loading="lazy">'
              + '<span class="mega-feat-in"><span class="mega-feat-en">' + s.en + '</span>'
              + '<span class="mega-feat-jp">' + s.jp + '</span></span></a>';
          }).join("")
    +   '</div>'
    + '</div>'
    + '<div class="mega-col mega-col-wide">'
    +   '<p class="mega-lb">Categories</p>'
    +   '<div class="mega-cats">'
    +     CATEGORIES.map(function (c) {
            return '<a href="' + c.href + '" class="mega-cat">'
              + '<span class="mega-cat-th"><img src="' + c.img + '" alt="" loading="lazy"></span>'
              + '<span class="mega-cat-lb">' + c.label + '</span></a>';
          }).join("")
    +   '</div>'
    +   '<div class="mega-links">'
    +     '<a href="/shad/products">すべての製品を見る<i class="ti ti-arrow-right"></i></a>'
    +     '<a href="/shad/fitment">車種から探す<i class="ti ti-arrow-right"></i></a>'
    +     '<a href="/shad/fitting-kits">フィッティングキットとは<i class="ti ti-arrow-right"></i></a>'
    +   '</div>'
    + '</div>'
    + '</div>';
  nav.appendChild(panel);

  link.setAttribute("aria-haspopup", "true");
  link.setAttribute("aria-expanded", "false");
  link.setAttribute("aria-controls", "megaProducts");

  var timer = null;
  function isDesktop() { return window.innerWidth >= 1024; }
  function show() {
    if (!isDesktop()) return;
    clearTimeout(timer);
    panel.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
    link.setAttribute("aria-expanded", "true");
  }
  function hide() {
    panel.classList.remove("is-open");
    panel.setAttribute("aria-hidden", "true");
    link.setAttribute("aria-expanded", "false");
  }
  // マウスが少し外れただけで閉じないよう、わずかに遅らせる
  function hideSoon() { clearTimeout(timer); timer = setTimeout(hide, 160); }

  item.addEventListener("mouseenter", show);
  item.addEventListener("mouseleave", hideSoon);
  panel.addEventListener("mouseenter", show);
  panel.addEventListener("mouseleave", hideSoon);
  link.addEventListener("focus", show);
  panel.addEventListener("focusout", function (e) {
    if (!panel.contains(e.relatedTarget)) hideSoon();
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") hide(); });
  window.addEventListener("resize", function () { if (!isDesktop()) hide(); });
})();
