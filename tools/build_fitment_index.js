#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const defaultSource = path.join("/private/tmp", "shad-fitting-inspect", "dist");
const sourceDir = process.argv[2] ? path.resolve(process.argv[2]) : defaultSource;
const outDir = path.join(root, "site", "data", "fitment");
const outFile = path.join(outDir, "fitment_index.json");
const outScriptFile = path.join(outDir, "fitment_index.js");
const fittingProductsFile = path.join(outDir, "fitting_products.json");

const topcaseBaseplates = {
  D1B29PAR: {
    products: ["SH26", "SH29", "SH33", "SH34"],
    label: "ベースプレートS",
  },
  D1B40PAR: {
    products: ["SH39", "SH40", "SH40CG", "SH44", "SH45", "SH47", "TR41", "TR46"],
    label: "ベースプレートM",
  },
  D1B591PA: {
    products: ["SH48", "SH51", "SH58X", "SH59X"],
    label: "ベースプレートL 樹脂製",
  },
  D1BTRPA2: {
    products: ["TR37", "TR48", "TR55"],
    label: "アルミ製ベースプレートL ブラック",
  },
  D1BTRPA: {
    products: ["TR37", "TR48", "TR55"],
    label: "アルミ製ベースプレートL シルバー",
  },
};

const sidecaseCodes = ["SH23", "SH35", "SH36", "SH38X"];

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function uniq(items) {
  return [...new Set(items.filter(Boolean))];
}

function normalizeText(value) {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[‐-‒–—ー−]/g, "-")
    .replace(/\s+/g, " ")
    .trim();
}

function stripYearRanges(label) {
  return String(label || "")
    .replace(/[\(（][^)）]*[\)）]/g, "")
    .replace(/\[[^\]]*]/g, "")
    .replace(/\s*｜\s*/g, " / ")
    .replace(/\s+/g, " ")
    .trim();
}

function extractYearLabel(label) {
  const text = String(label || "");
  const ranges = [];
  const parens = text.match(/[\(（][^)）]*[\)）]/g) || [];
  parens.forEach((item) => ranges.push(item.replace(/[()（）]/g, "")));
  const brackets = text.match(/\[[^\]]*]/g) || [];
  brackets.forEach((item) => ranges.push(item.replace(/[[\]]/g, "")));
  return uniq(ranges).join(" / ") || "適合年式";
}

function productUrl(code) {
  return `product-${code.toLowerCase()}.html`;
}

function productLabel(product) {
  if (!product) return "";
  return [product.series, product.jp].filter(Boolean).join(" / ");
}

function fittingProductFor(url) {
  if (!url) return null;
  let code = "";
  try {
    code = decodeURIComponent(new URL(url).pathname.split("/").filter(Boolean).pop() || "");
  } catch (_) {
    return null;
  }
  return fittingProductByCode.get(code) || null;
}

function withFittingProduct(fitment) {
  const fittingProduct = fittingProductFor(fitment.fittingUrl);
  return fittingProduct ? { ...fitment, fittingProductCode: fittingProduct.cjCode } : fitment;
}

function fitmentKey(row) {
  return [
    row.maker,
    row.displayModel,
    row.yearLabel,
    row.fitments
      .map((fit) => `${fit.productCode}:${fit.baseplateCode || fit.system || ""}:${fit.fittingUrl || ""}`)
      .sort()
      .join(","),
  ].join("|");
}

function mergeFitment(target, fitment) {
  const exists = target.fitments.some((item) => {
    return (
      item.productCode === fitment.productCode &&
      item.baseplateCode === fitment.baseplateCode &&
      item.system === fitment.system &&
      item.fittingUrl === fitment.fittingUrl
    );
  });
  if (!exists) target.fitments.push(fitment);
}

const products = readJson(path.join(root, "site", "products_data.json"));
const fittingProducts = fs.existsSync(fittingProductsFile) ? readJson(fittingProductsFile) : [];
const fittingProductByCode = new Map(
  fittingProducts.map((product) => [String(product.cjCode || ""), product])
);
const productByCode = new Map(products.map((product) => [product.code, product]));
const knownProductCodes = new Set(products.map((product) => product.code));
const rows = [];
const sourceProductCandidates = [];
const coverage = {
  sourceProducts: [],
  siteProductsCovered: [],
  siteProductsUnsupported: [],
  sourceOnlyProducts: [],
};

