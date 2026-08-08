/* =========================================================
   SHAD JAPAN — main.js
   1) 車種適合ファインダー（カスケード選択）
   2) STORYマーキーの無限ループ複製
   3) REELS動画の遅延再生（ビューポート内のみ再生）
   4) GSAPアニメーション（控えめ・reduced-motion対応）
   ========================================================= */

/* ---------- 1) Finder cascade ---------- */
(function () {
  // デモデータ：実装時はカスタムジャパン適合DB APIに置換
  var DATA = {
    "HONDA":   { "NC750X": ["2021-2025", "2016-2020"], "レブル250": ["2020-2025", "2017-2019"], "CB650R": ["2021-2025"], "ADV160": ["2023-2025"] },
    "YAMAHA":  { "MT-09": ["2024-2025", "2021-2023"], "TMAX560": ["2022-2025"] },
    "SUZUKI":  { "Vストローム650": ["2017-2025"] },
    "KAWASAKI":{ "Versys 650": ["2022-2025"] },
    "BMW":     { "R1300GS": ["2024-2025"] },
    "DUCATI":  { "ムルティストラーダV2": ["2022-2025"] }
  };
  var mk = document.getElementById("mk"),
      md = document.getElementById("md"),
      yr = document.getElementById("yr"),
      go = document.getElementById("go");
  if (!mk) return;
  if (document.querySelector("[data-fitment-finder]")) return;

  Object.keys(DATA).forEach(function (m) { mk.add(new Option(m, m)); });

  function reset(sel, ph) { sel.innerHTML = ""; sel.add(new Option(ph, "")); }

  mk.addEventListener("change", function () {
    reset(md, "選択してください"); reset(yr, "—");
    md.disabled = !mk.value; yr.disabled = true; go.disabled = true;
    if (mk.value) Object.keys(DATA[mk.value]).forEach(function (m) { md.add(new Option(m, m)); });
  });
  md.addEventListener("change", function () {
    reset(yr, "選択してください");
    yr.disabled = !md.value; go.disabled = true;
    if (md.value) DATA[mk.value][md.value].forEach(function (y) { yr.add(new Option(y, y)); });
  });
  yr.addEventListener("change", function () { go.disabled = !yr.value; });
  go.addEventListener("click", function () {
    // 実装時：適合結果ページへ遷移（/for-your-motorcycle/?mk=..&md=..&yr=..）
    if (!go.disabled) console.log("fitment search:", mk.value, md.value, yr.value);
  });
})();

/* ---------- 1.5) Hero video source switch（PC=16:9 / SP=9:16） ---------- */
(function () {
  var v = document.querySelector(".hero-video");
  if (!v) return;
  var mq = window.matchMedia("(max-width: 767px)");
  function apply() {
    var mobile = mq.matches;
    // 非表示（TOPのSPなど、別のスライダーが担当する場合）は読み込まない
    if (v.offsetParent === null && getComputedStyle(v).display === "none") {
      v.pause();
      return;
    }
    var src = v.dataset[mobile ? "srcMobile" : "srcDesktop"];
    if (v.getAttribute("src") === src) return;
    v.setAttribute("poster", v.dataset[mobile ? "posterMobile" : "posterDesktop"]);
    v.setAttribute("src", src);
    v.load(); v.play().catch(function () {});
  }
  apply();
  (mq.addEventListener ? mq.addEventListener("change", apply) : mq.addListener(apply));
})();

/* ---------- 2) Story marquee loop ---------- */
(function () {
  var trk = document.getElementById("mqTrack");
  if (trk) trk.innerHTML += trk.innerHTML; // シームレスループ用に複製
})();

/* ---------- 3) Reels lazy play ---------- */
(function () {
  var vids = document.querySelectorAll(".rtile video");
  if (!vids.length) return;
  if (!("IntersectionObserver" in window)) {
    vids.forEach(function (v) { v.play().catch(function () {}); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) e.target.play().catch(function () {});
      else e.target.pause();
    });
  }, { threshold: 0.25 });
  vids.forEach(function (v) { io.observe(v); });
})();

