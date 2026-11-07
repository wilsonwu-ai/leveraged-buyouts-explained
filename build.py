"""Build the GitHub Pages site in docs/ from the markdown copy, the figure partials and the model.

    python3 -I model/lbo_model.py    # illustrative LBO -> model/lbo_model.json
    python3 -I model/build_data.py   # lbo_model.json + sourced facts -> model/site_data.json
    python3 -I build.py              # site_data -> docs/assets/data.js; copy + figures + template -> docs/index.html
    python3 -I build.py --draft      # same, but a missing figure or section becomes a visible placeholder

Copy: content/00-intro.md ... 05-glossary.md, joined in order. Each section is a level-2 heading "## Title {#id}" and lands
in the template's <!-- COPY:id --> placeholder; text before the first section is the intro. The sources section is
generated from model/sources.json, and every external link in the copy must appear there.
Figures: a line "<!-- FIG:fig-name -->" in the copy (or the template) is replaced by templates/figures/fig-name.html.
Numbers inside figures: any leaf element with data-k="path" data-f="format" gets its text from site_data at build time
(same formats as docs/assets/js/core.js). "<!-- TABLE:name -->" inside a figure becomes a fallback data table.
"""
import json
import math
import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
FIGS = TEMPLATES / "figures"
CONTENT = ROOT / "content"
DOCS = ROOT / "docs"
ORDER = ["00-intro.md", "01-situation.md", "02-task-action.md", "03-result.md", "04-conclusion.md", "05-glossary.md"]
DRAFT = "--draft" in sys.argv
OWN_LINKS = ("https://wilsonwu-ai.github.io/", "https://github.com/wilsonwu-ai/")

SECTION_RE = re.compile(r"^## (.+?)\s*\{#([a-z0-9-]+)\}\s*$", re.M)
PLACEHOLDER_RE = re.compile(r"<!-- COPY:([a-z0-9-]+) -->")
FIG_RE = re.compile(r"(?:<p>\s*)?<!-- FIG:([a-z0-9-]+) -->(?:\s*</p>)?")
TABLE_RE = re.compile(r"<!-- TABLE:([a-z0-9-]+) -->")
HOOK_RE = re.compile(r"<(\w+)(\s[^<>]*?\bdata-k=\"[^\"]+\"[^<>]*)>([^<]*)</\1>")
LINK_RE = re.compile(r"\]\((https?://[^)\s]+)\)")
BANNED_CHARS = {"\u2014": "em dash", "\u2013": "en dash"}
DISCLAIMER = ("Educational only. Not investment, legal or tax advice. The worked example is an illustrative company, "
              "not a real deal. Sources as listed, as of 7 November 2026.")

DATA = json.loads((ROOT / "model" / "site_data.json").read_text())
SOURCES = json.loads((ROOT / "model" / "sources.json").read_text())


# ---------------------------------------------------------------- formats (must match core.js)
def rnd(a: float, d: int) -> float:
    m = 10 ** d
    return math.floor(a * m + 0.5) / m


def fmt(v, f: str) -> str:
    if v is None:
        return ""
    if f == "raw" or isinstance(v, bool) or not isinstance(v, (int, float)):
        return str(v)
    neg, a = v < 0, abs(float(v))
    s = {"d0": lambda: f"${rnd(a, 0):,.0f}", "K0": lambda: f"${rnd(a / 1000, 0):,.0f}K",
         "M1": lambda: f"${rnd(a / 1e6, 1):,.1f}M", "M2": lambda: f"${rnd(a / 1e6, 2):,.2f}M",
         "x1": lambda: f"{rnd(a, 1):,.1f}x", "x2": lambda: f"{rnd(a, 2):,.2f}x",
         "p0": lambda: f"{rnd(a, 0):,.0f}%", "p1": lambda: f"{rnd(a, 1):,.1f}%",
         "n0": lambda: f"{rnd(a, 0):,.0f}", "n1": lambda: f"{rnd(a, 1):,.1f}"}.get(f)
    if s is None:
        sys.exit(f"build: unknown data-f format '{f}'")
    return ("-" if neg else "") + s()


