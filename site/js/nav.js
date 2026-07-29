/* =========================================================
   SHAD JAPAN — nav.js
   スマートフォン用ナビゲーション（ハンバーガーメニュー）の開閉。
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
    if (window.innerWidth >= 768 && isOpen()) close();
  });
})();
