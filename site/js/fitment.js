/* =========================================================
   SHAD JAPAN — fitment.js（適合検索）
   商品マスター（ItemList_SHAD.csv）から生成した適合データで
   「車種 → 適合商品」を検索する。ロジックは提供された
   shad_site（車種別適合検索）の実装をそのまま移植し、
   ・データの取得先（/data/fitment/reverse_data.json）
   ・自サイト内リンクは同一タブで開く
   ・当サイトに存在しないキット一覧ページへのリンクを外す
   の3点だけをブランドサイト向けに変更している。

   データ生成： python3 tools/fitment/build.py
   ========================================================= */
(function () {
  var root = document.querySelector("[data-fitment-finder]");
  if (!root) return;
  var host = root.querySelector("[data-fitment-mount]") || root;
  var MODE = root.dataset.fitmentMode || "entry";   // entry（TOP）/ page（結果ページ）
  var RESULT_PAGE = "/fitment";

  /* 車種の識別子：メーカー＋車種名（URLに載せて結果ページへ渡す）*/
  function bikeKey(b) { return b.maker + "|" + b.model; }
  function queryParam(name) {
    return new URLSearchParams(location.search || "").get(name) || "";
  }

  /* 検索UIを注入（提供実装と同じ構造・ID。エントリーモードでは結果部分を隠す）*/
  host.innerHTML = `<div class="selector-panel">
  <div class="panel-label">車種から探す</div>
  <div class="selector-row">
    <select id="makerSelect">
      <option value="">メーカーを選択</option>
    </select>
    <select id="seriesSelect" disabled>
      <option value="">シリーズを選択</option>
    </select>
    <select id="modelSelect" disabled>
      <option value="">車種・年式を選択</option>
    </select>
  </div>

  <div class="panel-or">または</div>

  <div class="search-wrap">
    <input type="text" id="searchInput" placeholder="キーワードで探す（例：PCX Vストローム、）" autocomplete="off">
    <ul id="suggestList"></ul>
  </div>

  <div id="selectedBar">
    <span class="selected-label">選択中</span>
    <span class="selected-model" id="selectedModel"></span>
    <button id="clearBikeBtn">選択解除</button>
  </div>
</div>

<div class="cat-filter" id="categoryFilter">
  <button type="button" class="cat-chip on" data-cat="all">すべて</button>
  <button type="button" class="cat-chip" data-cat="top">トップケース</button>
  <button type="button" class="cat-chip" data-cat="side">サイドケース</button>
  <button type="button" class="cat-chip" data-cat="sidebag">サイドバッグ</button>
  <button type="button" class="cat-chip" data-cat="tank">タンクバッグ</button>
</div>

<div class="filter-bar">
  <label><input type="checkbox" id="terraFilter"> TERRAシリーズのみ表示</label>
  <span class="filter-group" id="capacityFilterGroup">
    <label><input type="radio" name="capacityFilter" value="all" checked> 容量すべて</label>
    <label><input type="radio" name="capacityFilter" value="le40"> 40Lまで</label>
    <label><input type="radio" name="capacityFilter" value="gt40"> 40Lを超える</label>
  </span>
</div>

<h2 id="productTitle">商品一覧</h2>
<p id="productSub"></p>
<div id="productArea"></div>`;

  /* ---- 以下、移植したロジック ---- */

/* 適合データと、一覧カードの表示情報（型番・容量・コピー・特徴）を読む。
   カード情報が取れなくても適合検索そのものは動くよう、失敗は空で通す。 */
var CARDS = {};
Promise.all([
  fetch('/data/fitment/reverse_data.json').then(r => r.json()),
  fetch('/data/catalog/cards.json').then(r => r.ok ? r.json() : {}).catch(() => ({}))
])
  .then(([DATA, cards]) => { CARDS = cards || {}; init(DATA); })
  .catch(err => {
    console.error('適合検索の初期化に失敗:', err);
    document.getElementById('productTitle').textContent = 'データの読み込みに失敗しました';
  });

function init(DATA) {

const PLATES = DATA.plates;
const SIDECASES = DATA.sidecases;
const TANKBAGS = DATA.tankbags || [];
const SIDEBAGS = DATA.sidebags || {};
const BIKES = DATA.bikes;

// 英語⇔カタカナ対応表（両方向で機能）
const ALIASES = {
  // ホンダ
  'forza': 'フォルツァ',
  'africa twin': 'アフリカツイン',
  'africatwin': 'アフリカツイン',
  'gold wing': 'ゴールドウイング',
  'goldwing': 'ゴールドウイング',
  'hornet': 'ホーネット',
  'integra': 'インテグラ',
  'transalp': 'トランザルプ',
  'grom': 'グロム',
  'nighthawk': 'ナイトホーク',
  'crossrunner': 'クロスランナー',
  'lead': 'リード',
  // ヤマハ
  'tracer': 'トレーサー',
  'tenere': 'テネレ',
  'tricity': 'トリシティ',
  'niken': 'ナイケン',
  'majesty': 'マジェスティ',
  'cygnus': 'シグナス',
  'grand majesty': 'グランドマジェスティ',
  'fazer': 'フェザー',
  'feather': 'フェザー',
  // スズキ
  'vstrom': 'Vストローム',
  'v-strom': 'Vストローム',
  'v-': 'Vストローム',
  'bandit': 'バンディット',
  'burgman': 'バーグマン',
  'skywave': 'スカイウェイブ',
  'address': 'アドレス',
  'gixxer': 'ジクサー',
  'gixser': 'ジクサー',
  'gladius': 'グラディウス',
  // カワサキ
  'ninja': 'ニンジャ',
  'concours': 'コンコース',
  'rebel': 'レブル',
  'eliminator': 'エリミネーター',
  'vulcan': 'バルカン',
  // その他汎用
  'pan america': 'パンアメリカ',
  'panamerica': 'パンアメリカ',
  'harley': 'ハーレー',
  'adventure': 'アドベンチャー',
  'diverson': 'ディバージョン',
  'diversion': 'ディバージョン',
};

function expandQuery(q) {
  const lower = q.toLowerCase();
  const targets = [lower];
  for (const [en, ja] of Object.entries(ALIASES)) {
    if (lower.includes(en)) targets.push(ja.toLowerCase());
    if (lower.includes(ja.toLowerCase())) targets.push(en);
  }
  return targets;
}

const MAIN_MAKERS = ['ホンダ', 'ヤマハ', 'スズキ', 'カワサキ'];
const allMakers = [...new Set(BIKES.map(d => d.maker))];
const otherMakers = allMakers
  .filter(m => !MAIN_MAKERS.includes(m))
  .sort((a, b) => a.localeCompare(b, 'ja'));

const makerSelect = document.getElementById('makerSelect');
const seriesSelect = document.getElementById('seriesSelect');
const modelSelect = document.getElementById('modelSelect');
const searchInput = document.getElementById('searchInput');
const suggestList = document.getElementById('suggestList');
const selectedBar = document.getElementById('selectedBar');
const selectedModel = document.getElementById('selectedModel');
const productTitle = document.getElementById('productTitle');
const productSub = document.getElementById('productSub');
const productArea = document.getElementById('productArea');

let selectedBike = null;
let pendingBike = null;   // エントリーモードで「適合を見る」を押すまで保持する車種
let terraOnly = false;
let capacityFilter = 'all'; // 'all' | 'le40' | 'gt40'
let categoryFilter = 'all'; // 'all' | 'top' | 'side' | 'sidebag' | 'tank'

/* 商品カテゴリは適合データの持ち方から決まる（型番 → カテゴリ）。
   トップケース＝ベースプレート配下、サイドケース／サイドバッグ＝ハード/ソフトの別、
   タンクバッグ＝クリックシステム。カード表示ではなくデータ構造が根拠。 */
/* 型番 → トップケースSKU の索引（キットの「対応モデル」から一覧を作るため）*/
const TOPCASE_BY_CODE = {};
Object.values(PLATES).forEach(p => (p.topcases || []).forEach(tc => {
  if (tc.code && !TOPCASE_BY_CODE[tc.code]) TOPCASE_BY_CODE[tc.code] = tc;
}));

const CATEGORY_OF = {};
function mapCategories() {
  Object.values(PLATES).forEach(p => (p.topcases || []).forEach(t => {
    if (t.code) CATEGORY_OF[t.code] = 'top';
  }));
  Object.values(SIDECASES).flat().forEach(i => { if (i.code) CATEGORY_OF[i.code] = 'side'; });
  Object.values(SIDEBAGS).flat().forEach(i => { if (i.code) CATEGORY_OF[i.code] = 'sidebag'; });
  TANKBAGS.forEach(i => { if (i.code) CATEGORY_OF[i.code] = 'tank'; });
}
mapCategories();

const CATEGORY_LABEL = { top: 'トップケース', side: 'サイドケース',
                         sidebag: 'サイドバッグ', tank: 'タンクバッグ' };

document.querySelectorAll('#categoryFilter .cat-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    categoryFilter = chip.dataset.cat;
    document.querySelectorAll('#categoryFilter .cat-chip')
      .forEach(c => c.classList.toggle('on', c === chip));
    renderProducts();
  });
});

