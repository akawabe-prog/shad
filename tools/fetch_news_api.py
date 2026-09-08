#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD — NEWS をカスタムジャパンのCMSから取得
=============================================================================
SHAD関連記事の原本はCJのCMS（WordPress）です。ここで取得してJSONに落とし、
`tools/build_news.py` が一覧（/news）とTOPのNEWS枠に流し込みます。

    出力: site/data/news/news_api.json

■ 使い方
    python3 tools/fetch_news_api.py            # 取得してJSONを更新
    python3 tools/fetch_news_api.py --dry-run  # 取得して内容を表示するだけ

■ 取得元
    GET https://cms.customjapan.net/wp-json/custom/v1/posts
        ?categories=480      … SHADカテゴリ。**この指定でSHAD記事だけが返る**
        &publish_codes=n&per_page=24&_embed
    ページングあり（X-WP-TotalPages）。全ページを順に取得します。

■ 記事の種別
    CJ側のタグ（#メディア / #特集 / #出展 / #ニュース）をサイトのカテゴリに対応させます。
    タグが無い記事（取付・使用方法など）は Guide 扱い。

■ 注意
    記事本文（content）もJSONに保存しますが、既定では一覧に使うのはタイトル・
    抜粋・アイキャッチだけで、クリック先はCJの元記事です。本文をサイト内に
    載せる場合は元記事と内容が重複するため、canonical の扱いを決めてください。
=============================================================================
"""

import html as html_mod
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "site", "data", "news", "news_api.json")

API = ("https://cms.customjapan.net/wp-json/custom/v1/posts"
       "?categories=480&publish_codes=n&per_page=24&_embed"
       "&_fields=id,date,title.rendered,excerpt.rendered,content.rendered,link,_embedded")

# CJのタグ → サイト側のカテゴリ（絞り込みチップに出る名前）
# 上にあるものを優先（1記事に「#メディア」と「#出展」が両方付くことがあるため）
TAG_TO_CATEGORY = [
    ("#出展", "Event"),
    ("#ニュース", "News"),
    ("#特集", "Feature"),
    ("#メディア", "Media"),
]
DEFAULT_CATEGORY = "Guide"      # 取付・使用方法など、種別タグが無い記事


def curl(url, dump_headers=None):
    args = ["curl", "-sS", "--max-time", "60", url]
    if dump_headers:
        args += ["-D", dump_headers]
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("curl failed: " + (res.stderr or "").strip())
    return res.stdout


def total_pages(header_file):
    try:
        for line in open(header_file, encoding="utf-8", errors="replace"):
            if line.lower().startswith("x-wp-totalpages:"):
                return int(line.split(":", 1)[1].strip())
    except OSError:
        pass
    return 1


def fetch_all():
    import tempfile
    head = os.path.join(tempfile.gettempdir(), "shad-news.head")
    out = curl(API + "&page=1", dump_headers=head)
    posts = json.loads(out)
    pages = total_pages(head)
    for p in range(2, pages + 1):
        posts += json.loads(curl(API + "&page=%d" % p))
    return posts, pages


def strip_html(s):
    """タグを外し、実体参照（&hellip; など）を文字に戻す。抜粋末尾の […] も落とす。"""
    s = re.sub(r"<[^>]+>", "", s or "")
    s = html_mod.unescape(s)
    s = re.sub(r"\s*\[\s*…\s*\]\s*$", "…", s)
    return re.sub(r"\s+", " ", s).strip()


def tags_of(post):
    return [t.get("name", "") for t in ((post.get("_embedded") or {}).get("tags") or [])
            if isinstance(t, dict)]


def image_of(post):
    """アイキャッチ。一覧カードは4:3なので medium_large（768px）で十分。"""
    fm = (post.get("_embedded") or {}).get("featured_media")
    if isinstance(fm, list):
        fm = fm[0] if fm and isinstance(fm[0], dict) else None
    if not isinstance(fm, dict):
        return ""
    sizes = (fm.get("media_details") or {}).get("sizes") or {}
    for key in ("medium_large", "large", "full"):
        if sizes.get(key, {}).get("source_url"):
            return sizes[key]["source_url"]
    return fm.get("source_url") or ""


def main():
    dry = "--dry-run" in sys.argv
    posts, pages = fetch_all()

    items = []
    for p in posts:
        tags = tags_of(p)
        kind = next((cat for tag, cat in TAG_TO_CATEGORY if tag in tags), DEFAULT_CATEGORY)
        items.append({
            "id": p["id"],
            "date": (p.get("date") or "")[:10],
            "category": kind,
            "title": strip_html(p.get("title", {}).get("rendered")),
            "lead": strip_html(p.get("excerpt", {}).get("rendered"))[:160],
            "image": image_of(p),
            "url": p.get("link") or "",
            "tags": [t for t in tags if not t.startswith("#")],
            "content": p.get("content", {}).get("rendered") or "",
        })
    items.sort(key=lambda x: x["date"], reverse=True)

    jst = timezone(timedelta(hours=9))
    payload = {
        "source": API,
        "fetchedAt": datetime.now(jst).replace(microsecond=0).isoformat(),
        "count": len(items),
        "items": items,
    }

    import collections
    print("取得: %d件（%dページ）" % (len(items), pages))
    for k, n in collections.Counter(x["category"] for x in items).most_common():
        print("  %-8s %d件" % (k, n))
    print("期間: %s 〜 %s" % (items[-1]["date"], items[0]["date"]))
    noimg = [x for x in items if not x["image"]]
    if noimg:
        print("⚠ アイキャッチ画像なし: %d件" % len(noimg))
    if dry:
        print("\n--dry-run のためファイルは書き出していません")
        for x in items[:5]:
            print("  %s [%s] %s" % (x["date"], x["category"], x["title"][:52]))
        return

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("\n出力: site/data/news/news_api.json")


if __name__ == "__main__":
    main()