/* ---------- 4) GSAP animations（控えめ） ---------- */
(function () {
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced || typeof gsap === "undefined") return;

  gsap.registerPlugin(ScrollTrigger);

  /* HEROイントロ：キッカー→見出し→サブ→CTAの順に静かに立ち上がる */
  gsap.timeline({ defaults: { ease: "power3.out" } })
    .from(".hero-kick",  { y: 24, opacity: 0, duration: .7 }, .15)
    .from(".hero-title", { y: 34, opacity: 0, duration: .9 }, "-=.4")
    .from(".hero-sub",   { y: 24, opacity: 0, duration: .7 }, "-=.55")
    .from(".hero-ctas",  { y: 18, opacity: 0, duration: .6 }, "-=.45");

  /* セクション要素：data-reveal をフェードアップ（近接要素はスタッガー） */
  ScrollTrigger.batch("[data-reveal]", {
    start: "top 88%",
    once: true,
    onEnter: function (els) {
      gsap.fromTo(els,
        { y: 28, opacity: 0 },
        { y: 0, opacity: 1, duration: .8, ease: "power3.out", stagger: .09 });
    }
  });
})();

/* ---------- 5) TOP店舗検索：現在地から探す（→ ロケーターへ距離順で遷移） ---------- */
(function () {
  var btn = document.getElementById("topGeo");
  if (!btn) return;
  btn.addEventListener("click", function () {
    if (!navigator.geolocation) { location.href = "store-locator"; return; }
    var orig = btn.innerHTML;
    btn.innerHTML = '<i class="ti ti-loader-2"></i>現在地を取得中…';
    navigator.geolocation.getCurrentPosition(
      function (p) { location.href = "store-locator?lat=" + p.coords.latitude.toFixed(5) + "&lng=" + p.coords.longitude.toFixed(5); },
      function () { btn.innerHTML = orig; alert("現在地を取得できませんでした。位置情報の許可をご確認ください。"); location.href = "store-locator"; },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  });
})();

/* ---------- 6) 動画モーダル（[data-video] をクリックでフルスクリーン再生） ---------- */
(function () {
  if (!document.querySelector("[data-video]")) return;
  var modal = document.createElement("div");
  modal.className = "vmodal";
  modal.innerHTML = '<button class="vmodal-close" aria-label="閉じる"><i class="ti ti-x"></i></button>'
    + '<video controls playsinline preload="none"></video>';
  document.body.appendChild(modal);
  var video = modal.querySelector("video");
  var closeBtn = modal.querySelector(".vmodal-close");

  function open(src, poster) {
    if (!src) return;
    if (poster) video.setAttribute("poster", poster);
    video.setAttribute("src", src);
    modal.classList.add("on");
    document.body.classList.add("vmodal-open");
    video.currentTime = 0;
    video.play().catch(function () {});
  }
  function close() {
    video.pause();
    modal.classList.remove("on");
    document.body.classList.remove("vmodal-open");
    video.removeAttribute("src"); video.load();
  }

  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-video]");
    if (!t) return;
    e.preventDefault();
    open(t.getAttribute("data-video"), t.getAttribute("data-poster"));
  });
  closeBtn.addEventListener("click", close);
  modal.addEventListener("click", function (e) { if (e.target === modal) close(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && modal.classList.contains("on")) close(); });
})();

/* ---------- 7) 横スライダーの矢印（[data-slider-arrow] data-target） ---------- */
(function () {
  document.querySelectorAll("[data-slider-arrow]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var s = document.querySelector(btn.getAttribute("data-target"));
      if (!s) return;
      var first = s.querySelector(":scope > *");
      var step = (first ? first.getBoundingClientRect().width + 14 : 320) * 1.4;
      s.scrollBy({ left: (btn.getAttribute("data-slider-arrow") === "next" ? 1 : -1) * step, behavior: "smooth" });
    });
  });
})();
