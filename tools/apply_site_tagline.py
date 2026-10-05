#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 全ページの meta description に「SHAD日本公式サイト。」を付ける（SEO の決まり文句）
=============================================================================
    python3 tools/apply_site_tagline.py        # site/ 配下の全 HTML（何度実行しても同じ結果）

・description / og:description / twitter:description の末尾に「SHAD日本公式サイト。」を追加
・「日本総代理店カスタムジャパンの公式サイト」のような旧文言は置き換える（2026-10-05 指示：総代理店名は入れない）
・すでに「日本公式」を含むページは変更しない
・ページを生成・更新したあと（build_landing.py / apply_seo_meta.py / build_news.py 等）の最後に実行する
=============================================================================
"""
import os, re, glob, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
TAG = "SHAD日本公式サイト。"
OLD = ["SHAD日本総代理店カスタムジャパンの公式サイト。", "SHAD日本総代理店公式。", "SHAD公式。"]

def fix(desc):
    d = html.unescape(desc)
    for o in OLD:
        d = d.replace(o, TAG)
    if "日本公式" not in d:
        d = d.rstrip()
        if d and not d.endswith(("。", ".", "！", "!")):
            d += "。"
        d = (d + TAG) if d else TAG
    return html.escape(d, quote=True)

def main():
    files = glob.glob(os.path.join(SITE, "*.html")) + glob.glob(os.path.join(SITE, "*", "*.html"))
    n = 0
    for f in sorted(files):
        s = open(f, encoding="utf-8").read()
        new = s
        for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
            new = re.sub(r'(<meta %s content=")([^"]*)(")' % re.escape(attr), lambda m: m.group(1) + fix(m.group(2)) + m.group(3), new, count=1)
        if new != s:
            open(f, "w", encoding="utf-8").write(new); n += 1
    print("description に「%s」を反映：%d ページ更新" % (TAG, n))

if __name__ == "__main__":
    main()
