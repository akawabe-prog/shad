#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD — シンプル版トップページを生成
=============================================================================
`site/index.html` を原本に、セクションを取捨選択した簡易版トップを作ります。
デザイン・パーツは既存のまま（同じCSS／同じマークアップ）を使い回すので、
本体のトップを直せばこのページも作り直すだけで揃います。

    出力: site/top-simple.html  →  /top-simple

■ 使い方
    python3 tools/build_top_simple.py

■ 本体トップとの違い
    削除  SHAD Technology / 鍵がなくても蓋の開け閉めが可能 /
          なぜ、世界のメーカーはSHADを純正に選ぶのか。/
          買ってからも、安心して使えるように。/ 映像で知る、SHAD。
    変更  カテゴリから探す … フィッティングキットを外し、残り4つを大きく配置
    追加  SHADカタログ（PDF）
    移動  NEWS を「カテゴリから探す」の直後に
=============================================================================
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
SRC = os.path.join(SITE, "index.html")
OUT = os.path.join(SITE, "top-simple.html")

# 原本のセクション見出しコメント（<!-- ===== ① HERO ===== --> 等）で切り分ける
MARK = re.compile(r"<!-- =====\s*.*?\s*=====\s*-->")   # 「）===== -->」のように空白が無い行もある

# 残すセクション（原本のコメント内の識別語 → 出力順）
KEEP_ORDER = ["NAV", "HERO", "NEW ARRIVALS", "FINDER", "PRODUCTS",
              "NEWS", "REELS", "FOOTER"]


def split_sections(html):
    """(見出しコメント, 本文) の並びに分解する。先頭は head 〜 body 開始まで。"""
    marks = list(MARK.finditer(html))
    head = html[:marks[0].start()]
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(html)
        out.append((m.group(0), html[m.start():end]))
    return head, out


def pick(sections, keyword):
    for label, body in sections:
        if keyword in label:
            return body
    raise SystemExit("原本に見つかりません: " + keyword)


def simplify_products(block):
    """カテゴリから探す：フィッティングキットのタイルを外し、4枚を大きく見せる"""
    # フィッティングキットのタイル（<a> 1つ分）を削除
    tiles = re.findall(r'      <a href="/products\?cat=[A-Z]+".*?\n      </a>\n',
                       block, re.S)
    fitting = [t for t in tiles if "フィッティングキット" in t]
    if len(fitting) != 1:
        raise SystemExit("フィッティングキットのタイルを特定できません（%d件）" % len(fitting))
    block = block.replace(fitting[0], "")

    # 5列前提のグリッドを4列に。1枚あたりが大きくなり、余白も揃う
    before = 'class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 md:gap-5"'
    after = 'class="grid grid-cols-2 lg:grid-cols-4 gap-5 md:gap-7"'
    if before not in block:
        raise SystemExit("カテゴリのグリッド指定が原本と一致しません")
    block = block.replace(before, after)

    # 画像の余白を詰めて（p-4 → p-6）、キャプションも一回り大きく
    block = block.replace(
        'flex items-center justify-center p-4 transition',
        'flex items-center justify-center p-6 md:p-8 transition')
    block = block.replace(
        'block text-center font-bold text-[14.5px] mt-3',
        'block text-center font-bold text-[16px] mt-3.5')
    return block


CATALOG = """<!-- ===== ⑪ CATALOG（PDF） ===== -->
<section id="catalog" class="bg-mist py-[76px]">
  <div class="max-w-site mx-auto px-7">
    <div class="mb-7" data-reveal>
      <h2 class="text-[30px] font-bold tracking-[.02em]">SHADカタログ</h2>
      <p class="text-neutral-500 text-[14.5px] mt-2.5 max-w-[640px]">製品ラインアップと仕様をまとめたカタログです。PDFでご覧いただけます。</p>
    </div>
    <div class="grid sm:grid-cols-2 gap-5 md:gap-7 max-w-[760px] items-start">
%s    </div>
  </div>
</section>
"""

