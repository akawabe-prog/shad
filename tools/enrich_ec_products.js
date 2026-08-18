#!/usr/bin/env node
/* =========================================================
   SHAD JAPAN — enrich_ec_products.js
   本体商品（26モデル）＋フィッティングキットの CustomJapan EC データを API取得。
   eXs実装 / enrich_fitment_products.js と同じパターン：
     1) moto.customjapan.net/i/<code> を1件開いて auth クッキー取得
     2) POST https://api-e.customjapan.net/api/v1/items {ids:[...]}
   取得値：price.list.taxIn=メーカー希望小売価格(MSRP) / price.regular.pc.taxIn=公開通常価格
   出力：
     - site/js/ec_links.js                  window.SHAD_EC（URLマップ／価格を含まない）
   ★販売価格を含む出力は公開フォルダ（site/）の外に置く。ブランドサイトは定価のみ表示。
     - data-source/ec_internal/ec_products.json    本体（code/cjCode/url/title/msrp/price/status/image）
     - data-source/ec_internal/fitting_prices.json フィッティング {cjCode:{msrpTaxIn,priceTaxIn}}
     - data-source/ec_internal/ec_products.js      window.SHAD_EC_DATA（社内確認用。サイトは読み込まない）
   ========================================================= */
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFile } = require("child_process");

const root = path.resolve(__dirname, "..");
// 販売価格を含む出力先は公開フォルダの外（data-source/ は .gitignore 対象）
const dataDir = path.join(root, "data-source", "ec_internal");
const fitmentIndexFile = path.join(root, "site", "data", "fitment", "fitment_index.json");
const jsonOut = path.join(dataDir, "ec_products.json");
const fittingPricesOut = path.join(dataDir, "fitting_prices.json");
const linksOut = path.join(root, "site", "js", "ec_links.js");
const dataJsOut = path.join(dataDir, "ec_products.js");
const apiUrl = "https://api-e.customjapan.net/api/v1/items";
const itemBaseUrl = "https://moto.customjapan.net/i/";
const cookieFile = path.join(os.tmpdir(), `shad-ec-api-${process.pid}.cookies`);

// 全26モデル → 代表本体SKU品番（CJ商品コード）。空 = EC未掲載/廃番（準備中）。
const CODE_TO_CJ = {
  SH23: "13210847", SH33: "10652824", SH34: "17838542", SH38X: "27952924",
  SH44: "27587515", SH47: "26591735", SH48: "17164078", SH51: "29468997",
  SH58X: "17319140",
  TR10: "28032793", TR27: "29469017", TR30: "28087540", TR36: "18319293",
  TR37: "18319286", TR41: "29044382", TR46: "29351718", TR47: "18319316",
  TR48: "18319279", TR50: "27819630", TR55: "27705902",
  E48: "28020653", LOCK: "27294062", SEAT: "17379793",
  // 本体EC未掲載/廃番のため準備中（要手動確認）：
  TR40: "",
};

function runCurl(curlArgs, maxBuffer = 16 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    execFile("curl", curlArgs, { maxBuffer }, (error, stdout, stderr) => {
      if (error) { error.message = `${error.message}${stderr ? `: ${stderr.trim()}` : ""}`; reject(error); }
      else resolve(stdout);
    });
  });
}

function priceTaxIn(item) {
  return Number(item?.price?.regular?.pc?.taxIn ?? item?.price?.regular?.taxIn ?? item?.priceTaxIn ?? 0);
}
function msrpTaxIn(item) {
  // メーカー希望小売価格 = price.list.taxIn（無ければ regular にフォールバック）
  return Number(item?.price?.list?.taxIn ?? item?.price?.regular?.pc?.taxIn ?? 0);
}

function normalizeMain(code, item) {
  const cjCode = String(item.id || "");
  return {
    code,
    cjCode,
    url: `${itemBaseUrl}${cjCode}`,
    title: item.name || "",
    maker: item?.maker?.name || "",
    category: item?.category?.name || "",
    msrpTaxIn: msrpTaxIn(item),
    priceTaxIn: priceTaxIn(item),
    status: item?.status?.txt || "",
    image: `img/products/${code.toLowerCase()}.jpg`, // ブランド側の看板画像（既存）
    fetchedAt: new Date().toISOString(),
  };
}

async function bootstrapSession(firstCode) {
  await runCurl(["-sSL", "--fail", "--max-time", "30", "-c", cookieFile, "-o", "/dev/null", `${itemBaseUrl}${firstCode}`]);
}

async function fetchItems(codes) {
  const stdout = await runCurl([
    "-sSL", "--fail", "--max-time", "60", "-b", cookieFile,
    "-X", "POST", apiUrl,
    "-H", "Origin: https://moto.customjapan.net",
    "-H", "Referer: https://moto.customjapan.net/",
    "-H", "Content-Type: application/json",
    "--data", JSON.stringify({ ids: codes }),
  ]);
  const json = JSON.parse(stdout);
  if (json.result !== "success" || !Array.isArray(json.data)) {
    throw new Error(`items API failed: ${json?.errors?.[0]?.cd || "unknown"}`);
  }
  return json.data;
}

