#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — sitemap.xml / robots.txt を生成する
=============================================================================
    python3 tools/build_sitemap.py

・site/ 直下・product/・news/ の公開HTMLを https://www.shad-japan.com/ のクリーンURLで列挙
・除外：thanks / form-error / 404 / top-simple（社内確認用）/ news/article（ライブ表示の器、noindex）/ install-guide
・lastmod はファイルの更新日時
=============================================================================
"""
import os, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
BASE = "https://www.shad-japan.com"
EXCLUDE = {"thanks", "form-error", "404", "top-simple", "news/article", "install-guide"}
PRIORITY = {"": "1.0", "products": "0.9", "fitment": "0.9", "lock-guide": "0.7", "news": "0.7",
            "top-cases": "0.9", "side-cases": "0.9", "bags": "0.9", "waterproof": "0.8", "helmet-storage": "0.8", "guide/top-case-size": "0.8"}

def url_of(path):
    rel = os.path.relpath(path, SITE)[:-5].replace(os.sep, "/")
    if rel == "index":
        return ""
    if rel.endswith("/index"):
        rel = rel[:-6]
    return rel

def main():
    files = sorted(glob.glob(os.path.join(SITE, "*.html")) + glob.glob(os.path.join(SITE, "product", "*.html")) + glob.glob(os.path.join(SITE, "news", "*.html")) + glob.glob(os.path.join(SITE, "guide", "*.html")))
    items = []
    for f in files:
        u = url_of(f)
        if u in EXCLUDE:
            continue
        mtime = datetime.date.fromtimestamp(os.path.getmtime(f)).isoformat()
        pr = PRIORITY.get(u, "0.8" if u.startswith("product/") else "0.6" if u.startswith("news/") else "0.7")
        items.append((BASE + "/" + u, mtime, pr))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lm, pr in items:
        xml.append("  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (loc.rstrip("/") + ("/" if loc.endswith(BASE + "/") else ""), lm, pr))
    xml.append("</urlset>")
    open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(xml) + "\n")
    robots = ["User-agent: *", "Allow: /", "Disallow: /thanks", "Disallow: /form-error", "Disallow: /top-simple", "Disallow: /news/article",
              "Disallow: /contact.php", "", "Sitemap: %s/sitemap.xml" % BASE, ""]
    open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8").write("\n".join(robots))
    print("sitemap.xml: %d URLs / robots.txt を出力" % len(items))

if __name__ == "__main__":
    main()
