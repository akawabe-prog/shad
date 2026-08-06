/* =========================================================
   SHAD × カスタムジャパン版（shad.customjapan.net）— cj_shop.js
   toC向けの販売表示。ブランドサイト（www.shad-japan.com）では読み込まない。

     ① 商品詳細：販売価格（税込）／定価／割引率／在庫 ＋ 購入ボタン
     ② 商品一覧・適合検索の結果カード：販売価格を表示
     ③ ブランドサイト用の「定価のみ・購入は代理店へ」という文言を差し替え

   価格・在庫は site/data/ec/api_prices.json（ECのAPIから取得）を参照。
   更新は  python3 tools/fetch_api_prices.py
   ========================================================= */
(function () {
  /* 購入導線。ECの商品ページを開く。
     カート投入用のURL仕様が決まれば、この1か所を差し替えれば全ページに反映される。 */
  var ITEM_URL = "https://moto.customjapan.net/i/";
  var PRICES = null;

  function yen(n) {
    n = Number(n);
    return n > 0 ? "¥" + n.toLocaleString("ja-JP") : "";
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  /* 在庫表記から状態を判定（◯在庫あり／△残りわずか／★在庫限り／取寄 など） */
  function stockClass(txt) {
    if (!txt) return "cj-stock-none";
    if (txt.indexOf("取寄") >= 0 || txt.indexOf("予約") >= 0) return "cj-stock-order";
    if (txt.indexOf("△") >= 0 || txt.indexOf("★") >= 0) return "cj-stock-few";
    if (txt.indexOf("×") >= 0 || txt.indexOf("完売") >= 0) return "cj-stock-out";
    return "cj-stock-ok";
  }
  function offRate(list, sale) {
    if (!list || !sale || sale >= list) return 0;
    return Math.round((1 - sale / list) * 100);
  }

  /* 型番 → その型番でいちばん安い品番の価格（一覧カードの「〜円から」表示用） */
  var byCode = null;
  function priceOfCode(code) {
    if (!PRICES) return null;
    if (!byCode) {
      byCode = {};
      Object.keys(PRICES).forEach(function (cj) {
        var v = PRICES[cj];
        if (!v.code || !v.saleTaxIn) return;
        var cur = byCode[v.code];
        if (!cur || v.saleTaxIn < cur.saleTaxIn) byCode[v.code] = v;
      });
    }
    return byCode[String(code || "").toUpperCase()] || null;
  }

  /* ---------- ① 商品詳細ページ ---------- */
  function productPage() {
    var slot = document.querySelector("[data-variant-slot]");
    var skuEl = document.querySelector("[data-sku]");
    if (!slot || !skuEl) return false;

    var box = document.createElement("div");
    box.className = "cj-buy";
    slot.parentNode.insertBefore(box, slot.nextSibling);

    function refresh() {
      var cj = (skuEl.textContent || "").trim();
      var v = (PRICES || {})[cj];
      if (!cj || cj === "—") { box.innerHTML = ""; return; }

      if (!v || !v.saleTaxIn) {
        box.innerHTML = '<a class="cj-buy-btn" href="' + ITEM_URL + encodeURIComponent(cj)
          + '" target="_blank" rel="noopener"><i class="ti ti-shopping-cart"></i>'
          + '在庫・価格を見る</a>'
          + '<p class="cj-buy-note">カスタムジャパンの通販サイトが開きます。</p>';
        return;
      }
      var off = offRate(v.listTaxIn, v.saleTaxIn);
      box.innerHTML = ''
        + '<div class="cj-price">'
        +   '<span class="cj-price-lb">販売価格</span>'
        +   '<b class="cj-price-num">' + yen(v.saleTaxIn) + '</b>'
        +   '<span class="cj-price-tax">（税込）</span>'
        +   (off ? '<span class="cj-off">' + off + '% OFF</span>' : '')
        + '</div>'
        + (v.listTaxIn ? '<p class="cj-list">定価 <s>' + yen(v.listTaxIn) + '</s>（税込）</p>' : '')
        + '<p class="cj-stock ' + stockClass(v.statusTxt) + '">'
        +   '<i class="ti ti-circle-filled"></i>' + esc(v.statusTxt || "在庫はECでご確認ください") + '</p>'
        + '<a class="cj-buy-btn" href="' + ITEM_URL + encodeURIComponent(cj)
        +   '" target="_blank" rel="noopener"><i class="ti ti-shopping-cart"></i>この商品を購入する</a>'
        + '<p class="cj-buy-note">選択中のカラー・仕様のページが開きます（決済はカスタムジャパン通販サイト）。</p>';
    }

    // purchase.js が品番を書き換えるたびに追従する
    new MutationObserver(refresh).observe(skuEl, { childList: true, characterData: true, subtree: true });
    refresh();

    /* ブランドサイトの「メーカー希望小売価格（定価）」の大きな表示は、
       販売価格と二重になるので隠す（定価は当ブロック内に打ち消しで出す）。 */
    var big = document.querySelector("[data-price]");
    if (big) {
      var line = big.closest("p");
      var label = line && line.previousElementSibling;
      if (label && label.textContent.indexOf("メーカー希望小売価格") >= 0) label.remove();
      if (line) line.remove();
    }

    // ブランドサイト用の文言・購入ブロックは重複するので消す
    document.querySelectorAll("p").forEach(function (p) {
      var t = (p.textContent || "");
      if (t.indexOf("ご購入は日本総代理店") >= 0 || t.indexOf("定価（税込）です") >= 0) {
        var wrap = p.closest(".rounded-\\[18px\\]") || p;
        wrap.remove();
      }
    });
    return true;
  }

  /* ---------- ② 一覧カード（/products・適合検索の結果） ---------- */
  function codeFromHref(href) {
    var m = String(href || "").match(/\/product\/([a-z0-9]+)/i);
    return m ? m[1].toUpperCase() : "";
  }
  function priceTag(v) {
    var el = document.createElement("p");
    el.className = "cj-card-price";
    el.innerHTML = '<b>' + yen(v.saleTaxIn) + '</b><span>税込</span>'
      + (v.listTaxIn && v.listTaxIn > v.saleTaxIn
          ? '<s>' + yen(v.listTaxIn) + '</s>' : '');
    return el;
  }
  function decorateCards() {
    var cards = document.querySelectorAll(".pcard, .product-card > a.card-link");
    cards.forEach(function (card) {
      if (card.querySelector(".cj-card-price")) return;
      var v = priceOfCode(codeFromHref(card.getAttribute("href")));
      if (!v) return;
      var anchor = card.querySelector(".pcard-jp") || card.querySelector(".card-jp")
                || card.querySelector(".card-head") || card.querySelector(".pcard-head");
      if (!anchor) return;
      anchor.parentNode.insertBefore(priceTag(v), anchor.nextSibling);
    });
  }

  /* ---------- 起動 ---------- */
  fetch("/data/ec/api_prices.json")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      PRICES = (d && d.byCjCode) || {};
      productPage();
      decorateCards();
      // 一覧は絞り込みで再描画されるため、追加分にも価格を付ける
      var grid = document.getElementById("grid") || document.getElementById("productArea");
      if (grid) new MutationObserver(decorateCards).observe(grid, { childList: true, subtree: true });
    })
    .catch(function () { /* 価格が取れない場合はブランドサイトと同じ表示のまま */ });
})();