document.getElementById('terraFilter').addEventListener('change', e => {
  terraOnly = e.target.checked;
  renderProducts();
});

document.querySelectorAll('input[name="capacityFilter"]').forEach(r => {
  r.addEventListener('change', e => {
    capacityFilter = e.target.value;
    renderProducts();
  });
});

// カテゴリ・TERRAシリーズ（TR〜）・容量（L）での絞り込みをまとめて適用する
function applyFilters(items) {
  let result = items;
  if (categoryFilter !== 'all') {
    // カテゴリ不明（マスター未登録など）は絞り込み時は対象外にする
    result = result.filter(i => CATEGORY_OF[i.code] === categoryFilter);
  }
  if (terraOnly) result = result.filter(i => i.name.includes('TERRA'));
  if (capacityFilter !== 'all') {
    // capacity 不明（null）の商品は容量絞り込み時は対象外にする
    result = result.filter(i => i.capacity != null &&
      (capacityFilter === 'le40' ? i.capacity <= 40 : i.capacity > 40));
  }
  return result;
}

function filtersActive() {
  return terraOnly || capacityFilter !== 'all' || categoryFilter !== 'all';
}

// このカテゴリのセクションを描画するか（「すべて」なら全部）
function showCategory(cat) {
  return categoryFilter === 'all' || categoryFilter === cat;
}

const groupKey = b => b.group || b.model;

// ---- 3段プルダウン（メーカー → シリーズ → 車種） ----

// メーカー: 国内4社 → 海外メーカー（optgroup）
MAIN_MAKERS.forEach(m => {
  const opt = document.createElement('option');
  opt.value = m;
  opt.textContent = m;
  makerSelect.appendChild(opt);
});
const ogOther = document.createElement('optgroup');
ogOther.label = '海外メーカー';
otherMakers.forEach(m => {
  const opt = document.createElement('option');
  opt.value = m;
  opt.textContent = m;
  ogOther.appendChild(opt);
});
makerSelect.appendChild(ogOther);

function kindSuffix(bike) {
  const kinds = [];
  if (bike.top.length > 0) kinds.push('トップ');
  if (bike.side.length > 0) kinds.push('サイド');
  return kinds.length ? '（' + kinds.join('・') + '）' : '';
}

function resetSelect(sel, placeholder) {
  sel.innerHTML = '<option value="">' + placeholder + '</option>';
  sel.disabled = true;
}

function bikesOf(maker) {
  return BIKES
    .map((b, i) => ({ ...b, idx: i }))
    .filter(b => b.maker === maker);
}

// シリーズプルダウンを再構築。1件しかない場合は自動選択して次へ進む
function populateSeries(maker) {
  resetSelect(modelSelect, '車種・年式を選択');
  seriesSelect.innerHTML = '<option value="">シリーズを選択</option>';
  const groups = new Map();
  bikesOf(maker).forEach(b => {
    const key = groupKey(b);
    groups.set(key, (groups.get(key) || 0) + 1);
  });
  [...groups.entries()]
    .sort((a, b) => a[0].localeCompare(b[0], 'ja'))
    .forEach(([g, n]) => {
      const opt = document.createElement('option');
      opt.value = g;
      opt.textContent = g;
      seriesSelect.appendChild(opt);
    });
  seriesSelect.disabled = false;
  if (groups.size === 1) {
    seriesSelect.selectedIndex = 1;
    populateModels(maker, seriesSelect.value);
  }
}

// 車種プルダウンを再構築。1件しかない場合は自動選択
function populateModels(maker, group) {
  modelSelect.innerHTML = '<option value="">車種・年式を選択</option>';
  const items = bikesOf(maker)
    .filter(b => groupKey(b) === group)
    .sort((a, b) => a.model.localeCompare(b.model, 'ja'));
  items.forEach(b => {
    const opt = document.createElement('option');
    opt.value = b.idx;
    opt.textContent = b.model + ' ' + kindSuffix(b);
    modelSelect.appendChild(opt);
  });
  modelSelect.disabled = false;
  if (items.length === 1) {
    modelSelect.selectedIndex = 1;
    selectBike(BIKES[items[0].idx]);
  }
}