def get(path: str):
    cur = DATA
    for p in re.findall(r"[^.\[\]]+|\[[^\]]+\]", path):
        if cur is None:
            return None
        if p.startswith("["):
            inner = p[1:-1]
            if "=" in inner:
                k, v = inner.split("=", 1)
                cur = next((o for o in cur if isinstance(o, dict) and str(o.get(k)) == v), None)
            else:
                cur = cur[int(inner)] if isinstance(cur, list) and int(inner) < len(cur) else None
        else:
            cur = cur.get(p) if isinstance(cur, dict) else None
    return cur


def need(path: str):
    v = get(path)
    if v is None:
        sys.exit(f"build: model/site_data.json has no '{path}'")
    return v


def fill_hooks(html_text: str, where: str) -> str:
    def rep(m):
        tag, attrs = m.group(1), m.group(2)
        k = re.search(r'\bdata-k="([^"]+)"', attrs).group(1)
        fm = re.search(r'\bdata-f="([^"]+)"', attrs)
        v = get(k)
        if v is None:
            sys.exit(f"build: {where}: data-k=\"{k}\" not found in model/site_data.json")
        return f"<{tag}{attrs}>{fmt(v, fm.group(1) if fm else 'raw')}</{tag}>"
    return HOOK_RE.sub(rep, html_text)


# ---------------------------------------------------------------- fallback tables
def table(head: list, rows: list, caption: str = "") -> str:
    th = "".join(f"<th scope=\"col\">{h}</th>" for h in head)
    body = "".join("<tr>" + "".join((f"<th scope=\"row\">{c}</th>" if i == 0 else f"<td>{c}</td>") for i, c in enumerate(r))
                   + "</tr>" for r in rows)
    cap = f"<caption class=\"sr-only\">{caption}</caption>" if caption else ""
    return f"<div class=\"table-wrap\"><table>{cap}<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>"


def yes(b) -> str:
    return "Yes" if b else "No"


def t_stack():
    labels = need("stack_labels")
    rows = []
    for k in ("a", "b", "c", "d"):
        s = need(f"stack.{k}")
        rows.append([labels[k], fmt(s["price"], "M2"), fmt(s["multiple"], "x2"), fmt(s["buyer_cash"], "K0"),
                     fmt(s["standby_seller_note"], "K0"), fmt(s["investor_equity"], "K0"), fmt(s["sba_loan"], "M2"),
                     fmt(s["annual_sba_payment"], "K0"), fmt(s["dscr"], "x2"), yes(s["passes"])])
    return table(["Case", "Price", "Price / EBITDA", "Buyer cash", "Seller note (standby)", "Investors", "SBA loan",
                  "Yearly loan payment", "DSCR", "Passes 1.25x"], rows,
                 "Illustrative capital stacks for a company with $1.0M of EBITDA")


def t_sens():
    rows = [[fmt(r["multiple"], "x2"), fmt(r["price"], "M2"), fmt(r["sba_loan"], "M2"), fmt(r["annual_sba_payment"], "K0"),
             fmt(r["dscr"], "x2"), yes(r["passes"])] for r in need("sens")]
    return table(["Price / EBITDA", "Price", "SBA loan", "Yearly loan payment", "DSCR", "Passes 1.25x"], rows,
                 "What the bank test says at each price, illustrative")


def t_scenarios():
    rows = []
    for k in ("base", "flat", "downside", "break"):
        s = need(f"scenarios.{k}")
        b = s["bridge"]
        rows.append([s["label"], fmt(s["growth_pct"], "p0"), fmt(s["year1_shock_pct"], "p0"), fmt(s["exit_multiple"], "x1"),
                     fmt(s["exit_ebitda"], "M2"), fmt(b["sale_price"], "M2"),
                     fmt(b["sba_still_owed"] + b["seller_note_with_interest"], "M2"), fmt(b["owner_proceeds"], "M2"),
                     fmt(s["moic_proceeds_only"], "x1"), fmt(s["irr_proceeds_only_pct"], "p0") if b["owner_proceeds"] > 0 else "n/a",
                     fmt(s["min_dscr"], "x2")])
    return table(["Scenario", "Yearly growth", "Year 1 change", "Exit multiple", "Year 6 EBITDA", "Sale price",
                  "Loans still owed", "Owner's proceeds", "Proceeds / cash in", "IRR", "Lowest DSCR"], rows,
                 "Illustrative scenarios, sale in year 6, proceeds only")


