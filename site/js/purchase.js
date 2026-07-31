/* =========================================================
   SHAD JAPAN — purchase.js（商品カタログ連携）
   商品マスター（data/catalog/*.json）を読み込み、商品詳細ページに
     ① カラー／仕様バリエーション選択（選択で 定価・品番・画像 を切替）
     ② 定価（メーカー希望小売価格・税込）
     ③ 対応するアクセサリー・補修パーツ一覧
   を自己注入する。購入ボタン・外部ECリンクは設置しない。

   データ生成は tools/build_catalog.py（CSV差し替え → 再実行で更新）
   ========================================================= */
(function () {
  var IMG_HOST = "https://img.customjapan.net";
  var BUY_BASE = "https://moto.customjapan.net/i/";   // 品番を付けて購入ページへ

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function yen(n) {
    n = Number(n);
    return n > 0 ? "¥" + n.toLocaleString("ja-JP") : "";
  }
  function imgUrl(p) {
    if (!p) return "";
    return /^https?:/.test(p) ? p : IMG_HOST + p;
  }
  function currentCode() {
    var el = document.querySelector("[data-product-fitment-checker]");
    var code = (el && el.dataset.productCode) || "";
    if (!code) {
      var m = (location.pathname || "").match(/\/product\/([a-z0-9]+)|product-([a-z0-9]+)/i);
      if (m) code = m[1] || m[2];
    }
    return code.toUpperCase();
  }
  function loadJSON(rel) {
    return fetch(new URL(rel, location.origin).href)
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }

  /* ---- 挿入位置：SPEC の直後（なければ SAME SERIES の直前）---- */
  function findInsertPoint() {
    var spec = null, same = null;
    var secs = document.querySelectorAll("section");
    for (var i = 0; i < secs.length; i++) {
      var h = secs[i].querySelector("h2");
      if (!h) continue;
      var t = h.textContent.trim();
      if (/^Spec$/i.test(t)) spec = secs[i];
      if (/^Same Series$/i.test(t) && !same) same = secs[i];
    }
    return { after: spec, before: same };
  }
  function insertSection(sec) {
    var pt = findInsertPoint();
    // 適合確認セクションの後（＝SAME SERIES の直前）に置き、購入導線を最後に見せる
    if (pt.before && pt.before.parentNode) pt.before.parentNode.insertBefore(sec, pt.before);
    else if (pt.after && pt.after.parentNode) pt.after.parentNode.insertBefore(sec, pt.after.nextSibling);
    else {
      var f = document.querySelector("footer");
      if (f && f.parentNode) f.parentNode.insertBefore(sec, f);
      else document.body.appendChild(sec);
    }
  }

  /* ---- ① + ② 価格・カラー選択（商品情報エリア＝ギャラリー横に表示）---- */
  function variantBlock(entry) {
    var variants = (entry && entry.variants) || [];
    var chips = "";
    if (variants.length > 1) {
      chips = '<div class="mt-4">'
        + '<span class="block text-[12px] font-bold text-neutral-700 mb-2">カラー・仕様を選ぶ<span class="text-neutral-400 font-normal ml-1.5">（' + variants.length + '種）</span></span>'
        + '<div class="flex flex-wrap gap-2" data-color-chips>'
        + variants.map(function (v, i) {
            var label = v.color || v.size || v.name;
            return '<button type="button" data-vi="' + i + '" aria-pressed="' + (i === 0) + '"'
              + ' class="cvchip' + (i === 0 ? " on" : "") + '">' + esc(label) + "</button>";
          }).join("")
        + "</div></div>";
    }
    return '<div>'
      + '<div class="flex items-end gap-2 flex-wrap">'
      +   '<span class="text-[12px] text-neutral-400">メーカー希望小売価格</span>'
      + "</div>"
      + '<p class="mt-0.5"><b data-price class="text-[30px] font-bold text-ink leading-none"></b>'
      +   '<span class="text-[12px] text-neutral-400 ml-1">（税込）</span></p>'
      + '<p class="text-[12.5px] text-neutral-500 mt-2">品番：<span data-sku class="font-medium text-neutral-700"></span></p>'
      + chips
      + '<p class="text-[11.5px] text-neutral-400 mt-3 leading-relaxed">※定価（税込）です。ご購入は日本総代理店 株式会社カスタムジャパンにて承ります。</p>'
      + "</div>";
  }

  /* ---- ③ 対応アクセサリー・補修パーツ ---- */
  function accessoryBlock(items) {
    if (!items.length) return "";
    var cards = items.map(function (a) {
      var img = imgUrl((a.images && a.images[0]) || a.thumb);
      return '<div class="border border-black/10 rounded-[12px] overflow-hidden bg-white">'
        + '<span class="block aspect-square bg-mist flex items-center justify-center overflow-hidden">'
        + (img ? '<img src="' + esc(img) + '" alt="" loading="lazy" class="w-full h-full object-contain p-2">'
               : '<i class="ti ti-photo text-[26px] text-neutral-300"></i>')
        + "</span>"
        + '<span class="block px-3.5 py-3">'
        +   '<span class="block text-[13px] font-medium leading-snug text-neutral-800">' + esc(a.displayName || a.name) + "</span>"
        +   '<span class="block text-[12px] text-neutral-500 mt-1.5">品番：' + esc(a.cjCode) + "</span>"
        +   (a.msrpTaxIn ? '<span class="block text-[14px] font-bold mt-1">' + yen(a.msrpTaxIn)
                          + '<span class="text-[11px] text-neutral-400 font-normal ml-1">（税込）</span></span>' : "")
        + "</span></div>";
    }).join("");
    return '<div class="mt-5 rounded-[18px] border border-black/10 bg-white p-6 md:p-8">'
      + '<span class="font-disp text-[13px] tracking-[.22em] uppercase text-neutral-400">Accessories &amp; Parts</span>'
      + '<h3 class="text-[19px] font-bold mt-1">対応アクセサリー・補修パーツ</h3>'
      + '<p class="text-[13px] text-neutral-500 mt-2">この商品にお使いいただけるアクセサリー・補修パーツです。</p>'
      + '<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mt-5">' + cards + "</div>"
      + "</div>";
  }

  /* ---- ④ 購入導線（日本総代理店カスタムジャパンの商品ページへ）---- */
  function buyBlock(entry) {
    if (!entry) return "";
    return '<div class="mt-5 rounded-[18px] bg-mist p-6 md:p-8 text-center">'
      + '<p class="text-[13.5px] text-neutral-700 leading-relaxed">ご購入は日本総代理店<br class="sm:hidden">株式会社カスタムジャパンの通販サイトにて承ります。</p>'
      + '<a data-buy-link href="' + BUY_BASE + '" target="_blank" rel="noopener"'
      +   ' class="btn bg-shad text-white hover:bg-[#c4151b] mt-4"><i class="ti ti-shopping-cart"></i>購入はこちらから</a>'
      + '<p class="text-[11.5px] text-neutral-400 mt-3">選択中のカラー・仕様の商品ページが開きます。</p>'
      + "</div>";
  }

  /* ---- ギャラリー画像の差し替え ---- */
  function applyGallery(variant) {
    var main = document.getElementById("gMain");
    var imgs = (variant.images || []).map(imgUrl).filter(Boolean);
    if (!main || !imgs.length) return;
    main.src = imgs[0];
    var row = document.querySelector(".g-thumb") && document.querySelector(".g-thumb").parentNode;
    if (!row) return;
    row.innerHTML = imgs.slice(0, 6).map(function (src, i) {
      return '<button class="g-thumb' + (i === 0 ? " on" : "") + '" data-src="' + esc(src) + '">'
        + '<img src="' + esc(src) + '" alt="" loading="lazy"></button>';
    }).join("");
    row.querySelectorAll(".g-thumb").forEach(function (b) {
      b.addEventListener("click", function () {
        main.src = b.dataset.src;
        row.querySelectorAll(".g-thumb").forEach(function (x) { x.classList.remove("on"); });
        b.classList.add("on");
      });
    });
  }

  /* ---- バリアント適用 ---- */
  function applyVariant(root, entry, index) {
    var v = entry.variants[index];
    if (!v) return;
    var p = root.querySelector("[data-price]");
    var s = root.querySelector("[data-sku]");
    if (p) p.textContent = yen(v.msrpTaxIn) || "お問い合わせください";
    if (s) s.textContent = v.cjCode || "—";
    // 購入ボタンは選択中のカラー・仕様の商品ページへ
    document.querySelectorAll("[data-buy-link]").forEach(function (a) {
      a.href = v.cjCode ? BUY_BASE + encodeURIComponent(v.cjCode) : BUY_BASE;
    });
    applyGallery(v);
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (document.querySelector("[data-catalog]") || document.querySelector("[data-catalog-parts]")) return;
    var code = currentCode();
    if (!code) return;

    Promise.all([
      loadJSON("/data/catalog/products.json"),
      loadJSON("/data/catalog/accessory_index.json"),
      loadJSON("/data/catalog/accessories.json"),
      loadJSON("/data/catalog/others.json"),
    ]).then(function (res) {
      var products = res[0] || {};
      var index = res[1] || {};
      var accAll = (res[2] || []).concat(res[3] || []);
      var entry = products[code];

      // 対応アクセサリー（索引にある品番のみ）
      var wanted = index[code] || [];
      var accs = accAll.filter(function (a) { return wanted.indexOf(a.cjCode) >= 0; })
                       .sort(function (a, b) { return (a.msrpTaxIn || 0) - (b.msrpTaxIn || 0); });

      if (!entry && !accs.length) return;  // データが無い製品は何も出さない

      /* ②③ 対応アクセサリー＋購入導線 → SPEC の後
         （購入ボタンの href はこの後の applyVariant で選択中の品番に更新される）*/
      var body = accessoryBlock(accs) + buyBlock(entry);
      if (body) {
        var sec = document.createElement("section");
        sec.className = "max-w-site mx-auto px-7 pt-10 pb-2";
        sec.setAttribute("data-catalog-parts", "");
        sec.innerHTML = body;
        insertSection(sec);
      }

      /* ① 定価＋カラー選択 → 商品情報エリア（ギャラリー横）の器に描画 */
      var slot = document.querySelector("[data-variant-slot]");
      if (entry && slot) {
        slot.setAttribute("data-catalog", "");
        slot.innerHTML = variantBlock(entry);
        applyVariant(slot, entry, 0);
        var chipWrap = slot.querySelector("[data-color-chips]");
        if (chipWrap) {
          chipWrap.addEventListener("click", function (e) {
            var b = e.target.closest(".cvchip");
            if (!b) return;
            chipWrap.querySelectorAll(".cvchip").forEach(function (x) {
              x.classList.remove("on");
              x.setAttribute("aria-pressed", "false");
            });
            b.classList.add("on");
            b.setAttribute("aria-pressed", "true");
            applyVariant(slot, entry, Number(b.dataset.vi));
          });
        }
      }

    });
  });
})();