async function fetchInBatches(codes, size = 50) {
  const out = [];
  for (let i = 0; i < codes.length; i += size) {
    const batch = codes.slice(i, i + size);
    const data = await fetchItems(batch);
    out.push(...data);
    console.log(`  ${Math.min(i + size, codes.length)}/${codes.length} fetched`);
  }
  return out;
}

function writeLinksJs(rows) {
  const order = Object.keys(CODE_TO_CJ);
  const byCode = Object.fromEntries(rows.map((r) => [r.code, r]));
  const urlLines = order.map((c) => {
    const r = byCode[c];
    return r ? `  "${c}": "${r.url}",` : `  "${c}": "", // 準備中：EC本体SKU未確定`;
  }).join("\n");
  fs.writeFileSync(linksOut,
`/* =========================================================
   SHAD JAPAN — ec_links.js  ※自動生成 (tools/enrich_ec_products.js)
   「この商品を購入する」ボタンの飛び先 URL マップ。空 = 準備中（無効表示）。
   詳細データ（MSRP/在庫/タイトル/画像）は ec_products.js / ec_products.json。
   ========================================================= */
window.SHAD_EC = {
${urlLines}
};
`, "utf8");
}

function writeDataJs(rows) {
  const map = {};
  rows.forEach((r) => {
    map[r.code] = { url: r.url, title: r.title, msrpTaxIn: r.msrpTaxIn, priceTaxIn: r.priceTaxIn, status: r.status, image: r.image };
  });
  fs.writeFileSync(dataJsOut,
`/* SHAD JAPAN — ec_products.js  ※自動生成 (tools/enrich_ec_products.js)
   window.SHAD_EC_DATA[code] = { url, title, msrpTaxIn, priceTaxIn, status, image } */
window.SHAD_EC_DATA = ${JSON.stringify(map, null, 2)};
`, "utf8");
}

async function main() {
  fs.mkdirSync(dataDir, { recursive: true });
  const entries = Object.entries(CODE_TO_CJ).filter(([, cj]) => cj);
  const mainCodes = entries.map(([, cj]) => cj);

  console.log(`[1/2] 本体商品 ${mainCodes.length} 件を取得 ...`);
  await bootstrapSession(mainCodes[0]);
  const mainItems = await fetchItems(mainCodes);
  const mainById = Object.fromEntries(mainItems.map((it) => [String(it.id), it]));
  const rows = [];
  for (const [code, cj] of entries) {
    const it = mainById[cj];
    if (it) rows.push(normalizeMain(code, it));
  }
  rows.sort((a, b) => a.code.localeCompare(b.code));
  fs.writeFileSync(jsonOut, `${JSON.stringify(rows, null, 2)}\n`, "utf8");
  writeLinksJs(rows);
  writeDataJs(rows);
  rows.forEach((r) => console.log(`  ${r.code.padEnd(6)} 希望小売 ${String(r.msrpTaxIn).padStart(7)}円 / 販売 ${String(r.priceTaxIn).padStart(7)}円 ${r.status}`));

  // フィッティングキットのMSRP
  console.log(`[2/2] フィッティングキットのMSRPを取得 ...`);
  let fittingPrices = {};
  try {
    const idx = JSON.parse(fs.readFileSync(fitmentIndexFile, "utf8"));
    const cjCodes = [...new Set((idx.fittingProducts || []).map((p) => String(p.cjCode)).filter(Boolean))];
    console.log(`  fitting cjCodes: ${cjCodes.length}`);
    const items = await fetchInBatches(cjCodes, 50);
    items.forEach((it) => {
      fittingPrices[String(it.id)] = { msrpTaxIn: msrpTaxIn(it), priceTaxIn: priceTaxIn(it) };
    });
    fs.writeFileSync(fittingPricesOut, `${JSON.stringify(fittingPrices, null, 1)}\n`, "utf8");
    console.log(`  fitting prices saved: ${Object.keys(fittingPrices).length}`);
  } catch (e) {
    console.warn("  フィッティング価格の取得をスキップ:", e.message);
  }

  console.log(`\nOK: 本体 ${rows.length} 件 / フィッティング ${Object.keys(fittingPrices).length} 件`);
  const preparing = Object.entries(CODE_TO_CJ).filter(([, cj]) => !cj).map(([c]) => c);
  if (preparing.length) console.log("準備中（EC未掲載/廃番）:", preparing.join(", "));
  try { fs.unlinkSync(cookieFile); } catch (_) {}
}

main().catch((e) => { console.error(e); process.exit(1); });
