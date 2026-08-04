#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 一覧用カード画像の生成（大きさを統一）
=============================================================================
商品一覧・同シリーズのカード画像は、元画像ごとに被写体の写る大きさが
バラバラだった（占有率47〜88%）ため、白背景をトリムして
一定の割合（FILL）で正方形キャンバスに配置し直す。

■ 使い方
    python3 tools/build_card_images.py
        → site/img/products/cards/<code>.webp を生成
        （products.html の PRODUCTS[].img を元画像として参照。
          CDN画像の商品は取得してから処理する）

■ 仕様
    ・出力：900x900 / WebP q82 / 白背景
    ・被写体は長辺が FILL（既定84%）になるよう拡縮して中央配置
    ・背景が白でない写真（ライフスタイル等）は正方形センタークロップ
=============================================================================
"""
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
LIST_HTML = os.path.join(SITE, "products.html")
OUT_DIR = os.path.join(SITE, "img", "products", "cards")
TMP_DIR = os.path.join("/tmp", "shad-card-src")
SIZE = 900
FILL = 0.84
WHITE_TOLERANCE = 14


def fetch(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 1000:
        return dst
    r = subprocess.run(["curl", "-sSL", "--max-time", "40", "-o", dst, url],
                       capture_output=True)
    return dst if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 1000 else None


def _bbox(im, tolerance):
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg).convert("L").point(
        lambda x: 255 if x > tolerance else 0)
    return diff.getbbox()


def normalize(src, out):
    im = Image.open(src).convert("RGB")
    area = im.size[0] * im.size[1]
    # 背景がわずかにグレーの画像もあるため、閾値を上げながら被写体を探す
    bb, on_white = None, False
    for tol in (WHITE_TOLERANCE, 34, 54):
        bb = _bbox(im, tol)
        if bb is not None and (bb[2] - bb[0]) * (bb[3] - bb[1]) < area * 0.97:
            on_white = True
            break

    if on_white:
        obj = im.crop(bb)
        k = (SIZE * FILL) / max(obj.size)
        obj = obj.resize((max(1, round(obj.width * k)), max(1, round(obj.height * k))),
                         Image.LANCZOS)
        canvas = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
        canvas.paste(obj, ((SIZE - obj.width) // 2, (SIZE - obj.height) // 2))
        mode = "トリム＋統一"
    else:
        s = min(im.size)
        left, top = (im.width - s) // 2, (im.height - s) // 2
        canvas = im.crop((left, top, left + s, top + s)).resize((SIZE, SIZE), Image.LANCZOS)
        mode = "センタークロップ"

    png = "/tmp/shad-card.png"
    canvas.save(png)
    subprocess.run(["cwebp", "-quiet", "-q", "82", png, "-o", out], check=True)
    return mode


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)
    text = open(LIST_HTML, encoding="utf-8").read()
    products = json.loads(re.search(r"var PRODUCTS=(\[.*?\]);", text, re.S).group(1))
    only = [c.upper() for c in sys.argv[1:] if not c.startswith("-")]

    made, skipped = [], []
    for p in products:
        code = p["code"]
        if only and code.upper() not in only:
            continue
        out = os.path.join(OUT_DIR, code.lower() + ".webp")
        img = p.get("img") or ""
        # すでに統一版を指している場合は元画像を探し直す
        if "/cards/" in img:
            cand = os.path.join(SITE, "img", "products", code.lower() + ".webp")
            src = cand if os.path.exists(cand) else None
            if src is None:
                src = fetch("https://img.customjapan.net/items/%s_1.jpg" % (p.get("cjCode") or ""),
                            os.path.join(TMP_DIR, code + ".jpg")) if p.get("cjCode") else None
            if src is None:
                skipped.append((code, "元画像が見つからない（生成済みを再利用）"))
                continue
        elif img.startswith("http"):
            src = fetch(img, os.path.join(TMP_DIR, code + ".jpg"))
            if src is None:
                skipped.append((code, "CDN取得失敗"))
                continue
        else:
            src = os.path.join(SITE, img.lstrip("/"))
            if not os.path.exists(src):
                skipped.append((code, "元画像なし"))
                continue
        made.append((code, normalize(src, out)))

    print("生成: %d 件 → site/img/products/cards/" % len(made))
    for c, m in made:
        print("   %-8s %s" % (c, m))
    if skipped:
        print("スキップ: %d 件" % len(skipped))
        for c, why in skipped:
            print("   %-8s %s" % (c, why))


if __name__ == "__main__":
    main()