makerSelect.addEventListener('change', () => {
  searchInput.value = '';
  hideSuggest();
  if (makerSelect.value === '') {
    resetSelect(seriesSelect, 'シリーズを選択');
    resetSelect(modelSelect, '車種・年式を選択');
    return;
  }
  populateSeries(makerSelect.value);
});

seriesSelect.addEventListener('change', () => {
  if (seriesSelect.value === '') {
    resetSelect(modelSelect, '車種・年式を選択');
    return;
  }
  populateModels(makerSelect.value, seriesSelect.value);
});

modelSelect.addEventListener('change', () => {
  if (modelSelect.value === '') return;
  selectBike(BIKES[Number(modelSelect.value)]);
});

// ---- キーワード検索（サジェスト式） ----

function hideSuggest() {
  suggestList.classList.remove('show');
  suggestList.innerHTML = '';
}

searchInput.addEventListener('input', () => {
  const q = searchInput.value.trim();
  if (q === '') { hideSuggest(); return; }
  const targets = expandQuery(q);
  const items = BIKES
    .map((b, i) => ({ ...b, idx: i }))
    .filter(d => {
      const m = d.model.toLowerCase();
      const mk = d.maker.toLowerCase();
      return targets.some(t => m.includes(t) || mk.includes(t));
    })
    .sort((a, b) => a.model.localeCompare(b.model, 'ja'));

  suggestList.innerHTML = '';
  if (items.length === 0) {
    const li = document.createElement('li');
    li.className = 'no-hit';
    li.textContent = '該当する車種が見つかりませんでした';
    suggestList.appendChild(li);
  } else {
    items.forEach(d => {
      const li = document.createElement('li');
      li.appendChild(document.createTextNode(d.model));
      const badge = document.createElement('span');
      badge.className = 'maker-badge';
      badge.textContent = d.maker;
      li.appendChild(badge);
      if (d.top.length > 0) li.appendChild(makeKindBadge('トップ'));
      if (d.side.length > 0) li.appendChild(makeKindBadge('サイド'));
      // mousedown: input の blur より先に発火させて確実に拾う
      li.addEventListener('mousedown', e => {
        e.preventDefault();
        selectBikeFromSearch(d.idx);
      });
      suggestList.appendChild(li);
    });
  }
  suggestList.classList.add('show');
});

function makeKindBadge(text) {
  const b = document.createElement('span');
  b.className = 'kind-badge';
  b.textContent = text;
  return b;
}

searchInput.addEventListener('blur', () => setTimeout(hideSuggest, 150));
searchInput.addEventListener('focus', () => {
  if (searchInput.value.trim() !== '') searchInput.dispatchEvent(new Event('input'));
});

function selectBikeFromSearch(idx) {
  const bike = BIKES[idx];
  searchInput.value = bike.model;
  hideSuggest();
  // プルダウン側も選択状態に同期
  makerSelect.value = bike.maker;
  populateSeries(bike.maker);
  seriesSelect.value = groupKey(bike);
  populateModels(bike.maker, groupKey(bike));
  modelSelect.value = String(idx);
  selectBike(bike);
}

// ---- 車種の選択 ----

function selectBike(bike) {
  /* エントリーモード（TOPの「車種から探す」）では、この時点では遷移せず
     「適合を見る」ボタンを押したときに結果ページへ移動する。 */
  if (MODE === "entry") {
    if (window.__fsSetPending) window.__fsSetPending(bike);
    return;
  }
  selectedBike = bike;
  selectedModel.textContent = bike.model;
  selectedBar.classList.add('show');
  if (window.history && history.replaceState) {
    history.replaceState(null, "", RESULT_PAGE + "?bike=" + encodeURIComponent(bikeKey(bike)));
  }
  renderProducts();
  var head = document.getElementById('productTitle');
  if (head) head.scrollIntoView({ block: 'start' });
}

function clearBike() {
  selectedBike = null;
  if (MODE === "entry" && window.__fsSetPending) window.__fsSetPending(null);
  selectedBar.classList.remove('show');
  if (MODE === "page" && window.history && history.replaceState) {
    history.replaceState(null, "", RESULT_PAGE);
  }
  modelSelect.value = '';
  searchInput.value = '';
  hideSuggest();
  renderProducts();
}

document.getElementById('clearBikeBtn').addEventListener('click', clearBike);

// ---- 商品一覧 ----

function el(tag, className, text) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = text;
  return e;
}

/* 自サイト内リンク（ルート相対）は同一タブで開く。
   a.href は絶対URLに解決されるため、必ず元の文字列で判定する。 */
