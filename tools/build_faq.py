#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD — 商品ページにFAQを書き出す
=============================================================================
`site/data/faq/faq.json`（tools/fetch_faq.py が取得）から、各商品ページの
FAQセクションを生成します。マーカー間を毎回置き換えるので、何度実行しても
同じ結果になります。

    <!-- FAQ:START 生成 tools/build_faq.py --> … <!-- FAQ:END -->

■ 使い方
    python3 tools/fetch_faq.py && python3 tools/build_faq.py

■ どのFAQをどの商品ページに出すか
    1) この商品について … FAQの relItems / slug がその型番を指しているもの
    2) <カテゴリ>について … FAQの分類（classS。例「トップケース」）が
                            その商品の種類名に含まれるもの
    3) SHADについて     … 分類が「全般」のもの（全商品ページ共通）
    ※1つのFAQが複数グループに該当する場合は、上のグループを優先して1回だけ出す

■ 出力
    - details/summary のアコーディオン（/faq と同じ .faq-item / .faq-q / .faq-a）
    - 構造化データ（FAQPage）… 検索結果でQ&Aが出る可能性があるため併記
=============================================================================
"""

import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
FAQ_JSON = os.path.join(SITE, "data", "faq", "faq.json")
CARDS = os.path.join(SITE, "data", "catalog", "cards.json")
PRODUCT_DIR = os.path.join(SITE, "product")

START = "<!-- FAQ:START 生成 tools/build_faq.py -->"
END = "<!-- FAQ:END -->"
# 「Same Series」の帯の直前に入れる（無ければフッターの直前）
ANCHOR_RE = re.compile(r'\n<section class="bg-mist py-12 mt-8">')
FOOTER_RE = re.compile(r"\n<footer")


def esc(s):
    return html.escape(s or "", quote=False)


def strip_tags(s):
    s = re.sub(r"<br\s*/?>", " ", s or "")
    return re.sub(r"<[^>]+>", "", s).strip()


def group_for(code, jp, items):
    """商品ページに出すFAQを (見出し, [FAQ...]) の並びで返す"""
    used = set()
    groups = []

    own = [x for x in items if code in x.get("codes", [])]
    if own:
        groups.append(("この商品について", own))
        used.update(x["id"] for x in own)

    # 分類（トップケース 等）が商品の種類名に含まれるもの
    cats = {}
    for x in items:
        c = x.get("category") or ""
        if x["id"] in used or not c or c == "全般":
            continue
        if c and c in (jp or ""):
            cats.setdefault(c, []).append(x)
    for c, rows in cats.items():
        groups.append((c + "について", rows))
        used.update(x["id"] for x in rows)

    common = [x for x in items if x.get("category") == "全般" and x["id"] not in used]
    if common:
        groups.append(("SHADについて", common))
    return groups


def render(code, jp, groups):
    # data-faq-* は js/faq.js が使う（CORS許可後にAPIから最新へ差し替えるため）
    out = [START,
           '<section class="max-w-site mx-auto px-7 py-12" id="faq"'
           ' data-faq-code="%s" data-faq-jp="%s">' % (esc(code), esc(jp)),
           '  <div class="max-w-[860px]">',
           '    <p class="font-disp font-semibold text-[13px] tracking-[.28em]'
           ' uppercase text-shad">FAQ</p>',
           '    <h2 class="text-[26px] font-bold tracking-[.02em] mt-2">よくあるご質問</h2>',
           '    <div data-faq-list>']
    first = True
    for title, rows in groups:
        out.append('    <h3 class="faq-group">%s</h3>' % esc(title))
        for x in rows:
            op = " open" if first else ""
            first = False
            out.append('    <details class="faq-item"%s>' % op)
            out.append('      <summary class="faq-q"><span class="qmark">Q</span>%s'
                       '<i class="ti ti-chevron-down chev"></i></summary>' % esc(x["question"]))
            out.append('      <div class="faq-a">%s</div>' % x["answer"])
            out.append('    </details>')
    out.append('    </div>')
    out.append('    <p class="mt-8 text-[13.5px]">'
               '<a href="/faq" class="text-shad underline underline-offset-4">'
               'すべてのご質問を見る</a>　'
               '<a href="/contact" class="text-shad underline underline-offset-4">'
               'お問い合わせ</a></p>')
    out.append('  </div>')

    # 構造化データ（検索結果でのQ&A表示用）
    qa = [{"@type": "Question", "name": strip_tags(x["question"]),
           "acceptedAnswer": {"@type": "Answer", "text": strip_tags(x["answer"])}}
          for _, rows in groups for x in rows]
    out.append('  <script type="application/ld+json">%s</script>'
               % json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                             "mainEntity": qa}, ensure_ascii=False))
    out.append('</section>')
    out.append('<script src="/js/faq.js"></script>')
    out.append(END)
    return "\n".join(out)


def replace_block(page, block):
    """マーカーがあれば差し替え、無ければ Same Series の直前（無ければフッター直前）に入れる"""
    if START in page and END in page:
        head, rest = page.split(START, 1)
        _, tail = rest.split(END, 1)
        return head + block + tail, "更新"
    m = ANCHOR_RE.search(page) or FOOTER_RE.search(page)
    if not m:
        return page, "挿入位置が見つからない"
    at = m.start()
    return page[:at] + "\n" + block + page[at:], "追加"


def main():
    data = json.load(open(FAQ_JSON, encoding="utf-8"))
    items = data["items"]
    cards = json.load(open(CARDS, encoding="utf-8"))

    only = [a.upper() for a in sys.argv[1:] if not a.startswith("-")]
    changed, skipped = [], []
    for path in sorted(glob.glob(os.path.join(PRODUCT_DIR, "*.html"))):
        slug = os.path.basename(path)[:-5]
        code = slug.upper()
        if only and code not in only:
            continue
        card = cards.get(code) or {}
        groups = group_for(code, card.get("jp", ""), items)
        if not groups:
            skipped.append(code)
            continue
        page = open(path, encoding="utf-8").read()
        new, how = replace_block(page, render(code, card.get("jp", ""), groups))
        if how not in ("更新", "追加"):
            skipped.append("%s(%s)" % (code, how))
            continue
        if new != page:
            open(path, "w", encoding="utf-8").write(new)
        n = sum(len(r) for _, r in groups)
        changed.append((code, how, n, [t for t, _ in groups]))

    print("FAQを書き出した商品ページ: %d件" % len(changed))
    for code, how, n, titles in changed:
        print("  %-9s %s %2d件  %s" % (code, how, n, " / ".join(titles)))
    if skipped:
        print("対象FAQなしでスキップ: %s" % ", ".join(skipped))


if __name__ == "__main__":
    main()
