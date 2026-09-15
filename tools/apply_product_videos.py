#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品ページの看板（サムネイル一覧）の直下に、本国のテクニカル動画（YouTube）を埋め込む。

    python3 tools/apply_product_videos.py            # 全商品ページ
    python3 tools/apply_product_videos.py TR46 SH51  # 指定のみ

・対応表：tools/product_videos.json（品番 → [{id, title}]）
・<!-- YT:START --> … <!-- YT:END --> のマーカーで差し替えるので、何度でも実行できる
・build_product_max.py も生成後にこの関数を呼ぶので、MAXページの再生成で消えない
・埋め込みは youtube-nocookie.com、loading="lazy"。動画のダウンロードは行わない
"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(ROOT, "tools", "product_videos.json")
MARK_S, MARK_E = "<!-- YT:START 生成 tools/apply_product_videos.py -->", "<!-- YT:END -->"

def block(code, vids):
    if not vids: return ""
    frames = "".join(
        '<div class="pd-yt-frame"><iframe src="https://www.youtube-nocookie.com/embed/%s?rel=0" title="%s" loading="lazy" '
        'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>%s</div>'
        % (v["id"], v["title"].replace('"', "&quot;"), ('<p class="pd-yt-cap">%s</p>' % v["title"]) if len(vids) > 1 else "")
        for v in vids)
    return ('%s\n    <div class="pd-yt"><p class="pd-yt-lb"><i class="ti ti-brand-youtube"></i>Technical Video'
            '<span>本国SHADのテクニカル動画（英語）</span></p><div class="pd-yt-grid%s">%s</div></div>\n    %s'
            % (MARK_S, " is-2" if len(vids) > 1 else "", frames, MARK_E))

def apply_html(s, code, vids):
    s = re.sub(re.escape(MARK_S) + r".*?" + re.escape(MARK_E) + r"\n?\s*", "", s, flags=re.S)   # 既存ブロックを除去
    b = block(code, vids)
    if not b: return s
    m = re.search(r'<div class="flex flex-wrap gap-2\.5 mt-3">.*?</div>', s, re.S)   # サムネイル行（ネストなし）
    if not m: return s
    return s[:m.end()] + "\n    " + b + s[m.end():]

def apply_to_file(path, code):
    data = json.load(open(DATA, encoding="utf-8"))["videos"]
    s = open(path, encoding="utf-8").read()
    t = apply_html(s, code, data.get(code.upper(), []))
    if t != s:
        open(path, "w", encoding="utf-8").write(t)
    return bool(data.get(code.upper()))

def main():
    codes = [c.upper() for c in sys.argv[1:]]
    files = sorted(f for f in os.listdir(os.path.join(SITE, "product")) if f.endswith(".html"))
    n = 0
    for f in files:
        code = f[:-5].upper()
        if codes and code not in codes: continue
        if apply_to_file(os.path.join(SITE, "product", f), code): n += 1; print("  埋め込み:", code)
    print("テクニカル動画を埋め込んだ商品ページ: %d件" % n)

if __name__ == "__main__":
    main()