def t_bridge():
    rows = []
    for k in ("base", "flat", "downside", "break"):
        s = need(f"scenarios.{k}")
        b = s["bridge"]
        rows.append([s["label"], fmt(b["price_paid"], "M2"), fmt(b["earnings_growth"], "M2"), fmt(b["multiple_change"], "M2"),
                     fmt(b["sale_price"], "M2"), fmt(-b["sba_still_owed"], "M2"), fmt(-b["seller_note_with_interest"], "M2"),
                     fmt(b["owner_proceeds"], "M2")])
    return table(["Scenario", "Price paid", "From earnings growth", "From the multiple", "Sale price", "SBA loan left",
                  "Seller note with interest", "Owner's proceeds"], rows, "Where the sale price goes, illustrative")


def t_qoe():
    rows = [[i["label"], fmt(i["amount"], "K0") if i["kind"] == "step" else fmt(i["amount"], "M2")] for i in need("qoe.items")]
    return table(["Item", "Amount"], rows, "Illustrative quality of earnings bridge")


def t_day1():
    d = need("day1")
    rows = [[f"Week {w['week']}", fmt(w["cash_peg"], "K0"), fmt(w["cash_no_ar"], "K0")] for w in d["weeks"]]
    return table(["Week", d["case_labels"]["peg"], d["case_labels"]["no_ar"]], rows,
                 "Illustrative cash balance in the first 13 weeks after closing")


def t_sentiment():
    rows = [[t["theme"], t["where"], t["tone"], t["count_label"]] for t in need("sentiment.themes")]
    return table(["Theme", "Where", "Tone", "Rough count"], rows, "What people are saying, by theme")


def t_timeline():
    rows = [[s["step"], s["typical"], s["source_short"]] for s in need("timeline.steps")]
    return table(["Step", "Typical time", "Source"], rows, "How long each step usually takes")


TABLES = {"stack": t_stack, "sens": t_sens, "scenarios": t_scenarios, "bridge": t_bridge, "qoe": t_qoe, "day1": t_day1,
          "sentiment": t_sentiment, "timeline": t_timeline}


# ---------------------------------------------------------------- sources section (generated)
def source_urls() -> set:
    return {i["url"] for g in SOURCES["groups"] for i in g["items"] if i.get("url")}


