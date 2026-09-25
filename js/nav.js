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

/* =========================================================
   ヘッダーの虫眼鏡：検索オーバーレイ（品番・商品名のサジェスト）
   /data/catalog/cards.json を1回だけ読み、入力に応じて候補を出す。
   PC・スマホ共通。Enter で先頭候補へ、ESC／外側タップで閉じる。
   ========================================================= */
(function () {
  var btns = [].slice.call(document.querySelectorAll('button[aria-label="検索"]'));
  if (!btns.length) return;
  var cards = null, box = null, input = null, list = null, active = -1, items = [];

  function esc(t){ return String(t==null?'':t).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function norm(t){ return String(t||'').toLowerCase().replace(/[\s\-＋+／/・]/g,''); }
  function build(){
    box = document.createElement('div'); box.className = 'srch'; box.setAttribute('role','dialog'); box.setAttribute('aria-label','商品検索');
    box.innerHTML = '<button type="button" class="srch-close" aria-label="閉じる"><i class="ti ti-x"></i></button>'
      + '<div class="srch-in"><label class="srch-box"><i class="ti ti-search"></i>'
      + '<input type="search" placeholder="品番・商品名で検索（例：TR46、トップケース、防水）" autocomplete="off" enterkeyhint="search"></label>'
      + '<p class="srch-hint">型番（TR46 / SH38X）・品番・メーカー品番・JAN・商品名・特徴で検索。Enter で該当ページへ</p>'
      + '<div class="srch-list" role="listbox"></div>'
      + '<div class="srch-quick"><a href="/shad/products">すべての製品</a><a href="/shad/products?cat=TOP">トップケース</a><a href="/shad/products?cat=SIDE">サイドケース</a>'
      + '<a href="/shad/products?feat=expandable">Expandable</a><a href="/shad/products?feat=waterproof">防水バッグ</a><a href="/shad/fitment">車種から探す</a><a href="/shad/lock-guide">ワンキー化ガイド</a></div></div>';
    document.body.appendChild(box);
    input = box.querySelector('input'); list = box.querySelector('.srch-list');
    box.querySelector('.srch-close').addEventListener('click', close);
    box.addEventListener('click', function(e){ if (e.target === box) close(); });
    input.addEventListener('input', render);
    input.addEventListener('keydown', function(e){
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') { e.preventDefault(); var q = norm(syn(input.value)); var a = list.querySelectorAll('.srch-item')[Math.max(active,0)]; var hit = exact(q); if (hit) location.href = '/shad/product/' + hit.code.toLowerCase(); else if (a) location.href = a.getAttribute('href'); else if (input.value.trim()) load().then(function(){ var h = exact(q); location.href = h ? '/shad/product/' + h.code.toLowerCase() : '/shad/products'; }); }
    });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && box.classList.contains('is-open')) close(); });
  }
  function exact(q){ if (!q || !items.length) return null; return items.filter(function(it){ return norm(it.code) === q || it.ids.split(' ').indexOf(q) >= 0; })[0] || null; }
  function move(d){ var as = [].slice.call(list.querySelectorAll('.srch-item')); if(!as.length) return; active = (active + d + as.length) % as.length; as.forEach(function(a,i){ a.classList.toggle('is-active', i===active); }); }
  function load(){
    if (cards) return Promise.resolve(cards);
    // cards.json（一覧カード）＋ products.json（品番・メーカー品番・JAN）を合わせて検索キーにする
    return Promise.all([
      fetch('/shad/data/catalog/cards.json').then(function(r){ return r.ok ? r.json() : {}; }).catch(function(){ return {}; }),
      fetch('/shad/data/catalog/products.json').then(function(r){ return r.ok ? r.json() : {}; }).catch(function(){ return {}; })
    ]).then(function(res){
      var d = res[0], P = res[1];
      var TAGJP = { alu:'アルミ', pp:'PP 樹脂 ポリプロピレン', soft:'ソフト 生地 バッグ', abs:'ABS樹脂 ハードシェル', expandable:'可変容量 エクスパンダブル', waterproof:'防水', smartlock:'スマートロック', terralock:'TERRAロック テラ', click:'クリックシステム タンクバッグ', fullpannier:'フルパニア' };
      items = Object.keys(d).map(function(k){ var c = d[k]; var tj = (c.tags||[]).map(function(t){ return TAGJP[t]||t; }).join(' ');
        var vs = (P[k] && P[k].variants) || [];
        var ids = vs.map(function(v){ return [v.cjCode, v.makerCode, v.jan, v.name].filter(Boolean).join(' '); }).join(' ');
        return { code:k, jp:c.jp||'', series:c.series||'', cap:c.cap||'', copy:c.copy||'', img:c.img||'', tags:tj, status:c.status||'',
        ids: norm(vs.map(function(v){ return [v.cjCode, v.makerCode, v.jan].filter(Boolean).join(' '); }).join(' ')),
        key: norm(k+' '+(c.jp||'')+' '+(c.series||'')+' '+(c.copy||'')+' '+(c.tags||[]).join(' ')+' '+tj+' '+ids) }; });
      cards = items; return cards;
    });
  }
  // 表記ゆらぎ（リアボックス→トップケース 等）を正規化してから照合
  var SYN = [[/リアボックス|リヤボックス|トップボックス|テールボックス|リアケース|リヤケース/g, 'トップケース'],
             [/サイドボックス|パニアケース|パニア/g, 'サイドケース'], [/シートバック|リアバッグ|リヤバッグ/g, 'シートバッグ'],
             [/バック/g, 'バッグ'], [/ボックス/g, 'ケース'], [/ハードケース/g, 'ケース'], [/防水バッグ/g, '防水']];
  function syn(s){ SYN.forEach(function(p){ s = s.replace(p[0], p[1]); }); return s; }
  function render(){
    if (!cards) { load().then(render); return; }
    var q = norm(syn(input.value)); active = -1;
    if (!q) { list.innerHTML = ''; return; }
    var hit = items.filter(function(it){ return it.key.indexOf(q) >= 0; });
    hit.sort(function(a,b){ function rank(x){ return norm(x.code) === q ? 0 : norm(x.code).indexOf(q)===0 ? 1 : x.ids.indexOf(q) >= 0 ? 2 : 3; } return rank(a) - rank(b) || a.code.localeCompare(b.code); });
    hit = hit.slice(0, 8);
    list.innerHTML = hit.length ? hit.map(function(it){
      return '<a class="srch-item" href="/shad/product/' + it.code.toLowerCase() + '" role="option">'
        + (it.img ? '<img src="' + esc(it.img) + '" alt="" loading="lazy">' : '')
        + '<span><b>' + esc(it.code) + '</b><span>' + esc(it.jp) + (it.cap ? ' / ' + esc(it.cap) : '') + (it.status ? '（' + esc(it.status) + '）' : '') + '</span></span>'
        + '<em>' + esc(it.series) + '</em></a>';
    }).join('') : '<p class="srch-empty">「' + esc(input.value) + '」に一致する商品が見つかりません。<a href="/shad/products" class="underline">製品一覧</a>からお探しください。</p>';
  }
  function open(){
    if (!box) build();
    box.classList.add('is-open'); document.documentElement.style.overflow = 'hidden';
    var m = document.getElementById('navMobile'); if (m) m.classList.add('hidden');
    load().then(function(){ render(); });
    setTimeout(function(){ input.focus(); }, 30);
  }
  function close(){ box.classList.remove('is-open'); document.documentElement.style.overflow = ''; }
  btns.forEach(function(b){ b.addEventListener('click', function(e){ e.preventDefault(); e.stopPropagation(); open(); }); });
})();