function isInternal(url) { return /^\//.test(String(url || '')); }
function productLink(name, url) {
  if (!url) return document.createTextNode(name);
  const a = document.createElement('a');
  a.href = url;
  if (!isInternal(url)) a.target = '_blank';
  a.textContent = name;
  return a;
}

function sectionTitle(text, count, kitListHref) {
  const t = el('div', 'product-section-title');
  t.appendChild(el('span', 'ttl', text));
  if (count !== undefined) t.appendChild(el('span', 'count', '全' + count + '点'));
  if (kitListHref) {
    const a = document.createElement('a');
    a.href = kitListHref;
    if (!isInternal(a.href)) a.target = '_blank';
    a.className = 'kit-list-link';
    a.textContent = 'フィッティングキット一覧 ›';
    t.appendChild(a);
  }
  return t;
}

/* 商品カード。商品一覧（/products）と同じ情報量で見せる：
   シリーズ／型番／容量／カテゴリ名・色数／キャッチコピー／特徴アイコン。
   表示情報は site/data/catalog/cards.json（products.html の PRODUCTS が原本）
   から型番で引く。カード情報が無い型番は名前だけの簡易表示にフォールバック。
   noteEl はカード下部の注記（標準付属・必要キットなど／省略可） */
const SERIES_JP = {
  'TERRA': 'Terra', 'EXPANDABLE': 'Expandable', 'TOP CASE': 'Top Case',
  'SIDE CASE': 'Side Case', 'ADVENTURE': 'Adventure', 'BAG': 'Bag',
  'LOCK': 'Lock', 'SEAT': 'Seat', 'ACCESSORY': 'Accessory'
};
const HELMET_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="1em" height="1em" style="display:inline-block;vertical-align:-2px;"><path d="M3.5 14a8.5 8.5 0 0 1 17 0"/><path d="M3.5 14h17v1.5a1.5 1.5 0 0 1-1.5 1.5h-3.2l-.9 2.4a1 1 0 0 1-.94.6H10a1 1 0 0 1-.94-.6L8.2 17H5a1.5 1.5 0 0 1-1.5-1.5z"/></svg>';

function featIcon(f) {
  if (f.oimg) return '<img src="' + f.oimg + '" alt="" class="oimg" loading="lazy">';
  if (f.ic === 'helmet') return HELMET_SVG;
  return '<i class="ti ti-' + f.ic + '"></i>';
}

function featRow(card) {
  if (!card.features || !card.features.length) return null;
  const row = el('div', 'feat-row');
  card.features.slice(0, 3).forEach(function (f) {
    const s = el('span', 'feat');
    const fi = el('span', 'fi');
    fi.innerHTML = featIcon(f);                 // アイコンのみHTML（データはテキストで入れる）
    s.appendChild(fi);
    s.appendChild(document.createTextNode(f.label));
    if (f.val) s.appendChild(el('b', null, f.val));
    row.appendChild(s);
  });
  return row;
}

/* 容量は「37L」→ 37+L、「23-32L」のような可変容量は一段小さく */
function capEl(cap) {
  const m = String(cap).match(/^([\d-]+)(L)$/);
  if (!m) return el('span', 'cap-num cap-long', cap);
  const e = el('span', 'cap-num' + (m[1].length >= 4 ? ' cap-long' : ''), m[1]);
  e.appendChild(el('small', null, m[2]));
  return e;
}

/* 車種を選んだ状態から商品ページへ渡すURL。
   商品ページ側は ?bike= があれば「この商品が装着できる車種」を出さず、
   選んだ車種の判定だけを見せる（他車種の一覧は不要なので）。 */
function productHref(item) {
  if (!isInternal(item.url) || !selectedBike) return item.url;
  return item.url + '?bike=' + encodeURIComponent(bikeKey(selectedBike));
}

function productCard(item, noteEl) {
  const info = CARDS[item.code] || null;
  const card = el('div', 'product-card');
  const link = document.createElement('a');
  link.href = productHref(item);
  if (!isInternal(item.url)) link.target = '_blank';
  link.className = 'card-link';

  const thumb = el('div', 'card-thumb');
  if (info && info.series) thumb.appendChild(el('span', 'badge', SERIES_JP[info.series] || info.series));
  if (info && info.status) {
    const b = el('span', 'new-badge', info.status);
    b.style.background = '#6b6b6b';
    thumb.appendChild(b);
  } else if (info && info.new) {
    thumb.appendChild(el('span', 'new-badge', 'New'));
  }
  const img = document.createElement('img');
  img.src = item.img;
  img.loading = 'lazy';
  img.alt = item.name;
  img.addEventListener('error', () => thumb.classList.add('noimg'));
  thumb.appendChild(img);
  link.appendChild(thumb);

  const body = el('div', 'card-body');
  if (info) {
    const head = el('div', 'card-head');
    head.appendChild(el('h3', 'card-code', info.label || info.code));
    if (info.cap) head.appendChild(capEl(info.cap));
    body.appendChild(head);

    const jp = el('p', 'card-jp', info.jp || '');
    if (info.colors > 1) {
      jp.appendChild(el('span', 'card-colors', '　' + info.colors + '色'));
    }
    body.appendChild(jp);

    if (info.copy) body.appendChild(el('p', 'card-copy', info.copy));
    const feats = featRow(info);
    if (feats) body.appendChild(feats);
  } else {
    body.appendChild(el('div', 'card-name', item.name));
  }
  body.appendChild(el('div', 'card-goto', '詳しく見る ›'));
  link.appendChild(body);

  card.appendChild(link);
  if (noteEl) card.appendChild(noteEl);
  return card;
}

/* 並び順は商品一覧と同じ「容量の大きいものから小さいものへ」。
   可変容量（23-32L）は上限で比べ、容量が無いものは末尾に回す。 */
function capValue(item) {
  const info = CARDS[item.code];
  const src = (info && info.cap) || item.capacity;
  if (src === undefined || src === null || src === '') return -1;
  const nums = String(src).match(/\d+/g);
  return nums ? Math.max.apply(null, nums.map(Number)) : -1;
}

function byCapacityDesc(a, b) {
  const d = capValue(b) - capValue(a);
  if (d) return d;
  const ka = a.code || a.name, kb = b.code || b.name;   // 同容量は型番順（商品一覧と同じ）
  return ka < kb ? -1 : (ka > kb ? 1 : 0);
}

/* 適合データはカラー違いのSKU単位。カードは商品一覧と同じくモデル単位で
   見せる（カラーはカード内の「2色」表記と商品ページで案内）ので、
   同じ型番が並ばないようまとめる。ベースプレート付属の情報は残す。 */
function byModel(items) {
  const map = new Map();
  items.forEach(item => {
    const key = item.code || item.name;
    const prev = map.get(key);
    if (!prev || (!prev.included && item.included)) map.set(key, item);
  });
  return [...map.values()];
}

function productGrid(items, noteBuilder) {
  const grid = el('div', 'product-grid');
  byModel(items).sort(byCapacityDesc)
    .forEach(item => grid.appendChild(productCard(item, noteBuilder ? noteBuilder(item) : null)));
  return grid;
}

// 全トップケースSKU（複数プレートに重複して現れるため名前で一意化）
function allTopcases() {
  const map = new Map();
  Object.values(PLATES).forEach(p => {
    p.topcases.forEach(tc => {
      if (!map.has(tc.name)) map.set(tc.name, tc);
    });
  });
  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name, 'ja'));
}

// 全サイドケースSKU（ハードケース）
function allSidecases() {
  return Object.values(SIDECASES).flat()
    .sort((a, b) => a.name.localeCompare(b.name, 'ja'));
}

// 全サイドバッグSKU（ソフトバッグ）
function allSidebags() {
  return Object.values(SIDEBAGS).flat()
    .sort((a, b) => a.name.localeCompare(b.name, 'ja'));
}

function renderAllProducts() {
  productTitle.textContent = '商品一覧';
  productSub.textContent = '車種を選択すると、適合する商品だけに絞り込まれます';
  productArea.innerHTML = '';

  // カテゴリで絞り込んでいるときは、そのセクションだけを出す
  [['top', allTopcases()], ['side', allSidecases()],
   ['sidebag', allSidebags()], ['tank', TANKBAGS]].forEach(([cat, source]) => {
    if (!showCategory(cat)) return;
    const items = byModel(applyFilters(source));
    const sec = el('div', 'product-section');
    sec.appendChild(sectionTitle(CATEGORY_LABEL[cat], items.length));
    if (items.length) sec.appendChild(productGrid(items));
    else sec.appendChild(el('div', 'no-fit', '絞り込み条件に合う商品はありません'));
    productArea.appendChild(sec);
  });
}

