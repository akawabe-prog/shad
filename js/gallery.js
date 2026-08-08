/* =========================================================
   SHAD JAPAN — gallery.js
   商品ページのメイン画像（看板画像）を、スマートフォンでは
   横スワイプのスライダーに切り替える。
   ・PC はサムネイル切替の従来UIのまま
   ・カラー変更（purchase.js）でサムネイルが差し替わったら作り直す
   ========================================================= */
(function () {
  var main = document.getElementById("gMain");
  if (!main) return;
  var wrap = main.closest(".g-main") || main.parentNode;
  var firstThumb = document.querySelector(".g-thumb");
  var row = firstThumb ? firstThumb.parentNode : null;
  if (row) row.classList.add("g-thumbs");

  var slider = document.createElement("div");
  slider.className = "g-slider";
  slider.setAttribute("data-g-slider", "");
  wrap.parentNode.insertBefore(slider, wrap.nextSibling);

  function sources() {
    var list = [];
    if (row) {
      row.querySelectorAll(".g-thumb").forEach(function (b) {
        if (b.dataset.src && list.indexOf(b.dataset.src) < 0) list.push(b.dataset.src);
      });
    }
    if (!list.length && main.getAttribute("src")) list.push(main.getAttribute("src"));
    return list;
  }

  function build() {
    var list = sources();
    if (!list.length) return;
    var alt = main.getAttribute("alt") || "";
    slider.innerHTML =
      '<div class="g-track">'
      + list.map(function (src, i) {
          return '<div class="g-slide"><img src="' + src + '" alt="' + (i === 0 ? alt : "") + '"'
            + (i === 0 ? "" : ' loading="lazy"') + "></div>";
        }).join("")
      + "</div>"
      + (list.length > 1
          ? '<div class="g-dots">' + list.map(function (_, i) {
              return '<span class="g-dot' + (i === 0 ? " on" : "") + '"></span>';
            }).join("") + "</div>"
          : "");

    var track = slider.querySelector(".g-track");
    var dots = slider.querySelectorAll(".g-dot");
    if (!dots.length) return;

    function mark(i) {
      dots.forEach(function (d, k) { d.classList.toggle("on", k === i); });
    }
    // 表示中のスライドを監視（scrollイベントに依存しない）
    if ("IntersectionObserver" in window) {
      var slides = track.querySelectorAll(".g-slide");
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) mark([].indexOf.call(slides, e.target));
        });
      }, { root: track, threshold: 0.6 });
      slides.forEach(function (s) { io.observe(s); });
    }
    track.addEventListener("scroll", function () {
      mark(Math.round(track.scrollLeft / Math.max(1, track.clientWidth)));
    }, { passive: true });

    // ドットをタップしてもその画像へ
    dots.forEach(function (d, i) {
      d.addEventListener("click", function () {
        track.scrollTo({ left: track.clientWidth * i, behavior: "smooth" });
      });
    });
  }

  build();
  // カラー・仕様の切替でサムネイルが入れ替わったら作り直す
  if (row && "MutationObserver" in window) {
    new MutationObserver(build).observe(row, { childList: true });
  }
})();
