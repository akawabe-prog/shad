#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — GitHub Pages 確認用ビルド
=============================================================================
本番（GCS）はドメイン直下に配置されるため、サイト内の参照はすべて
ルート相対パス（/css/... /product/tr55）で実装しています。

一方 GitHub Pages のプロジェクトページは
    https://<user>.github.io/<repo>/
のようにサブパス配下で配信されるため、ルート相対パスがドメイン直下を
指してしまい、CSS・JS・画像がすべて 404 になります。

このスクリプトは確認用に、サイト内のルート相対パスへ /<repo> を付けた
コピーを作ります。生成物を gh-pages ブランチに push して閲覧します。
（本番用の site/ は一切変更しません）

■ 使い方
    python3 tools/build_ghpages.py            # dist/ghpages/ を作る
    python3 tools/build_ghpages.py --push     # 作って gh-pages に push

■ 注意
    確認専用です。Drive/GCSへ納品するのは site/（= dist/shad/）の方です。
=============================================================================
"""

import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "dist", "ghpages")
PREFIX = "/shad"                      # GitHub Pages のリポジトリ名部分
TEXT_EXT = (".html", ".css", ".js", ".json")

# 置換対象：サイト内のルート相対パスだけ（// や http は対象外）
TARGET_DIRS = ("css", "js", "img", "media", "data", "docs", "product", "news")
PAGE_SLUGS = None                     # 実行時に site 直下の .html から作る


def page_slugs():
    """site直下の .html と、index.html を持つディレクトリ（/news など）"""
    slugs = [os.path.splitext(f)[0] for f in os.listdir(SITE) if f.endswith(".html")]
    slugs += [d for d in os.listdir(SITE)
              if os.path.isfile(os.path.join(SITE, d, "index.html"))]
    return sorted(set(slugs))


def rewrite(text, prefix=None):
    prefix = prefix or PREFIX
    # ① ディレクトリ配下（/css/... /img/... /product/xxx）
    text = re.sub(
        r'(["\'(])/(' + "|".join(TARGET_DIRS) + r')/',
        lambda m: m.group(1) + prefix + "/" + m.group(2) + "/",
        text,
    )
    # ② ルート直下のページ（/about /products /#finder /）
    for slug in PAGE_SLUGS:
        text = re.sub(r'(["\'])/' + re.escape(slug) + r'(?=["\'?#])',
                      lambda m: m.group(1) + prefix + "/" + slug, text)
    text = re.sub(r'(["\'])/(?=["\'])', lambda m: m.group(1) + prefix + "/", text)
    text = re.sub(r'(["\'])/#', lambda m: m.group(1) + prefix + "/#", text)
    # ③ 二重付与を戻す
    text = text.replace(prefix + prefix, prefix)
    return text


def main():
    global PAGE_SLUGS
    PAGE_SLUGS = page_slugs()

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SITE, OUT)

    changed = prepare(OUT, PREFIX)

    # カスタムジャパン版（dist/cj）があれば /cj/ 配下にも同梱して確認できるようにする
    cj_src = os.path.join(ROOT, "dist", "cj")
    cj_note = ""
    if os.path.isdir(cj_src):
        cj_out = os.path.join(OUT, "cj")
        shutil.copytree(cj_src, cj_out)
        changed += prepare(cj_out, PREFIX + "/cj")
        cj_note = "（カスタムジャパン版も /cj/ に同梱）"

    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print("dist/ghpages を作成：パス書き換え %d ファイル %s" % (changed, cj_note))

    if "--push" in sys.argv:
        push(OUT)


def prepare(root, prefix):
    """パスの書き換え＋拡張子なしURL用の index.html を用意する"""
    changed = 0
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(dirpath, name)
            if not name.endswith(TEXT_EXT):
                continue
            with open(path, encoding="utf-8", errors="ignore") as fh:
                src = fh.read()
            new = rewrite(src, prefix)
            if new != src:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
                changed += 1

    # 拡張子なしURLでも開けるように <slug>/index.html を用意
    for dirpath, _dirs, files in list(os.walk(root)):
        for name in files:
            if not name.endswith(".html") or name == "index.html":
                continue
            slug = os.path.splitext(name)[0]
            d = os.path.join(dirpath, slug)
            os.makedirs(d, exist_ok=True)
            shutil.copy2(os.path.join(dirpath, name), os.path.join(d, "index.html"))
    return changed


def push(OUT):
    if True:
        subprocess.run(["git", "init", "-q", "-b", "gh-pages"], cwd=OUT, check=True)
        subprocess.run(["git", "add", "-A"], cwd=OUT, check=True)
        subprocess.run(["git", "-c", "user.name=shad-preview",
                        "-c", "user.email=noreply@example.com",
                        "commit", "-q", "-m", "GitHub Pages 確認用ビルド"],
                       cwd=OUT, check=True)
        url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "remote", "add", "origin", url], cwd=OUT, check=True)
        subprocess.run(["git", "push", "-q", "-f", "origin", "gh-pages"],
                       cwd=OUT, check=True)
        print("gh-pages に push しました")
        print("  ブランドサイト     → https://akawabe-prog.github.io/shad/")
        print("  カスタムジャパン版 → https://akawabe-prog.github.io/shad/cj/")


if __name__ == "__main__":
    main()
