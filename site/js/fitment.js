/* =========================================================
   SHAD JAPAN — fitment.js
   Shared vehicle-to-product search and product compatibility check.
   Data source: site/data/fitment/fitment_index.json
   ========================================================= */
(function () {
  /* パスはルート相対で固定（クリーンURLの階層 /product/xxx から読んでも解決できる）*/
  var dataUrl = "/data/fitment/fitment_index.json";
  var dataScriptUrl = dataUrl.replace(/fitment_index\.json$/, "fitment_index.js");
  var optionsUrl = dataUrl.replace(/fitment_index\.json$/, "vehicle_options.json");
  var indexPromise = null;
  var optionsPromise = null;
  var fittingProductsByCode = {};

  /* 車種に紐づくオプション（バックレストキット / シーシーバーキット）。
     ボックスの型番ではなく車種で決まる商品なので、適合結果に併記する。
     データ生成： tools/build_vehicle_options.py */
  function loadVehicleOptions() {
    if (!optionsPromise) {
      optionsPromise = fetch(optionsUrl)
        .then(function (res) { return res.ok ? res.json() : null; })
        .catch(function () { return null; });
    }
    return optionsPromise;
  }

  function renderVehicleOptions(root, vehicles) {
    var result = getEls(root).result;
    if (!result || !vehicles || !vehicles.length) return;
    loadVehicleOptions().then(function (data) {
      if (!data || !data.byVehicle) return;
      var seen = {}, items = [];
      vehicles.forEach(function (v) {
        (data.byVehicle[v.id] || []).forEach(function (o) {
          if (seen[o.cjCode]) return;
          seen[o.cjCode] = 1;
          items.push(o);
        });
      });
      if (!items.length) return;
      var cards = items.map(function (o) {
        var price = o.priceTaxIn ? "¥" + Number(o.priceTaxIn).toLocaleString("ja-JP") + "（税込）" : "";
        return '<a class="fit-fitting-product" href="' + o.url + '" target="_blank" rel="noopener">'
          + '<span class="fit-fitting-product-media"><img src="' + o.image + '" alt="" loading="lazy"></span>'
          + '<span class="fit-fitting-product-body"><small>' + o.type + "</small>"
          + "<strong>" + o.name + "</strong>"
          + '<span class="fit-fitting-product-code">品番：' + o.cjCode + "</span>"
          + '<span class="fit-fitting-product-foot"><i class="ti ti-shopping-cart"></i>'
          + "<span>カスタムジャパンで購入</span><b>" + price + "</b></span></span></a>";
      }).join("");
      var sec = document.createElement("div");
      sec.className = "fit-options";
      sec.innerHTML = '<p class="fit-result-kick mt-8">Options for this Motorcycle</p>'
        + '<h3 class="text-[19px] font-bold mt-1">この車種で使えるオプション</h3>'
        + '<p class="text-[13px] text-neutral-500 mt-1.5">バックレスト・シーシーバーは車種専用のキットが必要です。</p>'
        + '<div class="fit-fitting-list fit-fitting-list-wide">' + cards + "</div>";
      result.appendChild(sec);
    });
  }

  function prepareIndex(index) {
    fittingProductsByCode = {};
    (index.fittingProducts || []).forEach(function (product) {
      fittingProductsByCode[product.cjCode] = product;
    });
    return index;
  }

  function loadIndex() {
    if (!indexPromise) {
      if (window.SHAD_FITMENT_INDEX) {
        indexPromise = Promise.resolve(window.SHAD_FITMENT_INDEX).then(prepareIndex);
      } else {
        indexPromise = fetch(dataUrl).then(function (res) {
          if (!res.ok) throw new Error("fitment index load failed");
          return res.json();
        }).catch(loadIndexScript).then(prepareIndex);
      }
    }
    return indexPromise;
  }

  function loadIndexScript() {
    return new Promise(function (resolve, reject) {
      if (window.SHAD_FITMENT_INDEX) {
        resolve(window.SHAD_FITMENT_INDEX);
        return;
      }
      var script = document.createElement("script");
      script.src = dataScriptUrl;
      script.onload = function () {
        if (window.SHAD_FITMENT_INDEX) resolve(window.SHAD_FITMENT_INDEX);
        else reject(new Error("fitment script fallback did not set data"));
      };
      script.onerror = function () {
        reject(new Error("fitment index script load failed"));
      };
      document.head.appendChild(script);
    });
  }

  function normalize(value) {
    return String(value || "")
      .normalize("NFKC")
      .toLowerCase()
      .replace(/[‐-‒–—ー−]/g, "-")
      .replace(/\s+/g, " ")
      .trim();
  }

  function unique(items) {
    var seen = {};
    return items.filter(function (item) {
      var key = String(item || "");
      if (!key || seen[key]) return false;
      seen[key] = true;
      return true;
    });
  }

  function byJa(a, b) {
    return String(a).localeCompare(String(b), "ja");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatYen(value) {
    var amount = Number(value || 0);
    return amount > 0 ? amount.toLocaleString("ja-JP") + "円（税込）" : "";
  }

  function clearOptions(select, label) {
    if (!select) return;
    select.innerHTML = "";
    select.add(new Option(label, ""));
  }

  function setEnabled(select, enabled) {
    if (select) select.disabled = !enabled;
  }

  function getEls(root) {
    return {
      maker: root.querySelector("[data-fitment-maker], #mk"),
      model: root.querySelector("[data-fitment-model], #md"),
      year: root.querySelector("[data-fitment-year], #yr"),
      submit: root.querySelector("[data-fitment-submit], #go"),
      result: root.querySelector("[data-fitment-result]"),
      keyword: root.querySelector("[data-fitment-keyword]"),
    };
  }

  function productMap(index) {
    var map = {};
    (index.products || []).forEach(function (product) {
      map[product.code] = product;
    });
    return map;
  }

  function filterVehicles(index, predicate) {
    return (index.vehicles || []).filter(predicate || function () { return true; });
  }

  function groupedFitments(vehicles) {
    var groups = {};
    vehicles.forEach(function (vehicle) {
      vehicle.fitments.forEach(function (fitment) {
        if (!groups[fitment.productCode]) {
          groups[fitment.productCode] = {
            productCode: fitment.productCode,
            productName: fitment.productName,
            productSeries: fitment.productSeries,
            productLabel: fitment.productLabel,
            productImage: fitment.productImage,
            productUrl: fitment.productUrl,
            category: fitment.category,
            mountType: fitment.mountType,
            items: [],
          };
        }
        // 同じフィッティングキットはベースプレートの色違い等で重複させない。
        // フィッティング品番があればそれを優先キーに（無ければベースプレート）。
        var key = [
          fitment.fittingProductCode || fitment.baseplateCode,
          fitment.system,
          fitment.fittingUrl,
          vehicle.id,
          vehicle.displayModel,
          vehicle.yearLabel,
        ].join("|");
        if (!groups[fitment.productCode].items.some(function (item) { return item.key === key; })) {
          groups[fitment.productCode].items.push({
            key: key,
            vehicleId: vehicle.id,
            maker: vehicle.maker,
            displayModel: vehicle.displayModel,
            yearLabel: vehicle.yearLabel,
            baseplateCode: fitment.baseplateCode,
            baseplateName: fitment.baseplateName,
            fittingUrl: fitment.fittingUrl,
            fittingName: fitment.fittingName,
            system: fitment.system,
            discontinued: fitment.discontinued,
            fittingProduct: fittingProductsByCode[fitment.fittingProductCode] || null,
          });
        }
      });
    });
    return Object.keys(groups).map(function (key) { return groups[key]; }).sort(function (a, b) {
      return byJa(a.productCode, b.productCode);
    });
  }

  function fittingMeta(item) {
    var bits = [];
    if (item.system) bits.push(item.system + "システム");
    if (item.baseplateCode) bits.push(item.baseplateName + " " + item.baseplateCode);
    if (item.discontinued) bits.push("廃番");
    return bits.join(" / ");
  }

  /* クリーンURL化：product-xxx.html → /product/xxx（クエリ/ハッシュは保持）
     データ側に旧形式が残っていても、表示時にこの関数で新しい階層に直す。 */
  function cleanUrl(url) {
    var u = String(url || "").replace(/\.html(?=$|[?#])/i, "");
    u = u.replace(/^(?:\.\/)?product-([a-z0-9]+)/i, "/product/$1");
    return u;
  }

  function withFitmentParam(url, vehicleId) {
    url = cleanUrl(url);
    if (!vehicleId) return url;
    var sep = url.indexOf("?") >= 0 ? "&" : "?";
    return url + sep + "fitment=" + encodeURIComponent(vehicleId);
  }

  function renderFittingProduct(item) {
    var product = item.fittingProduct;
    var itemMeta = fittingMeta(item) || "車種専用フィッティング";
    if (!product) {
      return '<div class="fit-fitting-link">'
        + '<i class="ti ti-tool"></i><span>' + escapeHtml(itemMeta) + "</span></div>";
    }
    var image = product.image
      ? '<img src="' + escapeHtml(product.image) + '" alt="' + escapeHtml(product.title) + '" loading="lazy">'
      : '<span class="fit-fitting-product-placeholder"><i class="ti ti-tool"></i></span>';
    var status = product.status ? '<span>' + escapeHtml(product.status) + "</span>" : "";
    return '<div class="fit-fitting-product">'
      + '<span class="fit-fitting-product-media">' + image + "</span>"
      + '<span class="fit-fitting-product-body">'
      + '<small>必要なフィッティングキット</small>'
      + '<strong>' + escapeHtml(product.title || itemMeta) + "</strong>"
      + '<span class="fit-fitting-product-code">商品ID ' + escapeHtml(product.cjCode) + "</span>"
      + (status ? '<span class="fit-fitting-product-foot">' + status + '</span>' : "")
      + "</span></div>";
  }

  function renderProductCard(group) {
    var first = group.items[0] || {};
    var meta = fittingMeta(first);
    var productUrl = withFitmentParam(group.productUrl, first.vehicleId);
    var sub = group.productLabel || group.mountType || "";
    var img = group.productImage
      ? '<img src="' + group.productImage + '" alt="' + group.productCode + '" loading="lazy">'
      : '<span class="fit-card-placeholder">' + group.productCode + "</span>";
    var fittings = group.items.slice(0, 3).map(function (item) {
      return renderFittingProduct(item);
    }).join("");
    if (group.items.length > 3) {
      fittings += '<span class="fit-more">ほか ' + (group.items.length - 3) + " 件</span>";
    }
    return '<article class="fit-card">'
      + '<a class="fit-card-media" href="' + productUrl + '">' + img + "</a>"
      + '<div class="fit-card-body">'
      + '<p class="fit-card-kick">' + sub + "</p>"
      + '<h3><a href="' + productUrl + '">' + group.productCode + "</a></h3>"
      + '<p class="fit-card-meta">' + (meta || "車種専用フィッティング対応") + "</p>"
      + '<div class="fit-fitting-list">' + fittings + "</div>"
      + '<span class="fit-match-badge"><i class="ti ti-circle-check"></i>選択中の車体に適合</span>'
      + '<a href="' + productUrl + '" class="fit-detail-link">適合状態で商品を見る <i class="ti ti-arrow-right"></i></a>'
      + "</div></article>";
  }

  function renderVehicleResults(root, vehicles) {
    var result = getEls(root).result;
    if (!result) return;
    if (!vehicles.length) {
      result.innerHTML = '<div class="fit-empty"><i class="ti ti-alert-circle"></i><p>該当する適合商品が見つかりませんでした。</p></div>';
      return;
    }
    var groups = groupedFitments(vehicles);
    var title = vehicles[0].maker + " " + vehicles[0].displayModel + " / " + vehicles[0].yearLabel;
    result.innerHTML = '<div class="fit-result-head">'
      + '<div><p class="fit-result-kick">Fitment Result</p><h3>' + title + "</h3></div>"
      + '<span>' + groups.length + " モデル</span></div>"
      + '<div class="fit-card-grid">' + groups.map(renderProductCard).join("") + "</div>";
    renderVehicleOptions(root, vehicles);
  }

  function renderProductCheck(root, productCode, vehicles) {
    var result = getEls(root).result;
    if (!result) return;
    if (!vehicles.length) {
      result.innerHTML = '<div class="fit-empty"><i class="ti ti-circle-x"></i><p>この車体への適合は見つかりませんでした。</p><span>別モデルまたは年式を選択してください。</span></div>';
      return;
    }
    var groups = groupedFitments(vehicles.map(function (vehicle) {
      return Object.assign({}, vehicle, {
        fitments: vehicle.fitments.filter(function (fitment) { return fitment.productCode === productCode; }),
      });
    }));
    var group = groups[0];
    var fittings = (group ? group.items : []).map(function (item) {
      return renderFittingProduct(item);
    }).join("");
    result.innerHTML = '<div class="fit-ok">'
      + '<i class="ti ti-circle-check"></i>'
      + '<div><p>装着できます</p><span>必要な車種専用フィッティングを確認してください。</span></div>'
      + "</div>"
      + '<div class="fit-fitting-list fit-fitting-list-wide">' + fittings + "</div>";
    renderVehicleOptions(root, vehicles);
  }

  function renderProductMismatch(root, vehicle) {
    var result = getEls(root).result;
    if (!result) return;
    var label = vehicle ? vehicle.maker + " " + vehicle.displayModel + " / " + vehicle.yearLabel : "選択中の車体";
    result.innerHTML = '<div class="fit-empty"><i class="ti ti-circle-x"></i><p>' + label + ' への適合は見つかりませんでした。</p><span>この商品では別の車体を選択してください。</span></div>';
  }

  function currentFitmentId() {
    return new URLSearchParams(window.location.search || "").get("fitment");
  }

  function preserveFitmentLinks(fitmentId) {
    if (!fitmentId) return;
    document.querySelectorAll('a[href]').forEach(function (link) {
      var raw = link.getAttribute("href") || "";
      if (!/^\/product\/[a-z0-9-]+(?:[?#]|$)/i.test(raw)) return;
      var hashParts = raw.split("#");
      var hash = hashParts.length > 1 ? "#" + hashParts.slice(1).join("#") : "";
      var queryParts = hashParts[0].split("?");
      var base = queryParts[0];
      var params = new URLSearchParams(queryParts[1] || "");
      params.set("fitment", fitmentId);
      link.setAttribute("href", base + "?" + params.toString() + hash);
    });
  }

  /* メーカーの表示順：国内4メーカー＋BMWを先頭に固定し、以降は五十音・アルファベット順 */
  var MAKER_PRIORITY = ["ホンダ", "カワサキ", "ヤマハ", "スズキ", "BMW"];

  function byMaker(a, b) {
    var ia = MAKER_PRIORITY.indexOf(a), ib = MAKER_PRIORITY.indexOf(b);
    if (ia >= 0 || ib >= 0) {
      if (ia < 0) return 1;
      if (ib < 0) return -1;
      return ia - ib;
    }
    return byJa(a, b);
  }

  function initCascade(root, index, vehicles, onSubmit) {
    var els = getEls(root);
    if (!els.maker || !els.model || !els.year) return;
    var makers = unique(vehicles.map(function (vehicle) { return vehicle.maker; })).sort(byMaker);
    clearOptions(els.maker, "選択してください");
    clearOptions(els.model, "—");
    clearOptions(els.year, "—");
    makers.forEach(function (maker) { els.maker.add(new Option(maker, maker)); });
    setEnabled(els.model, false);
    setEnabled(els.year, false);
    if (els.submit) els.submit.disabled = true;

    function selectedVehicles() {
      return vehicles.filter(function (vehicle) {
        return vehicle.maker === els.maker.value &&
          vehicle.modelKey === els.model.value &&
          vehicle.yearLabel === els.year.value;
      });
    }

    els.maker.addEventListener("change", function () {
      var models = unique(vehicles
        .filter(function (vehicle) { return vehicle.maker === els.maker.value; })
        .map(function (vehicle) { return vehicle.modelKey; }))
        .sort(byJa);
      clearOptions(els.model, "選択してください");
      clearOptions(els.year, "—");
      models.forEach(function (model) { els.model.add(new Option(model, model)); });
      setEnabled(els.model, Boolean(els.maker.value));
      setEnabled(els.year, false);
      if (els.submit) els.submit.disabled = true;
    });

    els.model.addEventListener("change", function () {
      var years = unique(vehicles
        .filter(function (vehicle) {
          return vehicle.maker === els.maker.value && vehicle.modelKey === els.model.value;
        })
        .map(function (vehicle) { return vehicle.yearLabel; }))
        .sort(byJa);
      clearOptions(els.year, "選択してください");
      years.forEach(function (year) { els.year.add(new Option(year, year)); });
      setEnabled(els.year, Boolean(els.model.value));
      if (els.submit) els.submit.disabled = true;
    });

    els.year.addEventListener("change", function () {
      if (els.submit) els.submit.disabled = !els.year.value;
      if (!els.submit && els.year.value) onSubmit(selectedVehicles());
    });

    if (els.submit) {
      els.submit.addEventListener("click", function (event) {
        event.preventDefault();
        if (!els.year.value) return;
        onSubmit(selectedVehicles());
      });
    }

    if (els.keyword) {
      els.keyword.addEventListener("input", function () {
        var q = normalize(els.keyword.value);
        if (q.length < 2) return;
        var matches = vehicles.filter(function (vehicle) {
          return vehicle.searchText.indexOf(q) >= 0 || normalize(vehicle.displayModel).indexOf(q) >= 0;
        });
        renderVehicleResults(root, matches.slice(0, 8));
      });
    }

    return {
      selectVehicle: function (vehicle) {
        if (!vehicle) return;
        els.maker.value = vehicle.maker;
        els.maker.dispatchEvent(new Event("change"));
        els.model.value = vehicle.modelKey;
        els.model.dispatchEvent(new Event("change"));
        els.year.value = vehicle.yearLabel;
        els.year.dispatchEvent(new Event("change"));
      },
    };
  }

  function initVehicleFinder(root, index) {
    initCascade(root, index, filterVehicles(index), function (vehicles) {
      renderVehicleResults(root, vehicles);
    });
  }

  function initProductChecker(root, index) {
    var productCode = (root.dataset.productCode || "").toUpperCase();
    var result = getEls(root).result;
    var fitmentId = currentFitmentId();
    preserveFitmentLinks(fitmentId);
    var covered = (index.coverage && index.coverage.siteProductsCovered || []).indexOf(productCode) >= 0;
    var allVehicles = filterVehicles(index);
    var vehicles = filterVehicles(index, function (vehicle) {
      return vehicle.fitments.some(function (fitment) { return fitment.productCode === productCode; });
    });
    if (!covered || !vehicles.length) {
      var els = getEls(root);
      [els.maker, els.model, els.year, els.submit].forEach(function (el) {
        if (el) el.disabled = true;
      });
      if (result) {
        result.innerHTML = '<div class="fit-empty"><i class="ti ti-info-circle"></i><p>この商品の適合データは現在準備中です。</p><span>車種専用フィッティングの有無は取扱店でご確認ください。</span></div>';
      }
      return;
    }
    var cascade = initCascade(root, index, vehicles, function (selectedVehicles) {
      renderProductCheck(root, productCode, selectedVehicles);
    });
    if (fitmentId) {
      var selected = vehicles.find(function (vehicle) { return vehicle.id === fitmentId; });
      var selectedAnyProduct = allVehicles.find(function (vehicle) { return vehicle.id === fitmentId; });
      if (selected && cascade) {
        cascade.selectVehicle(selected);
        renderProductCheck(root, productCode, [selected]);
        root.scrollIntoView({ block: "start" });
      } else if (selectedAnyProduct) {
        renderProductMismatch(root, selectedAnyProduct);
        root.scrollIntoView({ block: "start" });
      }
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var finders = document.querySelectorAll("[data-fitment-finder]");
    var checkers = document.querySelectorAll("[data-product-fitment-checker]");
    if (!finders.length && !checkers.length) return;
    loadIndex().then(function (index) {
      finders.forEach(function (root) { initVehicleFinder(root, index); });
      checkers.forEach(function (root) { initProductChecker(root, index); });
    }).catch(function () {
      document.querySelectorAll("[data-fitment-result]").forEach(function (el) {
        el.innerHTML = '<div class="fit-empty"><i class="ti ti-alert-circle"></i><p>適合データを読み込めませんでした。</p></div>';
      });
    });
  });
})();
