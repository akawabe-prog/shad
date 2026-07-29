#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFile } = require("child_process");

const root = path.resolve(__dirname, "..");
const indexFile = path.join(root, "site", "data", "fitment", "fitment_index.json");
const outputFile = path.join(root, "site", "data", "fitment", "fitting_products.json");
const missingOutputFile = path.join(root, "site", "data", "fitment", "fitting_products_missing.json");
const imageDir = path.join(root, "site", "img", "fitment");
const apiUrl = "https://api-e.customjapan.net/api/v1/items";
const itemBaseUrl = "https://moto.customjapan.net/i/";
const imageBaseUrl = "https://img.customjapan.net";

const args = process.argv.slice(2);
const limitArg = args.find((arg) => arg.startsWith("--limit="));
const batchArg = args.find((arg) => arg.startsWith("--batch-size="));
const concurrencyArg = args.find((arg) => arg.startsWith("--concurrency="));
const refresh = args.includes("--refresh");
const limit = limitArg ? Number(limitArg.split("=")[1]) : Infinity;
const batchSize = batchArg ? Math.max(1, Number(batchArg.split("=")[1])) : 50;
const concurrency = concurrencyArg ? Math.max(1, Number(concurrencyArg.split("=")[1])) : 8;
const cookieFile = path.join(os.tmpdir(), `shad-fitment-api-${process.pid}.cookies`);

function runCurl(curlArgs, maxBuffer = 16 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    execFile("curl", curlArgs, { maxBuffer }, (error, stdout, stderr) => {
      if (error) {
        error.message = `${error.message}${stderr ? `: ${stderr.trim()}` : ""}`;
        reject(error);
      } else {
        resolve(stdout);
      }
    });
  });
}

function cjCodeFromUrl(url) {
  try {
    return decodeURIComponent(new URL(url).pathname.split("/").filter(Boolean).pop() || "");
  } catch (_) {
    return "";
  }
}

function imageExtension(imageUrl) {
  try {
    const ext = path.extname(new URL(imageUrl).pathname).toLowerCase();
    return [".jpg", ".jpeg", ".png", ".webp"].includes(ext) ? ext : ".jpg";
  } catch (_) {
    return ".jpg";
  }
}

function readExisting() {
  if (!fs.existsSync(outputFile)) return {};
  const rows = JSON.parse(fs.readFileSync(outputFile, "utf8"));
  return Object.fromEntries(rows.map((row) => [row.cjCode, row]));
}

function readMissing() {
  if (!fs.existsSync(missingOutputFile)) return {};
  const rows = JSON.parse(fs.readFileSync(missingOutputFile, "utf8"));
  return Object.fromEntries(rows.map((row) => [row.cjCode, row]));
}

function writeRows(cache) {
  const rows = Object.values(cache).sort((a, b) => a.cjCode.localeCompare(b.cjCode, "ja"));
  fs.writeFileSync(outputFile, `${JSON.stringify(rows, null, 2)}\n`, "utf8");
}

function priceTaxIn(item) {
  return Number(
    item?.price?.regular?.pc?.taxIn
      ?? item?.price?.regular?.taxIn
      ?? item?.price?.list?.taxIn
      ?? item?.priceTaxIn
      ?? 0
  );
}

function normalizeItem(item, urlByCode) {
  const cjCode = String(item.id || "");
  const imagePath = item?.img?.l || item?.img?.s || "";
  const sourceImageUrl = imagePath
    ? (imagePath.startsWith("http") ? imagePath : `${imageBaseUrl}${imagePath}`)
    : "";
  const ext = imageExtension(sourceImageUrl);
  return {
    cjCode,
    url: urlByCode[cjCode] || `${itemBaseUrl}${cjCode}`,
    title: item.name || "",
    maker: item?.maker?.name || "",
    category: item?.category?.name || "",
    catch: item.catch || "",
    fit: Array.isArray(item.fit) ? item.fit.join(" / ") : String(item.fit || ""),
    priceTaxIn: priceTaxIn(item),
    status: item?.status?.txt || "",
    sourceImageUrl,
    image: sourceImageUrl ? `img/fitment/${cjCode}${ext}` : "",
    fetchedAt: new Date().toISOString(),
  };
}

async function bootstrapSession(firstCode) {
  await runCurl([
    "-sSL",
    "--fail",
    "--max-time",
    "30",
    "-c",
    cookieFile,
    "-o",
    "/dev/null",
    `${itemBaseUrl}${firstCode}`,
  ]);
}

