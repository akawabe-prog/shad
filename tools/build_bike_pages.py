#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SHAD JAPAN — 車種別の適合ページ（/bike/<slug>）を適合データから生成する（SEO：車種名＋トップケース 等の検索の受け皿）
=============================================================================
    python3 tools/build_bike_pages.py     # 適合データ更新（tools/fitment/build.py → postprocess.py）のあとに実行

生成するもの
  site/bike/index.html          メーカー別の車種一覧（/bike）
  site/bike/<slug>.html         車種ページ：付くトップケース・サイドケース・サイドバッグと必要なキット
・装着できるケースの決め方は site/js/fitment.js と同じ（キット仕様欄の対応モデル → 対応ベースプレート配下）
・slug はメーカー＋車種名の英数字。英数字が少ない車種名は maker|model のハッシュを付けて固定（データを作り直しても URL が変わらない）
・ヘッダー／フッター／共通部品は tools/build_landing.py を流用
=============================================================================
"""
import os, re, json, html, hashlib, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_landing as L

ROOT = L.ROOT; SITE = L.SITE; BASE = L.BASE
RD = json.load(open(os.path.join(SITE, "data/fitment/reverse_data.json"), encoding="utf-8"))
OUT = os.path.join(SITE, "bike")
MAKER_SLUG = {"ホンダ": "honda", "ヤマハ": "yamaha", "スズキ": "suzuki", "カワサキ": "kawasaki", "ハーレー": "harley-davidson"}
MAKER_ORDER = ["ホンダ", "ヤマハ", "スズキ", "カワサキ"]
esc = L.esc

def mslug(m):
    return MAKER_SLUG.get(m) or re.sub(r"[^a-z0-9]+", "-", m.lower()).strip("-") or hashlib.sha1(m.encode()).hexdigest()[:6]

def slug_of(b):
    model = b["model"]
    ms = mslug(b["maker"])
    a = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")
    for pre in {ms, ms.split("-")[0], "hd"}:            # 車種名の先頭にメーカー名があれば重ねない（aprilia-aprilia-… を防ぐ）
        if a.startswith(pre + "-"): a = a[len(pre) + 1:]
    h = hashlib.sha1((b["maker"] + "|" + model).encode("utf-8")).hexdigest()[:6]
    if len(re.sub(r"[^a-z]", "", a)) < 2 or re.search(r"[^\x00-\x7f]", model):
        a = (a + "-" if a else "") + h       # 日本語を含む車種名（フォルツァ、アドレス125 など）はハッシュで固定
    return mslug(b["maker"]) + "-" + a

PLATES = RD["plates"]
TOP_BY_CODE = {}
for pl in PLATES.values():
    for tc in pl["topcases"]:
        TOP_BY_CODE.setdefault(tc["code"], tc)
SIDE = {**RD.get("sidecases", {}), **RD.get("sidebags", {})}

def top_for(bike):
    kits = {}
    for t in bike.get("top", []):
        k = kits.setdefault(t["url"], {"name": t["name"], "url": t["url"], "plates": [], "models": t.get("models"), "noPlate": t.get("noPlate")})
        k["plates"].append(t.get("plate"))
    codes = []
    for k in kits.values():
        plates = [p for p in k["plates"] if p in PLATES]
        if k["models"] and "*" in k["models"]:
            src = [tc["code"] for p in plates for tc in PLATES[p]["topcases"]] if plates else list(TOP_BY_CODE)
        elif k["models"]:
            src = [c for c in k["models"] if c in TOP_BY_CODE]
        else:
            src = [tc["code"] for p in plates for tc in PLATES[p]["topcases"]]
        for c in src:
            if c not in codes: codes.append(c)
    return list(kits.values()), codes

def side_for(bike):
    out = []
    for s in bike.get("side", []):
        codes = []
        for c in s.get("cases", []):
            for it in SIDE.get(c, []):
                if it["code"] not in codes: codes.append(it["code"])
        if codes: out.append((s, codes))
    return out

SYS = {"3P": "3Pシステム フィッティングキット", "4P": "4Pシステム フィッティングキット", "サイドバッグホルダー": "サイドバッグホルダーキット", "サイドバッグホルダーSR": "SRバッグフィッティングキット"}

def bycap(codes):
    cards = L.C
    def cap(c):
        e = L.P.get(c)
        return L.cap_max(c) if e else 0
    return sorted(codes, key=lambda c: (-cap(c), c))

def kit_line(name, url, label):
    cj = re.search(r"/i/([A-Za-z0-9]+)", url or "")
    return ('<div class="kit-block"><div class="kit-line">取付には %s が必要です：</div><div class="kit-line"><span class="kit-name">%s</span>'
            '<a href="%s" target="_blank" rel="noopener" class="kit-btn">商品を見る ›</a>%s</div></div>') % (
            esc(label), esc(name), esc(url), ('<span class="text-[12.5px] text-neutral-500">品番 %s</span>' % cj.group(1)) if cj else "")

def build_one(b, slug):
    maker, model = b["maker"], b["model"]
    tkits, tcodes = top_for(b)
    sides = side_for(b)
    bags = [c for _, cs in sides for c in cs if c in RD.get("sidebags", {})]
    cases = [c for _, cs in sides for c in cs if c in RD.get("sidecases", {})]
    n_top, n_side, n_bag = len(tcodes), len(set(cases)), len(set(bags))
    path = "/bike/" + slug
    name = "%s %s" % (maker, model)
    kinds = "・".join(x for x, n in (("トップケース", n_top), ("サイドケース", n_side), ("サイドバッグ", n_bag)) if n)
    body = L.hero("Fitment", "%s に付く SHAD の%s" % (esc(model), esc(kinds or "ケース")),
                  "%s %s に取り付けできる SHAD のケース・バッグと、必要な車種専用フィッティングキットです。キットを車体に付ければ、対応するケースはワンタッチで着脱できます。" % (esc(maker), esc(model)),
                  "/img/fitting/topcase_banner.webp")
    if tkits:
        blk = "".join(kit_line(k["name"], k["url"], "トップマスター（トップケース用）") for k in tkits)
        if tcodes:
            blk += '<div class="mt-6">%s</div>' % L.grid(bycap(tcodes))
        body += L.section("Top Case", "トップケース（%d モデル）" % n_top, blk + L.p("ベースプレートが別売のモデルと付属のモデルがあります。詳しくは各商品ページでご確認ください。"), "py-12 md:py-16")
    for s, codes in sides:
        label = SYS.get(s.get("system"), (s.get("system") or "") + "システム フィッティングキット")
        kind = "サイドバッグ" if all(c in RD.get("sidebags", {}) for c in codes) else ("サイドケース・サイドバッグ" if any(c in RD.get("sidebags", {}) for c in codes) else "サイドケース")
        body += L.section("Side", "%s（%s）" % (kind, esc(label.split(" ")[0])), kit_line(s["name"], s["url"], label) + '<div class="mt-6">%s</div>' % L.grid(bycap(codes)), "pb-12 md:pb-16")
    body += L.section("Next", "購入の前に",
        L.ul(["ケース本体とフィッティングキットは別売です（ベースプレートが付属するトップケースもあります）。",
              "年式・型式・純正オプション（キャリア・パニアステー等）の有無で適合が変わることがあります。キットの商品ページで適合をご確認ください。",
              "タンクバッグはクリックシステムの車種別アタッチメントで取り付けます。<a href='/tank-bags' class='text-shad'>タンクバッグの選び方</a>"])
        + L.links([("適合検索でこの車種を見る", "/fitment?bike=" + html.escape(maker + "|" + model, quote=True)), ("ほかの車種を探す", "/bike"), ("フィッティングキットとは", "/fitting-kits"), ("取扱店・SHAD BASE", "/store-locator")]), "pb-16 md:pb-24")
    title = "%s（%s）のトップケース・サイドケース｜SHAD 適合フィッティングキット — SHAD JAPAN" % (model, maker)
    desc = "%s %s に適合する SHAD の%sと、必要な車種専用フィッティングキット（品番）を掲載。%s" % (maker, model,
            "・".join(x for x in (("トップケース%dモデル" % n_top) if n_top else "", ("サイドケース%dモデル" % n_side) if n_side else "", ("サイドバッグ%dモデル" % n_bag) if n_bag else "") if x), "SHAD日本公式サイト。")
    items = bycap(tcodes) + bycap(list(dict.fromkeys(cases + bags)))
    L.page(path, title, desc, body, [L.crumbs_ld(path, name, ("車種から探す", "/bike")), L.itemlist_ld("%s に付く SHAD 製品" % model, items)], "/img/fitting/topcase_banner.webp")
    return {"maker": maker, "model": model, "slug": slug, "n": n_top + n_side + n_bag}

def main():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    seen, made = {}, []
    for b in RD["bikes"]:
        if not (b.get("top") or b.get("side")): continue
        s = slug_of(b)
        if s in seen:
            s = s + "-" + hashlib.sha1((b["maker"] + "|" + b["model"]).encode()).hexdigest()[:4]
        seen[s] = 1
        made.append(build_one(b, s))
    # 一覧（メーカー別）
    by = {}
    for m in made: by.setdefault(m["maker"], []).append(m)
    makers = sorted(by, key=lambda x: (MAKER_ORDER.index(x) if x in MAKER_ORDER else 9, x))
    nav = '<div class="flex flex-wrap gap-2 mt-6">%s</div>' % "".join('<a href="#mk-%s" class="tag hover:border-shad hover:text-shad transition">%s<span class="text-neutral-400 ml-1">%d</span></a>' % (mslug(m), esc(m), len(by[m])) for m in makers)
    lists = "".join('<div id="mk-%s" class="mt-10 scroll-mt-[96px]"><h3 class="font-bold text-[20px]">%s</h3><ul class="grid sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-1.5 mt-3">%s</ul></div>' % (
        mslug(m), esc(m), "".join('<li><a href="/bike/%s" class="text-[14.5px] hover:text-shad">%s</a></li>' % (x["slug"], esc(x["model"])) for x in sorted(by[m], key=lambda x: x["model"]))) for m in makers)
    body = L.hero("Fitment", "車種から探す｜SHAD 適合車種一覧", "SHAD のトップケース・サイドケース・サイドバッグが付く車種を、メーカー別に一覧にしました。車種を選ぶと、付くケースと必要なフィッティングキットが分かります。", "/img/fitting/topcase_banner.webp")
    body += L.section("Makers", "メーカーから選ぶ（%d 車種）" % len(made), nav + lists + L.links([("適合検索（キーワードで探す）", "/fitment")]), "py-12 md:py-16")
    L.page("/bike/index", "車種別 適合一覧｜SHAD のトップケース・サイドケースが付くバイク — SHAD JAPAN",
           "SHAD のトップケース・サイドケース・サイドバッグが付く %d 車種をメーカー別に一覧。ホンダ・ヤマハ・スズキ・カワサキ・BMW ほか。車種ごとに対応ケースと必要なフィッティングキットを掲載。SHAD日本公式サイト。" % len(made),
           body, [L.crumbs_ld("/bike", "車種から探す")], "/img/fitting/topcase_banner.webp")
    # canonical を /bike に（index.html で生成したため）
    f = os.path.join(OUT, "index.html"); s = open(f, encoding="utf-8").read().replace(BASE + "/bike/index", BASE + "/bike")
    open(f, "w", encoding="utf-8").write(s)
    print("車種ページ %d ＋ 一覧 /bike を生成" % len(made))

if __name__ == "__main__":
    main()