def sources_md() -> str:
    L = ["## Sources {#sources}", "", SOURCES["intro"], ""]
    for g in SOURCES["groups"]:
        L += [f"### {g['title']}", ""]
        if g.get("note"):
            L += [g["note"], ""]
        for i in g["items"]:
            title = f"[{i['title']}]({i['url']})" if i.get("url") else i["title"]
            via = f" ({i['via']})" if i.get("via") else ""
            date = f", {i['date']}" if i.get("date") else ""
            L.append(f"- {i['org']}, \"{title}\"{date}{via}.")
        L.append("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- build
def md_to_html(text: str) -> str:
    out = markdown.markdown(text, extensions=["tables", "attr_list", "md_in_html", "fenced_code"], output_format="html5")
    out = re.sub(r"<table>", '<div class="table-wrap"><table>', out).replace("</table>", "</table></div>")
    out = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', out)
    return out


def check_text(name: str, text: str) -> None:
    for ch, label in BANNED_CHARS.items():
        if ch in text:
            line = text[: text.index(ch)].count("\n") + 1
            sys.exit(f"build: {name} line {line} contains an {label}")


def load_copy() -> str:
    parts, links = [], []
    for name in ORDER:
        p = CONTENT / name
        if not p.exists():
            if DRAFT:
                print(f"build: note: {name} missing (draft mode)")
                continue
            sys.exit(f"build: content/{name} is missing")
        text = re.sub(r"\s?<!-- src:[a-z0-9-]+ -->", "", p.read_text())  # source markers feed model/sources.json only
        check_text(f"content/{name}", text)
        links += [(name, u) for u in LINK_RE.findall(text)]
        parts.append(text)
    known = source_urls()
    unlisted = sorted({f"{n}: {u}" for n, u in links if u not in known and not u.startswith(OWN_LINKS)})
    if unlisted:
        msg = "build: link(s) in the copy missing from model/sources.json:\n  " + "\n  ".join(unlisted)
        if DRAFT:
            print(msg.replace("build:", "build: note:", 1))
        else:
            sys.exit(msg)
    parts.append(sources_md())
    return "\n\n".join(parts)


def split_sections(text: str):
    matches = list(SECTION_RE.finditer(text))
    intro = text[: matches[0].start()] if matches else text
    sections = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if m.group(2) in sections:
            sys.exit(f"build: section id '{m.group(2)}' appears twice")
        sections[m.group(2)] = f"## {m.group(1)}\n{text[m.end():end]}".strip() + "\n"
    return intro, sections


def insert_figures(html_text: str, used: list) -> str:
    def rep(m):
        fid = m.group(1)
        used.append(fid)
        p = FIGS / f"{fid}.html"
        if not p.exists():
            if DRAFT:
                return f'<figure class="fig" id="{fid}"><p class="fig-title">[{fid} pending]</p></figure>'
            sys.exit(f"build: figure partial templates/figures/{fid}.html is missing")
        part = p.read_text()
        check_text(f"templates/figures/{fid}.html", part)
        part = TABLE_RE.sub(lambda t: TABLES[t.group(1)]() if t.group(1) in TABLES else sys.exit(f"build: unknown TABLE:{t.group(1)}"), part)
        return fill_hooks(part, f"templates/figures/{fid}.html")
    return FIG_RE.sub(rep, html_text)


def main() -> None:
    (DOCS / "assets").mkdir(parents=True, exist_ok=True)
    (DOCS / "assets" / "data.js").write_text("// Generated from model/site_data.json by build.py. Do not edit by hand.\n"
                                              "window.SITE_DATA = " + json.dumps(DATA, separators=(",", ":")) + ";\n")
    intro, sections = split_sections(load_copy())
    page = (TEMPLATES / "index.html").read_text()
    wanted = PLACEHOLDER_RE.findall(page)
    intro_md = re.sub(r"^# .*$", "", intro, flags=re.M).strip()
    sections["intro"] = intro_md
    missing = [k for k in wanted if k not in sections]
    extra = [k for k in sections if k not in wanted]
    if missing and not DRAFT:
        sys.exit(f"build: no copy for placeholder(s): {', '.join(missing)}")
    if extra:
        sys.exit(f"build: copy with no placeholder: {', '.join(extra)}")

    def fill(m):
        key = m.group(1)
        if key not in sections:
            return f"<p>[{key} pending]</p>"
        out = md_to_html(sections[key])
        return out.replace("<p>", '<p class="dek">', 1) if key == "intro" else out

    page = PLACEHOLDER_RE.sub(fill, page)
    page = page.replace("<!-- DISCLAIMER -->", DISCLAIMER)
    used = []
    page = insert_figures(page, used)
    dup = sorted({f for f in used if used.count(f) > 1})
    if dup:
        sys.exit(f"build: figure(s) placed more than once: {dup}")
    unused = sorted(p.stem for p in FIGS.glob("fig-*.html") if p.stem not in used) if FIGS.exists() else []
    if unused:
        print(f"build: note: figure partial(s) not placed: {unused}")
    check_text("docs/index.html", page)
    left = PLACEHOLDER_RE.findall(page) + FIG_RE.findall(page) + TABLE_RE.findall(page)
    if left and not DRAFT:
        sys.exit(f"build: docs/index.html still has placeholder(s): {left}")
    (DOCS / "index.html").write_text(page)
    (DOCS / ".nojekyll").write_text("")
    print(f"build: wrote docs/index.html ({len(page):,} bytes, {len(used)} figures), docs/assets/data.js"
          + (" [draft]" if DRAFT else ""))


if __name__ == "__main__":
    main()
