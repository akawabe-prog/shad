"""
フィッティングキットの一覧ページ生成（写真なし・表形式）

dist/reverse_data.json（generate_reverse_data_from_itemlist.py の出力）を読み込み、
以下3種類の静的HTMLページを dist/ に出力する。

  fitting_baseplates.html : ベースプレート単位
      1行=1ベースプレート。対応トップケースと、そのプレートを使うトップキットが
      対応する車種一覧を表示する。

  fitting_topcases.html   : トップケース（ボックス）のフィッティングキット単位
      1行=1トップマスターフィッティングキット。対応車種・対応ベースプレートを表示する。

  fitting_sidekits.html   : 3P/4Pキットの車種一覧
      1行=1車種。3P/4Pそれぞれのキットの有無を表示する。
      3P/4Pは1キットが1車種に紐付くため、キット単位ではなく車種一覧に対して
      キットの有無を記載する形式にする。

廃盤（CJ廃番=1）の商品・キットは reverse_data.json 生成側（is_catalog_visible /
is_kit_visible）で除外済みのため、本スクリプト側では廃盤の扱いを考慮しない。
"""

import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(ROOT, "dist")

PAGE_STYLE = """
:root { --accent: #d81f26; --dark: #111; --border: #e2e2e2; }
* { box-sizing: border-box; }
body {
  font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
  max-width: 1160px; margin: 0 auto; padding: 24px 20px 60px; color: #1a1a1a; background: #fff;
}
.brand-bar {
  background: linear-gradient(115deg, var(--dark) 88%, var(--accent) 88.3%, var(--accent) 92%, var(--dark) 92.3%, var(--dark) 94%, var(--accent) 94.3%);
  color: #fff; padding: 20px 28px; margin-bottom: 20px; display: flex; align-items: baseline; gap: 16px; flex-wrap: wrap;
}
.brand-logo { font-weight: 900; font-size: 1.6rem; letter-spacing: 4px; font-style: italic; }
.brand-logo .dot { color: var(--accent); }
.brand-title { font-size: 0.9rem; color: #bbb; letter-spacing: 2px; font-weight: bold; }
.page-sub { font-size: 0.85rem; color: #666; margin: 0 0 18px; }
#filterInput {
  width: 100%; padding: 10px 12px; font-size: 0.9rem; border: 1px solid var(--border);
  margin-bottom: 14px;
}
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
thead th {
  text-align: left; background: var(--dark); color: #fff; padding: 8px 10px;
  position: sticky; top: 0; font-weight: bold; letter-spacing: 0.5px;
}
tbody td { padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
tbody tr:nth-child(even) { background: #fafafa; }
tbody tr.no-match { display: none; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.count-badge { font-size: 0.72rem; color: #fff; background: var(--dark); padding: 1px 7px; margin-left: 6px; }
.tag-no { color: #ddd; }
.col-narrow { white-space: nowrap; }
.kit-badge {
  display: inline-block; min-width: 4.2em; text-align: center; font-weight: bold; font-size: 0.85rem;
  color: #fff; background: #2e7d32; padding: 7px 14px; text-decoration: none; line-height: 1.3;
  letter-spacing: 0.5px; box-shadow: 0 2px 0 rgba(0,0,0,0.15); cursor: pointer;
  transition: transform 0.08s, box-shadow 0.08s, background 0.08s;
  margin: 2px 4px 2px 0;
}
.kit-badge:hover {
  background: var(--dark); text-decoration: none;
  box-shadow: 0 3px 0 rgba(0,0,0,0.25); transform: translateY(-1px);
}
.kit-badge:active { box-shadow: 0 1px 0 rgba(0,0,0,0.2); transform: translateY(1px); }
.col-kit { text-align: center; }
"""

FILTER_SCRIPT = """
document.getElementById('filterInput').addEventListener('input', e => {
  const q = e.target.value.trim().toLowerCase();
  document.querySelectorAll('tbody tr').forEach(tr => {
    tr.classList.toggle('no-match', q !== '' && !tr.textContent.toLowerCase().includes(q));
  });
});
"""


def load_reverse_data():
    with open(os.path.join(DIST_DIR, "reverse_data.json"), encoding="utf-8") as f:
        return json.load(f)


def page_shell(title, subtitle, thead_html, tbody_rows_html, row_count):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>{PAGE_STYLE}</style>
</head>
<body>

<div class="brand-bar">
  <span class="brand-logo">SHAD<span class="dot">.</span></span>
  <span class="brand-title">{html.escape(title)}</span>
