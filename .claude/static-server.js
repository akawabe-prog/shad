#!/usr/bin/env node
/* =========================================================
   SHAD JAPAN — 確認用ローカルサーバー（開発専用・本番では使いません）
   site/ を配信し、本番と同じクリーンURL（/fitment → fitment.html、
   /product/tr55 → product/tr55.html）を再現します。
   起動: node .claude/static-server.js  （既定 http://localhost:8742）
   ========================================================= */
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "site");
const PORT = Number(process.env.PORT || 8742);

const MIME = {
  ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
  ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon",
  ".woff2": "font/woff2", ".mp4": "video/mp4", ".webm": "video/webm",
  ".txt": "text/plain; charset=utf-8", ".xml": "application/xml; charset=utf-8",
};

function resolveFile(urlPath) {
  const clean = decodeURIComponent(urlPath.split("?")[0].split("#")[0]);
  // ディレクトリトラバーサル防止
  const rel = path.normalize(clean).replace(/^(\.\.[/\\])+/, "");
  const base = path.join(ROOT, rel);
  const candidates = [];
  if (clean.endsWith("/")) {
    candidates.push(path.join(base, "index.html"));
  } else {
    candidates.push(base, base + ".html", path.join(base, "index.html"));
  }
  for (const p of candidates) {
    if (!p.startsWith(ROOT)) continue;
    try { if (fs.statSync(p).isFile()) return p; } catch (_) {}
  }
  return null;
}

http.createServer((req, res) => {
  const file = resolveFile(req.url === "/" ? "/index.html" : req.url);
  if (!file) {
    res.writeHead(404, { "Content-Type": "text/html; charset=utf-8" });
    return res.end("<h1>404</h1>");
  }
  res.writeHead(200, {
    "Content-Type": MIME[path.extname(file).toLowerCase()] || "application/octet-stream",
    "Cache-Control": "no-store",   // 確認中に古いJSON/JSを掴まないように
  });
  fs.createReadStream(file).pipe(res);
}).listen(PORT, () => {
  console.log(`SHAD JAPAN ローカル確認用: http://localhost:${PORT}/`);
});