async function fetchBatch(codes, urlByCode) {
  const stdout = await runCurl([
    "-sSL",
    "--fail",
    "--max-time",
    "60",
    "-b",
    cookieFile,
    "-X",
    "POST",
    apiUrl,
    "-H",
    "Origin: https://moto.customjapan.net",
    "-H",
    "Referer: https://moto.customjapan.net/",
    "-H",
    "Content-Type: application/json",
    "--data",
    JSON.stringify({ ids: codes }),
  ]);
  const json = JSON.parse(stdout);
  if (json.result !== "success" || !Array.isArray(json.data)) {
    const code = json?.errors?.[0]?.cd || "unknown";
    throw new Error(`items API failed: ${code}`);
  }
  return json.data.map((item) => normalizeItem(item, urlByCode));
}

async function fetchBatchSafely(codes, urlByCode, failedCodes) {
  try {
    return await fetchBatch(codes, urlByCode);
  } catch (error) {
    if (codes.length === 1) {
      failedCodes.push({ cjCode: codes[0], error: error.message });
      console.error(`API item skipped: ${codes[0]} (${error.message})`);
      return [];
    }
    const midpoint = Math.ceil(codes.length / 2);
    const left = await fetchBatchSafely(codes.slice(0, midpoint), urlByCode, failedCodes);
    const right = await fetchBatchSafely(codes.slice(midpoint), urlByCode, failedCodes);
    return left.concat(right);
  }
}

async function downloadImages(rows) {
  let cursor = 0;
  let downloaded = 0;
  let failed = 0;

  async function worker() {
    while (cursor < rows.length) {
      const row = rows[cursor++];
      if (!row.sourceImageUrl || !row.image) continue;
      const imagePath = path.join(root, "site", row.image);
      if (!refresh && fs.existsSync(imagePath)) continue;
      try {
        await runCurl([
          "-sSL",
          "--fail",
          "--max-time",
          "45",
          "-o",
          imagePath,
          row.sourceImageUrl,
        ], 2 * 1024 * 1024);
        downloaded++;
        if (downloaded % 25 === 0) console.log(`${downloaded} images downloaded`);
      } catch (error) {
        failed++;
        row.image = "";
        console.error(`Image failed: ${row.cjCode} (${error.message})`);
      }
    }
  }

  await Promise.all(Array.from({ length: Math.min(concurrency, rows.length) }, worker));
  return { downloaded, failed };
}

async function main() {
  const index = JSON.parse(fs.readFileSync(indexFile, "utf8"));
  const urls = [...new Set(index.vehicles.flatMap((vehicle) => {
    return vehicle.fitments.map((fitment) => fitment.fittingUrl).filter(Boolean);
  }))].slice(0, limit);
  const urlByCode = Object.fromEntries(urls.map((url) => [cjCodeFromUrl(url), url]));
  const codes = Object.keys(urlByCode).filter(Boolean);
  const cache = readExisting();
  const codesToFetch = refresh ? codes : codes.filter((code) => !cache[code]);
  const missingCache = readMissing();
  const failedCodes = [];
  codesToFetch.forEach((code) => {
    delete missingCache[code];
  });

  if (!codes.length) {
    console.log("No fitting product IDs found.");
    return;
  }

  fs.mkdirSync(imageDir, { recursive: true });
  await bootstrapSession(codes[0]);

  for (let offset = 0; offset < codesToFetch.length; offset += batchSize) {
    const batch = codesToFetch.slice(offset, offset + batchSize);
    const rows = await fetchBatchSafely(batch, urlByCode, failedCodes);
    rows.forEach((row) => {
      cache[row.cjCode] = row;
    });
    writeRows(cache);
    console.log(`${Math.min(offset + batch.length, codesToFetch.length)}/${codesToFetch.length} API items fetched`);
  }

  const selectedRows = codes.map((code) => cache[code]).filter(Boolean);
  const imageResult = await downloadImages(selectedRows);
  writeRows(cache);
  failedCodes.forEach((row) => {
    missingCache[row.cjCode] = row;
  });
  fs.writeFileSync(
    missingOutputFile,
    `${JSON.stringify(
      Object.values(missingCache).sort((a, b) => a.cjCode.localeCompare(b.cjCode)),
      null,
      2
    )}\n`,
    "utf8"
  );
  fs.rmSync(cookieFile, { force: true });
  console.log(
    `Done: ${selectedRows.length} products, ${imageResult.downloaded} images downloaded, `
      + `${imageResult.failed} image failures, ${failedCodes.length} API items skipped`
  );
}

main().catch((error) => {
  fs.rmSync(cookieFile, { force: true });
  console.error(error);
  process.exit(1);
});