Object.entries(topcaseBaseplates).forEach(([baseplateCode, config]) => {
  const file = path.join(sourceDir, `topcase_${baseplateCode}.json`);
  if (!fs.existsSync(file)) return;
  const sourceRows = readJson(file);
  config.products.forEach((productCode) => {
    sourceProductCandidates.push(productCode);
    if (!knownProductCodes.has(productCode)) return;
    sourceRows.forEach((source) => {
      const product = productByCode.get(productCode);
      const displayModel = source.model;
      rows.push({
        maker: source.maker,
        displayModel,
        modelKey: stripYearRanges(displayModel) || displayModel,
        yearLabel: extractYearLabel(displayModel),
        group: source.group || "",
        searchText: normalizeText([source.maker, displayModel, source.group, productCode].join(" ")),
        fitments: [
          withFittingProduct({
            productCode,
            productName: product ? `${product.code} ${product.jp}` : productCode,
            productSeries: product ? product.series : "",
            productLabel: productLabel(product),
            productImage: product ? product.img : "",
            productUrl: productUrl(productCode),
            category: "topcase",
            mountType: "トップケース",
            baseplateCode,
            baseplateName: config.label,
            fittingUrl: source.url,
            fittingName: source.model,
            system: "",
            discontinued: false,
          }),
        ],
      });
    });
  });
});

const sidecaseFile = path.join(sourceDir, "sidecase_data.json");
if (fs.existsSync(sidecaseFile)) {
  const sideRows = readJson(sidecaseFile);
  sidecaseCodes.forEach((productCode) => {
    sourceProductCandidates.push(productCode);
    if (!knownProductCodes.has(productCode)) return;
    sideRows
      .filter((source) => source.cases.includes(productCode))
      .forEach((source) => {
        const product = productByCode.get(productCode);
        const displayModel = source.name || source.models;
        rows.push({
          maker: source.maker,
          displayModel,
          modelKey: stripYearRanges(displayModel) || displayModel,
          yearLabel: extractYearLabel(source.models || displayModel),
          group: source.group || "",
          searchText: normalizeText(
            [source.maker, source.name, source.models, source.group, source.system, productCode].join(" ")
          ),
          fitments: [
            withFittingProduct({
              productCode,
              productName: product ? `${product.code} ${product.jp}` : productCode,
              productSeries: product ? product.series : "",
              productLabel: productLabel(product),
              productImage: product ? product.img : "",
              productUrl: productUrl(productCode),
              category: "sidecase",
              mountType: "サイドケース",
              baseplateCode: "",
              baseplateName: "",
              fittingUrl: source.url,
              fittingName: source.name,
              system: source.system,
              discontinued: Boolean(source.discontinued),
            }),
          ],
        });
      });
  });
}

const merged = new Map();
rows.forEach((row) => {
  const key = [row.maker, row.displayModel, row.yearLabel].join("|");
  if (!merged.has(key)) {
    merged.set(key, {
      id: Buffer.from(key).toString("base64url"),
      maker: row.maker,
      displayModel: row.displayModel,
      modelKey: row.modelKey,
      yearLabel: row.yearLabel,
      group: row.group,
      searchText: row.searchText,
      fitments: [],
    });
  }
  row.fitments.forEach((fitment) => mergeFitment(merged.get(key), fitment));
});

const vehicles = [...merged.values()].sort((a, b) => {
  return `${a.maker} ${a.modelKey} ${a.yearLabel}`.localeCompare(
    `${b.maker} ${b.modelKey} ${b.yearLabel}`,
    "ja"
  );
});

const sourceProducts = uniq(sourceProductCandidates).sort();
coverage.sourceProducts = sourceProducts;
coverage.siteProductsCovered = products
  .map((product) => product.code)
  .filter((code) => sourceProducts.includes(code))
  .sort();
coverage.siteProductsUnsupported = products
  .map((product) => product.code)
  .filter((code) => !sourceProducts.includes(code))
  .sort();
coverage.sourceOnlyProducts = sourceProducts.filter((code) => !knownProductCodes.has(code)).sort();

const index = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  source: {
    description: "Generated from shad-fitting.zip dist JSON files.",
    sourceDir,
  },
  coverage,
  products,
  fittingProducts,
  vehicles,
};

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(outFile, `${JSON.stringify(index, null, 2)}\n`, "utf8");
fs.writeFileSync(
  outScriptFile,
  `window.SHAD_FITMENT_INDEX = ${JSON.stringify(index)};\n`,
  "utf8"
);

console.log(`Wrote ${vehicles.length} vehicle rows to ${path.relative(root, outFile)}`);
console.log(`Wrote script fallback to ${path.relative(root, outScriptFile)}`);
console.log(`Covered site products: ${coverage.siteProductsCovered.join(", ")}`);
console.log(`Unsupported site products: ${coverage.siteProductsUnsupported.join(", ")}`);