function buildTopSection(bike) {
  const sec = el('div', 'product-section');
  sec.appendChild(sectionTitle('トップケース'));

  if (bike.top.length === 0) {
    sec.appendChild(el('div', 'no-fit', 'この車種に適合するトップケース用フィッティングキットはありません'));
    return sec;
  }

  // 1つのキットが複数ベースプレートに対応するため、キットURL単位でまとめる
  const byUrl = new Map();
  bike.top.forEach(t => {
    if (!byUrl.has(t.url)) {
      byUrl.set(t.url, { plates: [], name: t.name, models: t.models, noPlate: t.noPlate });
    }
    const k = byUrl.get(t.url);
    k.plates.push(t.plate);
    if (t.models && !k.models) k.models = t.models;
    if (t.noPlate) k.noPlate = true;
  });

  /* 装着できるトップケースの決め方
     ① キットの仕様欄に「対応モデル」があればそれを正とする（マスター記載）
        例: シーシーバー取付 ※プレート付 → SH26/SH29/SH33/SH34（プレート不要）
     ② 記載が無ければ、対応ベースプレート配下のトップケースを集める */
  function resolveKitSkus(kit) {
    const skuMap = new Map();
    const plateCodes = kit.plates;
    const usablePlates = plateCodes.filter(pc => PLATES[pc]);
    if (kit.models && kit.models.indexOf('*') >= 0) {
      /* 「全てのSHAD＆TERRAトップケース/バッグに対応」と書かれたキット。
         対応ベースプレートが分かる場合は、そのプレートに載るケースだけを出す
         （プレートが物理的な制約。仕様欄の「全て」は総称表現で、54件はプレート指定と
          食い違うため、狭いほうに合わせる）。プレート不要のキットは全モデルを出す。 */
      if (usablePlates.length) {
        usablePlates.forEach(pc => {
          PLATES[pc].topcases.forEach(tc => {
            if (!skuMap.has(tc.name)) skuMap.set(tc.name, { ...tc, plates: [] });
            skuMap.get(tc.name).plates.push(pc);
          });
        });
      } else {
        Object.values(TOPCASE_BY_CODE).forEach(tc => {
          if (!skuMap.has(tc.name)) skuMap.set(tc.name, { ...tc, plates: [] });
        });
      }
    } else if (kit.models && kit.models.length) {
      kit.models.forEach(code => {
        const tc = TOPCASE_BY_CODE[code];
        if (tc && !skuMap.has(tc.name)) skuMap.set(tc.name, { ...tc, plates: [] });
      });
    } else {
      plateCodes.forEach(pc => {
        const plate = PLATES[pc];
        if (!plate) return;
        plate.topcases.forEach(tc => {
          if (!skuMap.has(tc.name)) skuMap.set(tc.name, { ...tc, plates: [] });
          skuMap.get(tc.name).plates.push(pc);
        });
      });
    }
    return skuMap;
  }

  const kits = [];
  byUrl.forEach((kit, url) => kits.push({ ...kit, url, skuMap: resolveKitSkus(kit) }));

  /* 商品一覧はキットごとに分けず、1つにまとめて出す。
     シーシーバー取付（※プレート別／※プレート付）のように同じ車種に複数の買い方が
     あるキットは、以前はキットごとにブロックを作っていたため同じトップケースが
     二重に並び、その間にキットの案内が割り込んで読みにくくなっていた。
     必要なキットはセクション先頭にまとめ、装着可能トップケースは重複を除いて1回だけ出す。 */
  const merged = new Map();
  kits.forEach(kit => {
    kit.skuMap.forEach((tc, name) => {
      if (!merged.has(name)) merged.set(name, { ...tc, plates: [], noPlate: false });
      const m = merged.get(name);
      (tc.plates || []).forEach(pc => { if (m.plates.indexOf(pc) < 0) m.plates.push(pc); });
      if (kit.noPlate) m.noPlate = true;   // プレート不要のキットでも装着できるモデル
    });
  });

  const allSkus = [...merged.values()].sort((a, b) => a.name.localeCompare(b.name, 'ja'));
  const skus = applyFilters(allSkus);
  if (allSkus.length && skus.length === 0) {
    sec.appendChild(el('div', 'no-fit', '絞り込み条件に合うトップケースはありません'));
    return sec;
  }

  const block = el('div', 'kit-block');
  block.appendChild(el('div', 'kit-line', kits.length > 1
    ? '取付には車種専用フィッティングキット（いずれか）が必要です：'
    : '取付には車種専用フィッティングキットが必要です：'));
  kits.forEach(kit => {
    const kitLine = el('div', 'kit-line');
    kitLine.appendChild(el('span', 'kit-name', kit.name));
    const btn = document.createElement('a');
    btn.href = kit.url;
    btn.target = '_blank';
    btn.className = 'kit-btn';
    btn.textContent = '商品を見る ›';
    kitLine.appendChild(btn);
    block.appendChild(kitLine);
  });

  // プレートコード不明のキット（plate=null のみ）は対応ケース一覧を出せないため商品ページへ誘導
  if (allSkus.length === 0) {
    block.appendChild(el('p', 'kit-note', kits.some(k => k.noPlate)
      ? 'このキットはベースプレート不要です（トップケースをキットに直接取り付けます）。'
        + '対応モデルはキットの商品ページでご確認ください。'
      : '装着できるトップケースは、キットに付属するベースプレートに準じます。'
        + '詳細はキットの商品ページでご確認ください。'));
    sec.appendChild(block);
    return sec;
  }

  block.appendChild(el('div', 'kit-caption', '装着可能トップケース'));
  block.appendChild(productGrid(skus, tc => {
    if (tc.included) return el('div', 'card-note ok', 'ベースプレート付属');
    // プレート不要のキットで装着できるモデルは、そのキットを選べばプレート購入が不要
    if (tc.noPlate && !tc.plates.length) {
      return el('div', 'card-note ok', 'ベースプレート不要（キットに直接取付）');
    }
    // ベースプレート別売：別途購入が必要なプレートへのリンクを併記
    const note = el('div', 'card-note',
      tc.noPlate ? '※プレート付キットなら不要／※プレート別の場合：' : '要ベースプレート（別売）：');
    tc.plates.forEach((pc, i) => {
      if (i > 0) note.appendChild(document.createTextNode(' / '));
      const plate = PLATES[pc];
      note.appendChild(productLink(plate.name, plate.url));
    });
    return note;
  }));
  sec.appendChild(block);
  return sec;
}