</div>
<p class="page-sub">{html.escape(subtitle)}<span class="count-badge">全{row_count}件</span></p>

<input type="text" id="filterInput" placeholder="キーワードで絞り込み（車種名・コードなど）">

<table>
  <thead><tr>{thead_html}</tr></thead>
  <tbody>
{tbody_rows_html}
  </tbody>
</table>

<script>{FILTER_SCRIPT}</script>
</body>
</html>
"""


def link(name, url):
    return f'<a href="{html.escape(url)}" target="_blank">{html.escape(name)}</a>'


# ホンダ/ヤマハ/スズキ/カワサキを優先し、それ以外はメーカー名のアルファベット順
PRIORITY_MAKERS = ["ホンダ", "ヤマハ", "スズキ", "カワサキ"]


def maker_sort_key(maker):
    try:
        return (PRIORITY_MAKERS.index(maker), "")
    except ValueError:
        return (len(PRIORITY_MAKERS), maker)


def bike_sort_key(maker, model):
    return maker_sort_key(maker) + (model,)


def bike_label(maker, model):
    """メーカー名+車種名を表示用に結合。車種名側にすでにメーカー名が含まれる場合
    （海外車種は item_name に "BMW C600(15-24)..." のようにメーカー名が入っている）
    は重複させない。
    """
    if model.upper().startswith(maker.upper() + " "):
        return model
    return f"{maker} {model}"


def build_baseplate_page(data):
    plates = data["plates"]
    bikes = data["bikes"]

    plate_bikes = {code: [] for code in plates}
    for b in bikes:
        codes_for_bike = {t["plate"] for t in b["top"] if t["plate"]}
        label = bike_label(b["maker"], b["model"])
        for code in codes_for_bike:
            plate_bikes.setdefault(code, []).append(label)
    for v in plate_bikes.values():
        v.sort()

    thead = ("<th>コード</th><th>プレート名</th><th>対応トップケース</th>"
             "<th class=\"col-narrow\">対応車種数</th><th>対応車種一覧</th>")

    rows = []
    for code, plate in sorted(plates.items()):
        topcase_names = "、".join(tc["name"] for tc in plate["topcases"]) or "-"
        bike_list = plate_bikes.get(code, [])
        bike_names = "、".join(bike_list) or "-"
        rows.append(
            f"<tr><td class=\"col-narrow\">{link(code, plate['url'])}</td>"
            f"<td>{html.escape(plate['name'])}</td>"
            f"<td>{html.escape(topcase_names)}</td>"
            f"<td class=\"col-narrow\">{len(bike_list)}</td>"
            f"<td>{html.escape(bike_names)}</td></tr>"
        )

    return page_shell(
        "ベースプレート一覧",
        "ベースプレート単位で、対応トップケースと対応車種を表示",
        thead, "\n".join(rows), len(plates),
    )


def build_topcase_kit_page(data):
    bikes = data["bikes"]

    kits = {}  # url -> {plates: set, bikes: set of (maker, model)}
    for b in bikes:
        for t in b["top"]:
            kit = kits.setdefault(t["url"], {"plates": set(), "bikes": set()})
            kit["bikes"].add((b["maker"], b["model"]))
            if t["plate"]:
                kit["plates"].add(t["plate"])

    thead = "<th>対応車種</th><th class=\"col-narrow\">対応ベースプレート</th>"

    def kit_sort_key(item):
        url, kit = item
        return min(bike_sort_key(m, mo) for m, mo in kit["bikes"])

    rows = []
    for url, kit in sorted(kits.items(), key=kit_sort_key):
        bike_list = sorted(kit["bikes"], key=lambda mm: bike_sort_key(*mm))
        bike_links = "、".join(link(bike_label(m, mo), url) for m, mo in bike_list)
        plate_codes = "、".join(sorted(kit["plates"])) or "-"
        rows.append(
            f"<tr><td>{bike_links}</td>"
            f"<td class=\"col-narrow\">{html.escape(plate_codes)}</td></tr>"
        )

    return page_shell(
        "トップケース フィッティングキット一覧",
        "トップマスターフィッティングキット単位で、対応車種と対応ベースプレートを表示",
        thead, "\n".join(rows), len(kits),
    )


def side_kit_cell(label, entries):
    if not entries:
        return '<span class="tag-no">-</span>'
    parts = [
        f'<a class="kit-badge" href="{html.escape(s["url"])}" target="_blank" '
        f'title="{html.escape(s["name"])}">{label}</a>'
        for s in entries
    ]
    return " ".join(parts)


def build_side_kit_page(data):
    bikes = sorted(data["bikes"], key=lambda b: (b["maker"], b["model"]))

    thead = ("<th>メーカー</th><th>車種</th>"
             "<th class=\"col-narrow col-kit\">3P</th><th class=\"col-narrow col-kit\">4P</th>")

    rows = []
    for b in bikes:
        p3 = [s for s in b["side"] if s["system"] == "3P"]
        p4 = [s for s in b["side"] if s["system"] == "4P"]
        if not p3 and not p4:
            continue  # 3P/4Pともにキットがない車種は表示しない
        rows.append(
            f"<tr><td>{html.escape(b['maker'])}</td><td>{html.escape(b['model'])}</td>"
            f"<td class=\"col-narrow col-kit\">{side_kit_cell('3P', p3)}</td>"
            f"<td class=\"col-narrow col-kit\">{side_kit_cell('4P', p4)}</td></tr>"
        )

    return page_shell(
        "3P/4Pシステムキット 車種一覧",
        "車種ごとに3P/4Pシステムフィッティングキットの有無を表示（バッジをクリックでキット商品ページへ）",
        thead, "\n".join(rows), len(rows),
    )


def build_sidebag_holder_page(data):
    bikes = data["bikes"]

    kits = {}  # url -> {plates(=cases): set, bikes: set of (maker, model)}
    for b in bikes:
        for s in b["side"]:
            if s["system"] not in ("サイドバッグホルダー", "サイドバッグホルダーSR"):
                continue
            kit = kits.setdefault(s["url"], {"cases": set(), "bikes": set()})
            kit["bikes"].add((b["maker"], b["model"]))
            kit["cases"].update(s["cases"])

    thead = "<th>対応車種</th><th class=\"col-narrow\">対応サイドバッグ</th>"

    def kit_sort_key(item):
        url, kit = item
        return min(bike_sort_key(m, mo) for m, mo in kit["bikes"])

    rows = []
    for url, kit in sorted(kits.items(), key=kit_sort_key):
        bike_list = sorted(kit["bikes"], key=lambda mm: bike_sort_key(*mm))
        bike_links = "、".join(link(bike_label(m, mo), url) for m, mo in bike_list)
        case_codes = "、".join(sorted(kit["cases"])) or "-"
        rows.append(
            f"<tr><td>{bike_links}</td>"
            f"<td class=\"col-narrow\">{html.escape(case_codes)}</td></tr>"
        )

    return page_shell(
        "サイドバッグホルダーキット一覧",
        "サイドバッグホルダーキット単位で、対応車種と対応サイドバッグ（E48/SW42/SL58等）を表示",
        thead, "\n".join(rows), len(kits),
    )


def build_clicksystem_page(data):
    kits = data.get("clicksystem_kits", [])

    thead = ("<th>キット名</th><th class=\"col-narrow\">対応メーカー</th>"
             "<th>適合車種（参考・要適合確認）</th><th class=\"col-narrow\">対応タンクバッグ</th>")

    rows = []
    for kit in kits:
        model_text = "、".join(kit["models"]) or "-"
        case_codes = "、".join(kit["cases"]) or "-"
        rows.append(
            f"<tr><td>{link(kit['name'], kit['url'])}</td>"
            f"<td class=\"col-narrow\">{html.escape(kit['maker'])}</td>"
            f"<td>{html.escape(model_text)}</td>"
            f"<td class=\"col-narrow\">{html.escape(case_codes)}</td></tr>"
        )

    return page_shell(
        "クリックシステム フィッティングキット一覧",
        "1キットが複数メーカー・複数車種にまたがるため車種別の自動判定はしていません。"
        "適合車種は参考情報としてキットの記載をそのまま表示しています。実際の適合は必ずキット商品ページでご確認ください。",
        thead, "\n".join(rows), len(kits),
    )


def main():
    data = load_reverse_data()

    pages = [
        ("fitting_baseplates.html", build_baseplate_page(data)),
        ("fitting_topcases.html", build_topcase_kit_page(data)),
        ("fitting_sidekits.html", build_side_kit_page(data)),
        ("fitting_sidebagholders.html", build_sidebag_holder_page(data)),
        ("fitting_clicksystem.html", build_clicksystem_page(data)),
    ]
    for filename, content in pages:
        out_path = os.path.join(DIST_DIR, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ dist/{filename}")


if __name__ == "__main__":
    main()
