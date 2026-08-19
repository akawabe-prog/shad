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
    削除  なぜ、世界のメーカーはSHADを純正に選ぶのか。（ブランドの核ブロック）
    変更  カテゴリから探す … フィッティングキットを外し、残り4つを大きく配置
          HEROの「SHADを知る」… 本体は #why、シンプル版は /about へ
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


# 本国サイト（www.shad-japan.com）下部のカタログ枠を踏襲：
#   45°ストライプの帯の中に、左＝カタログの見開き画像／右＝赤いPDFボタンを縦に並べる
CATALOG = """<!-- ===== ⑪ CATALOG（PDF） ===== -->
<section id="catalog" class="bg-white py-[84px] md:py-[104px]">
  <div class="max-w-site mx-auto px-7">
    <div class="ptn-stripe45 py-4" data-reveal>
      <div class="max-w-[820px] mx-auto grid sm:grid-cols-2 gap-6 md:gap-8 items-center px-4">
        <a href="/docs/catalog/%(latest_file)s" target="_blank" rel="noopener" class="group block">
          <img src="/img/catalog/catalog_%(latest_year)s_spread.webp" alt="SHADカタログ%(latest_year)s" loading="lazy" width="%(latest_w)s" height="%(latest_h)s" class="block w-full h-auto shadow-[0_10px_30px_rgba(0,0,0,.12)] transition duration-300 group-hover:-translate-y-1 group-hover:shadow-[0_18px_40px_rgba(0,0,0,.18)]">
        </a>
        <div class="flex flex-col gap-3.5">
%(btns)s        </div>
      </div>
    </div>
  </div>
</section>
"""

CATALOG_BTN = """          <a href="/docs/catalog/%(file)s" target="_blank" rel="noopener" class="catalog-btn">SHADカタログ%(year)s PDF版<span class="sz">%(size)s</span></a>
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
    btns = ""
    for c in CATALOGS:
        mb = os.path.getsize(os.path.join(SITE, "docs", "catalog", c["file"])) / 1024 / 1024
        btns += CATALOG_BTN % dict(c, size="PDF %.1fMB" % mb)
    latest = CATALOGS[0]                       # 画像は最新年度の見開きを使う
    w, h = webp_size(os.path.join(SITE, "img", "catalog",
                                  "catalog_%s_spread.webp" % latest["year"]))
    return CATALOG % dict(latest_year=latest["year"], latest_file=latest["file"],
                          latest_w=w, latest_h=h, btns=btns)


def fix_hero(block):
    """HEROの「SHADを知る」は本体トップの #why 用。シンプル版には無いので /about へ"""
    return block.replace('href="#why"', 'href="/about"')


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
        if key == "HERO":
            block = fix_hero(block)
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