function buildSideSection(bike) {
  /* ハードケースとソフトバッグは同じサイドキットに紐づくため1セクションで扱う。
     カテゴリで絞り込んでいるときは見出しもその名前にする。 */
  const label = categoryFilter === 'sidebag' ? 'サイドバッグ' : 'サイドケース';
  const sec = el('div', 'product-section');
  sec.appendChild(sectionTitle(label));

  if (bike.side.length === 0) {
    sec.appendChild(el('div', 'no-fit', 'この車種に適合する' + label + '用フィッティングキットはありません'));
    return sec;
  }

  const SYSTEM_LABELS = { '3P': '3Pシステムフィッティングキット', '4P': '4Pシステムフィッティングキット',
                          'サイドバッグホルダー': 'サイドバッグホルダーキット',
                          'サイドバッグホルダーSR': 'SRバッグフィッティングキット' };
  let blockCount = 0;
  bike.side.forEach(s => {
    // cases はハードケース(SIDECASES)とソフトバッグ(SIDEBAGS)のコードが混在する
    const allSkus = s.cases.flatMap(code => SIDECASES[code] || SIDEBAGS[code] || []);
    // 絞り込み条件（カテゴリ/TERRA/容量）で該当がなくなった場合はこのキット自体を表示しない
    const skus = applyFilters(allSkus);
    if (filtersActive() && skus.length === 0) return;

    const block = el('div', 'kit-block');
    const kitTypeLabel = SYSTEM_LABELS[s.system] || (s.system + 'システムフィッティングキット');
    block.appendChild(el('div', 'kit-line', '取付には ' + kitTypeLabel + 'が必要です：'));
    const kitLine = el('div', 'kit-line');
    kitLine.appendChild(el('span', 'kit-name', s.name));
    const btn = document.createElement('a');
    btn.href = s.url;
    btn.target = '_blank';
    btn.className = 'kit-btn';
    btn.textContent = '商品を見る ›';
    kitLine.appendChild(btn);
    block.appendChild(kitLine);

    block.appendChild(el('div', 'kit-caption', '装着可能' + label));
    block.appendChild(productGrid(skus));
    sec.appendChild(block);
    blockCount++;
  });
  if (blockCount === 0) {
    sec.appendChild(el('div', 'no-fit', '絞り込み条件に合う' + label + 'はありません'));
  }
  return sec;
}

/* タンクバッグは車種専用キットが不要（クリックシステム）なので、
   車種を選んだ状態でカテゴリに「タンクバッグ」を選んだときだけ案内付きで出す。 */
function buildTankSection() {
  const items = byModel(applyFilters(TANKBAGS));
  const sec = el('div', 'product-section');
  sec.appendChild(sectionTitle('タンクバッグ', items.length));
  sec.appendChild(el('div', 'kit-line', 'タンクバッグは車種専用フィッティングキットが不要です（クリックシステム対応リングで装着します）'));
  if (items.length) sec.appendChild(productGrid(items));
  else sec.appendChild(el('div', 'no-fit', '絞り込み条件に合うタンクバッグはありません'));
  return sec;
}

function renderFilteredProducts(bike) {
  productTitle.textContent = bike.model + ' に適合する商品';
  productSub.textContent = '';
  productArea.innerHTML = '';
  if (showCategory('top')) productArea.appendChild(buildTopSection(bike));
  if (showCategory('side') || showCategory('sidebag')) productArea.appendChild(buildSideSection(bike));
  if (categoryFilter === 'tank') productArea.appendChild(buildTankSection());
}

function renderProducts() {
  if (selectedBike) {
    renderFilteredProducts(selectedBike);
  } else {
    renderAllProducts();
  }
}

// ---- 初期表示 ----
if (MODE === "entry") {
  // TOPでは検索フォームのみ（結果は /fitment で表示）
  root.querySelectorAll('.cat-filter, .filter-bar, #productTitle, #productSub, #productArea')
      .forEach(function (n) { n.remove(); });
  var go = document.createElement('button');
  go.type = 'button';
  go.className = 'btn bg-shad text-white hover:bg-[#c4151b] mt-5 w-full sm:w-auto justify-center';
  go.innerHTML = '<i class="ti ti-search"></i>適合を見る';
  go.disabled = true;
  go.addEventListener('click', function () {
    var b = pendingBike;
    if (b) location.href = RESULT_PAGE + "?bike=" + encodeURIComponent(bikeKey(b));
  });
  host.querySelector('.selector-panel').appendChild(go);
  window.__fsSetPending = function (bike) {
    pendingBike = bike;
    go.disabled = !bike;
    if (bike) {
      selectedModel.textContent = bike.model;
      selectedBar.classList.add('show');
    } else {
      selectedBar.classList.remove('show');
    }
  };
} else {
  // 結果ページ：URLの ?bike= を復元して表示
  var want = queryParam('bike');
  var target = want ? BIKES.filter(function (b) { return bikeKey(b) === want; })[0] : null;
  if (target) {
    selectedBike = target;
    selectedModel.textContent = target.model;
    selectedBar.classList.add('show');
    // プルダウンも選択状態に合わせる
    makerSelect.value = target.maker;
    makerSelect.dispatchEvent(new Event('change'));
    var gk = target.group || target.model;
    if ([].slice.call(seriesSelect.options).some(function (o) { return o.value === gk; })) {
      seriesSelect.value = gk;
      seriesSelect.dispatchEvent(new Event('change'));
      if ([].slice.call(modelSelect.options).some(function (o) { return o.value === target.model; })) {
        modelSelect.value = target.model;
      }
    }
  }
  renderProducts();
}
}

})();

/* =========================================================
   商品ページ（順引き）：この商品が装着できる車種
   [data-product-fitment-checker][data-product-code="TR55"] に描画。
   逆引きデータ（reverse_data.json）1本から導出する。
     トップケース … product_index.json で自コードのベースプレートを引き、
                    そのプレートに対応するキットを持つ車種を集める
     サイドケース／サイドバッグ … side[].cases に自コードを含む車種を集める
   ロジック（メーカー絞り込み・英語⇔カナ検索・シリーズ束ね）は
   提供実装 baseplateS.html / sidecaseS.html と同じ考え方。
   ========================================================= */
