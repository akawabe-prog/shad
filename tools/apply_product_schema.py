#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 商品ページの構造化データ（Product／パンくず）をマスターから作り直す（SEO：検索結果のリッチ表示）
=============================================================================
    python3 tools/apply_product_schema.py      # 商品マスター更新後・商品ページ再生成後に実行（何度実行しても同じ結果）

・Product：名前・品番（mpn）・JAN（gtin13）・画像・説明（meta description と同じ文）・カテゴリ・
  Offer（定価・JPY・在庫状況・新品）。カラー違いで価格が違う商品は AggregateOffer（最安〜最高）
  在庫状況は商品マスターの「商品ステータスコード」：SE/SF=在庫あり、SO=入荷待ち（BackOrder）、それ以外=在庫あり扱い
・パンくず：ホーム ＞ カテゴリページ（/top-cases 等）＞ 商品。見える位置の「← 製品一覧」の横にもカテゴリへのリンクを置く
=============================================================================
"""
import os, re, json, csv, glob, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site"); BASE = "https://www.shad-japan.com"
P = json.load(open(os.path.join(SITE, "data/catalog/products.json"), encoding="utf-8"))
C = json.load(open(os.path.join(SITE, "data/catalog/cards.json"), encoding="utf-8"))
ROWS = {r["品番"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data-source/ItemList_SHAD.csv"), encoding="cp932", newline=""))}
AV = {"SE": "InStock", "SF": "LimitedAvailability", "SO": "BackOrder"}

def category(code):
    jp = (C.get(code) or {}).get("jp", "") + " " + P[code]["variants"][0].get("category", "")
    for k, path, name in (("トップケース", "/top-cases", "トップケース"), ("サイドケース", "/side-cases", "サイドケース"),
                          ("サイドバッグ", "/side-bags", "サイドバッグ"), ("タンクバッグ", "/tank-bags", "タンクバッグ"),
                          ("ロック", "/locks", "SHAD LOCKS"), ("ツーリングバッグ", "/bags", "バッグ"), ("バッグ", "/bags", "バッグ")):
        if k in jp: return path, name
    return "/products", "製品一覧"

def availability(e):
    st = [ROWS.get(v["cjCode"], {}).get("商品ステータスコード", "") for v in e["variants"]]
    for s in ("SE", "SF", "SO"):
        if s in st: return AV[s]
    return "InStock"

def main():
    n = 0
    for f in sorted(glob.glob(os.path.join(SITE, "product", "*.html"))):
        code = os.path.basename(f)[:-5].upper()
        if code not in P: continue
        e = P[code]; v0 = e["variants"][0]
        s = open(f, encoding="utf-8").read()
        url = BASE + "/product/" + code.lower()
        desc = html.unescape((re.search(r'<meta name="description" content="([^"]*)"', s) or [None, ""])[1])
        title = html.unescape(re.search(r"<title>(.*?)</title>", s, re.S).group(1)).split("｜")[0]
        img = re.search(r'<meta property="og:image" content="([^"]+)"', s)
        prices = sorted({v["msrpTaxIn"] for v in e["variants"] if v.get("msrpTaxIn")})
        av = "https://schema.org/" + availability(e)
        if len(prices) > 1:
            offer = {"@type": "AggregateOffer", "priceCurrency": "JPY", "lowPrice": prices[0], "highPrice": prices[-1], "offerCount": len(e["variants"]), "availability": av}
        else:
            offer = {"@type": "Offer", "priceCurrency": "JPY", "price": prices[0] if prices else None, "availability": av, "itemCondition": "https://schema.org/NewCondition", "url": url}
        offer["seller"] = {"@type": "Organization", "name": "株式会社カスタムジャパン"}
        cpath, cname = category(code)
        prod = {"@context": "https://schema.org", "@type": "Product", "name": "%s %s" % (code if code != "SH40CG" else "SH40 CARGO", (C.get(code) or {}).get("jp", "")),
                "sku": code, "mpn": v0.get("makerCode") or None, "gtin13": v0.get("jan") or None, "brand": {"@type": "Brand", "name": "SHAD"},
                "category": cname, "image": img.group(1) if img else None, "description": desc, "url": url, "offers": offer}
        prod = {k: v for k, v in prod.items() if v not in (None, "")}
        crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ホーム", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": cname, "item": BASE + cpath},
            {"@type": "ListItem", "position": 3, "name": title, "item": url}]}
        new = s
        new = re.sub(r'<script type="application/ld\+json">\s*\{\s*"@context":\s*"https://schema.org",\s*"@type":\s*"Product".*?</script>',
                     lambda m: '<script type="application/ld+json">%s</script>' % json.dumps(prod, ensure_ascii=False), new, count=1, flags=re.S)
        new = re.sub(r'<script type="application/ld\+json">\{"@context":\s*"https://schema.org",\s*"@type":\s*"BreadcrumbList".*?</script>',
                     lambda m: '<script type="application/ld+json">%s</script>' % json.dumps(crumbs, ensure_ascii=False, separators=(",", ":")), new, count=1, flags=re.S)
        # 見える位置のパンくず：「← 製品一覧」の後ろにカテゴリリンク
        new = re.sub(r'(<a href="/products" class="inline-flex items-center gap-2 text-\[13px\] text-neutral-500 hover:text-shad transition"><i class="ti ti-arrow-left"></i>製品一覧</a>)(?:<span class="pd-crumb">.*?</span>)?',
                     lambda m: m.group(1) + ('<span class="pd-crumb text-[13px] text-neutral-400"> ／ <a href="%s" class="text-neutral-500 hover:text-shad transition">%s</a></span>' % (cpath, cname) if cpath != "/products" else ""), new, count=1, flags=re.S)
        if new != s:
            open(f, "w", encoding="utf-8").write(new); n += 1
    print("商品ページの構造化データ・パンくずを更新：%d ページ" % n)

if __name__ == "__main__":
    main()