CATALOG_CARD = """      <a href="/docs/catalog/%(file)s" target="_blank" rel="noopener" class="group block" data-reveal>
        <span class="block rounded-[16px] overflow-hidden bg-black border border-black/10 transition group-hover:-translate-y-1 group-hover:shadow-[0_18px_40px_rgba(0,0,0,.14)]">
          <img src="/img/catalog/catalog_%(year)s.webp" alt="SHADカタログ%(year)s 表紙" loading="lazy" width="%(w)s" height="%(h)s" class="block w-full h-auto transition duration-300 group-hover:scale-[1.03]">
        </span>
        <span class="flex items-center justify-between gap-3 mt-3.5">
          <span class="font-bold text-[16px] group-hover:text-shad transition">SHADカタログ%(year)s</span>
          <span class="inline-flex items-center gap-1.5 text-[13px] text-neutral-500 group-hover:text-shad group-hover:gap-2.5 transition-all whitespace-nowrap">PDF %(size)s<i class="ti ti-download"></i></span>
        </span>
      </a>
"""

CATALOGS = [
    {"year": "2025", "file": "shad_catalog_2025.pdf"},
    {"year": "2024", "file": "shad_catalog_2024.pdf"},
]


def webp_size(path):
    """WebPのヘッダから幅・高さを読む（表紙は年によって判型が違うため）"""
    b = open(path, "rb").read(40)
    if b[12:16] == b"VP8X":
        w = int.from_bytes(b[24:27], "little") + 1
        h = int.from_bytes(b[27:30], "little") + 1
    elif b[12:16] == b"VP8L":
        n = int.from_bytes(b[21:25], "little")
        w = (n & 0x3FFF) + 1
        h = ((n >> 14) & 0x3FFF) + 1
    else:                                   # VP8（ロッシー）
        w = int.from_bytes(b[26:28], "little") & 0x3FFF
        h = int.from_bytes(b[28:30], "little") & 0x3FFF
    return w, h


def catalog_section():
    cards = ""
    for c in CATALOGS:
        pdf = os.path.join(SITE, "docs", "catalog", c["file"])
        mb = os.path.getsize(pdf) / 1024 / 1024
        w, h = webp_size(os.path.join(SITE, "img", "catalog",
                                      "catalog_%s.webp" % c["year"]))
        cards += CATALOG_CARD % dict(c, size="%.1fMB" % mb, w=w, h=h)
    return CATALOG % cards


def fix_head(head):
    """タイトルとURL周りだけ差し替える（本体トップと重複して検索に出ないように）"""
    head = head.replace(
        "<title>SHAD JAPAN｜バイク用トップケース・サイドケース — 本物にこだわるライダーへ</title>",
        "<title>SHAD JAPAN｜バイク用トップケース・サイドケース</title>")
    head = head.replace('<meta property="og:url" content="https://www.shad-japan.com/">',
                        '<meta property="og:url" content="https://www.shad-japan.com/top-simple">')
    # 本体トップと内容が重なるため、確認中は検索エンジンに載せない
    head = head.replace('<link rel="canonical" href="https://www.shad-japan.com/">',
                        '<link rel="canonical" href="https://www.shad-japan.com/top-simple">\n'
                        '<meta name="robots" content="noindex">')
    if 'name="robots"' not in head:
        head = head.replace("</head>", '<meta name="robots" content="noindex">\n</head>')
    return head


def main():
    html = open(SRC, encoding="utf-8").read()
    head, sections = split_sections(html)

    parts = [fix_head(head)]
    for key in KEEP_ORDER:
        block = pick(sections, key)
        if key == "PRODUCTS":
            block = simplify_products(block)
        if key == "FOOTER":
            parts.append(catalog_section())   # カタログはフッターの直前
        parts.append(block)

    out = "".join(parts)
    open(OUT, "w", encoding="utf-8").write(out)

    dropped = [l for l, _ in sections if not any(k in l for k in KEEP_ORDER)]
    print("出力: site/top-simple.html  →  /top-simple")
    print("残したセクション: %s" % " / ".join(KEEP_ORDER))
    print("外したセクション:")
    for d in dropped:
        print("  " + d.replace("<!-- ===== ", "").replace(" ===== -->", ""))
    print("追加: CATALOG（%s）" % "・".join(c["year"] for c in CATALOGS))


if __name__ == "__main__":
    main()