(function () {
  var root = document.querySelector("[data-product-fitment-checker]");
  if (!root) return;
  var code = (root.dataset.productCode || "").toUpperCase();
  if (!code) return;

  /* 適合検索から来た場合（?bike=メーカー|車種）は、他車種の一覧は不要なので
     このセクションを出さず、選んだ車種の判定だけを上部に表示する。
     判定できなかったときだけ通常のセレクターに戻す。 */
  var FROM_BIKE = (new URLSearchParams(location.search || "")).get("bike") || "";
  if (FROM_BIKE) root.style.display = "none";

  function showSelectedBike(rows, kitLabel) {
    var parts = FROM_BIKE.split("|");
    var maker = parts[0], model = parts.slice(1).join("|");
    var hit = null;
    rows.forEach(function (r) {
      if (!hit && r.maker === maker && r.model === model) hit = r;
    });
    if (!hit) { root.style.display = ""; return; }   // 判定できなければ通常表示に戻す

    var label = hit.system ? hit.system + "フィッティングキット"
                           : (kitLabel || "車種専用フィッティングキット");
    var box = document.createElement("div");
    box.className = "fit-from";
    box.innerHTML = ''
      + '<p class="fit-from-ok"><i class="ti ti-circle-check"></i>'
      +   '<span><b>' + esc(model) + '</b> に装着できます</span></p>'
      + '<p class="fit-from-kit">取付には車種専用の' + esc(label) + 'が必要です</p>'
      + '<div class="fit-from-btns">'
      +   '<a class="fit-from-kitbtn" href="' + esc(hit.url) + '" target="_blank" rel="noopener">'
      +     'キットを見る<i class="ti ti-arrow-right"></i></a>'
      +   '<a class="fit-from-back" href="/fitment?bike=' + encodeURIComponent(FROM_BIKE) + '">'
      +     '<i class="ti ti-arrow-left"></i>適合検索の結果に戻る</a>'
      + '</div>';

    // 「適合確認はこちら」ボタン（とその下の説明文）の位置に置き換える
    var jump = document.querySelector("[data-fit-jump]");
    var note = jump ? jump.nextElementSibling : null;
    if (note && note.tagName === "P") note.remove();
    if (jump && jump.parentNode) jump.parentNode.replaceChild(box, jump);
    else if (root.parentNode) root.parentNode.insertBefore(box, root);
    root.remove();
  }

  var MAIN = ["ホンダ", "ヤマハ", "スズキ", "カワサキ", "BMW"];
  var ALIASES = {
    forza: "フォルツァ", "africa twin": "アフリカツイン", transalp: "トランザルプ",
    tracer: "トレーサー", tenere: "テネレ", tricity: "トリシティ", xmax: "エックスマックス",
    burgman: "バーグマン", "v-strom": "vストローム", vstrom: "vストローム",
    versys: "ヴェルシス", ninja: "ニンジャ", rebel: "レブル", adventure: "アドベンチャー"
  };
  var SYSTEM_LABEL = {
    "3P": "3Pシステム", "4P": "4Pシステム",
    "サイドバッグホルダー": "サイドバッグホルダー",
    "サイドバッグホルダーSR": "SRバッグ"
  };

  function norm(s) { return String(s || "").toLowerCase(); }
  function expand(q) {
    var out = [norm(q)];
    Object.keys(ALIASES).forEach(function (en) {
      var ja = ALIASES[en];
      if (norm(q).indexOf(en) >= 0) out.push(norm(ja));
      if (norm(q).indexOf(norm(ja)) >= 0) out.push(en);
    });
    return out;
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function get(url) {
    return fetch(url).then(function (r) { return r.ok ? r.json() : null; })
                     .catch(function () { return null; });
  }

  Promise.all([get("/data/fitment/product_index.json"),
               get("/data/fitment/reverse_data.json")]).then(function (res) {
    var idx = res[0] || {}, data = res[1];
    if (!data) { root.style.display = ""; render([], null); return; }
    var plate = (idx.topcasePlate || {})[code];
    var rows = [], kitLabel = null;

    if (plate) {
      kitLabel = "トップマスターフィッティングキット";
      data.bikes.forEach(function (b) {
        var hit = (b.top || []).filter(function (t) { return t.plate === plate; })[0];
        if (hit) rows.push({ maker: b.maker, model: b.model, group: b.group, url: hit.url });
      });
    } else if ((idx.tankbagCodes || []).indexOf(code) >= 0) {
      /* タンクバッグはクリックシステムのキットで装着する。
         1つのキットが複数メーカー・複数車種にまたがる表記のため、
         車種単位のマッチングは行わずキット一覧を案内する（提供実装と同じ扱い）。
         車種別の一覧ではないので、適合検索から来た場合もそのまま表示する。 */
      if (FROM_BIKE) root.style.display = "";
      renderClickSystem(data.clicksystem_kits || []);
      return;
    } else {
      data.bikes.forEach(function (b) {
        (b.side || []).forEach(function (s) {
          if ((s.cases || []).indexOf(code) >= 0) {
            rows.push({ maker: b.maker, model: b.model, group: b.group, url: s.url,
                        system: SYSTEM_LABEL[s.system] || s.system });
          }
        });
      });
      if (rows.length) kitLabel = "車種専用フィッティングキット";
    }
    // 同一車種・同一キットの重複を除く
    var seen = {}, uniq = [];
    rows.forEach(function (r) {
      var k = r.model + "|" + r.url;
      if (!seen[k]) { seen[k] = 1; uniq.push(r); }
    });
    if (FROM_BIKE) { showSelectedBike(uniq, kitLabel); }
    if (root.isConnected) render(uniq, kitLabel);
  });

  /* タンクバッグ：クリックシステムのキット一覧（車種は各キットのページで確認）*/
  function renderClickSystem(kits) {
    var host = root.querySelector("[data-fitment-result]") || root;
    if (!kits.length) { render([], null); return; }
    var rows = kits.slice().sort(function (a, b) {
      return String(a.name).localeCompare(String(b.name), "ja");
    });
    host.innerHTML = ''
      + '<div class="fit-ok"><i class="ti ti-click"></i><div><p>クリックシステムで装着します</p>'
      +   '<span>タンクキャップに車種専用のクリックシステムフィッティングキットを取り付け、'
      +   'ワンタッチで着脱します。</span></div></div>'
      + '<p class="pf-count">車種専用キット ' + rows.length + ' 種（対応車種は各キットのページでご確認ください）</p>'
      + '<div class="pf-list">' + rows.map(function (k) {
          var makers = String(k.maker || "").replace(/_/g, " / ");
          return '<a class="pf-row" href="' + esc(k.url) + '" target="_blank" rel="noopener">'
            + '<span class="pf-model">' + esc(k.name) + '</span>'
            + (makers ? '<span class="pf-sys">' + esc(makers.slice(0, 28)) + '</span>' : '')
            + '<span class="pf-go">キットを見る<i class="ti ti-arrow-right"></i></span></a>';
        }).join("") + '</div>';
  }

  /* 商品ページの適合UI：メーカー → シリーズ → 車種 のプルダウンで選び、
     判定と必要なキットを表示する。全件の一覧は折りたたみで確認できる。 */
  function render(items, kitLabel) {
    var host = root.querySelector("[data-fitment-result]") || root;
    if (!items.length) {
      host.innerHTML = '<div class="fit-empty"><i class="ti ti-info-circle"></i>'
        + '<p>この商品の適合車種データは準備中です</p>'
        + '<span>お手数ですが、お問い合わせフォームよりご確認ください。</span></div>';
      return;
    }

    /* メーカー（国内4社＋BMWを先頭）→ シリーズ → 車種 の木を作る */
    var tree = {};
    items.forEach(function (i) {
      var mk = i.maker || "その他";
      var gp = i.group || i.model;
      (tree[mk] = tree[mk] || {});
      (tree[mk][gp] = tree[mk][gp] || []).push(i);
    });
    var makers = Object.keys(tree).sort(function (a, b) {
      var ia = MAIN.indexOf(a), ib = MAIN.indexOf(b);
      if (ia >= 0 || ib >= 0) return (ia < 0 ? 1 : ib < 0 ? -1 : ia - ib);
      return a.localeCompare(b, "ja");
    });

    host.innerHTML = ''
      + '<div class="pf-selects">'
      +   '<div><label class="finder-label">メーカー</label>'
      +     '<select class="finder-select" data-pf-maker><option value="">選択してください</option>'
      +       makers.map(function (m) {
              return '<option value="' + esc(m) + '">' + esc(m) + '</option>';
            }).join("")
      +     '</select></div>'
      +   '<div><label class="finder-label">シリーズ</label>'
      +     '<select class="finder-select" data-pf-series disabled><option value="">—</option></select></div>'
      +   '<div><label class="finder-label">車種・年式</label>'
      +     '<select class="finder-select" data-pf-model disabled><option value="">—</option></select></div>'
      + '</div>'
      + '<div class="pf-verdict" data-pf-verdict></div>'
      + '<details class="pf-all"><summary>'
      +   '<i class="ti ti-list" aria-hidden="true"></i>'
      +   '<span>適合車種の一覧を見る</span>'
      +   '<i class="ti ti-chevron-down pf-all-mark" aria-hidden="true"></i></summary>'
      +   '<div class="pf-all-body">'
      +     '<div class="pf-search"><i class="ti ti-search" aria-hidden="true"></i>'
      +       '<input type="text" data-pf-input placeholder="車種名で絞り込む（例：PCX、Vストローム、Africa Twin）"></div>'
      +     '<p class="pf-count" data-pf-count></p>'
      +     '<div class="pf-list" data-pf-list></div>'
      +   '</div>'
      + '</details>';

    var mkSel = host.querySelector("[data-pf-maker]");
    var seSel = host.querySelector("[data-pf-series]");
    var mdSel = host.querySelector("[data-pf-model]");
    var verdict = host.querySelector("[data-pf-verdict]");

    function fill(sel, opts, placeholder) {
      sel.innerHTML = '<option value="">' + placeholder + '</option>'
        + opts.map(function (o) {
            return '<option value="' + esc(o.value) + '">' + esc(o.label) + '</option>';
          }).join("");
      sel.disabled = !opts.length;
    }

    mkSel.addEventListener("change", function () {
      var mk = mkSel.value;
      verdict.innerHTML = "";
      if (!mk) { fill(seSel, [], "—"); fill(mdSel, [], "—"); return; }
      var groups = Object.keys(tree[mk]).sort(function (a, b) { return a.localeCompare(b, "ja"); });
      fill(seSel, groups.map(function (g) {
        return { value: g, label: g };
      }), "選択してください");
      fill(mdSel, [], "—");
    });

    seSel.addEventListener("change", function () {
      verdict.innerHTML = "";
      var list = (tree[mkSel.value] || {})[seSel.value] || [];
      fill(mdSel, list.map(function (i) { return { value: i.model, label: i.model }; }),
           "選択してください");
      if (list.length === 1) { mdSel.value = list[0].model; showVerdict(); }
    });

    mdSel.addEventListener("change", showVerdict);

    function showVerdict() {
      var list = (tree[mkSel.value] || {})[seSel.value] || [];
      var hit = list.filter(function (i) { return i.model === mdSel.value; })[0];
      if (!hit) { verdict.innerHTML = ""; return; }
      verdict.innerHTML = ''
        + '<div class="fit-ok"><i class="ti ti-circle-check"></i>'
        +   '<div><p>装着できます</p>'
        +   '<span>' + esc(hit.model) + '</span></div></div>'
        + '<div class="pf-kit">'
        +   '<p class="pf-kit-cap">取付に必要な車種専用フィッティングキット'
        +     (hit.system ? '（' + esc(hit.system) + '）' : '') + '</p>'
        +   '<a class="pf-kit-btn" href="' + esc(hit.url) + '" target="_blank" rel="noopener">'
        +     'キットを見る<i class="ti ti-arrow-up-right"></i></a>'
        + '</div>';
    }

    /* 折りたたみ内の全件一覧（キーワード絞り込み付き）*/
    var listEl = host.querySelector("[data-pf-list]");
    var countEl = host.querySelector("[data-pf-count]");
    var input = host.querySelector("[data-pf-input]");

    function draw() {
      var q = input.value.trim();
      var qs = q ? expand(q) : null;
      var rows = items.filter(function (i) {
        if (!qs) return true;
        var t = norm(i.model) + " " + norm(i.maker) + " " + norm(i.group);
        return qs.some(function (x) { return x && t.indexOf(x) >= 0; });
      });
      countEl.textContent = kitLabel ? "取付には車種専用の" + kitLabel + "が必要です" : "";
      var groups = {};
      rows.forEach(function (r) {
        var k = (r.maker || "") + " / " + (r.group || r.model);
        (groups[k] = groups[k] || []).push(r);
      });
      var keys = Object.keys(groups).sort(function (a, b) { return a.localeCompare(b, "ja"); });
      listEl.innerHTML = keys.length ? keys.map(function (k) {
        return '<div class="pf-group"><p class="pf-group-ttl">' + esc(k) + '</p>'
          + groups[k].map(function (r) {
              return '<a class="pf-row" href="' + esc(r.url) + '" target="_blank" rel="noopener">'
                + '<span class="pf-model">' + esc(r.model) + '</span>'
                + (r.system ? '<span class="pf-sys">' + esc(r.system) + '</span>' : '')
                + '<span class="pf-go">キットを見る<i class="ti ti-arrow-right"></i></span></a>';
            }).join("") + '</div>';
      }).join("") : '<div class="fit-empty"><i class="ti ti-search-off"></i>'
                    + '<p>該当する車種がありません</p>'
                    + '<span>キーワードを変えてお試しください。</span></div>';
    }
    input.addEventListener("input", draw);
    draw();
  }
})();
