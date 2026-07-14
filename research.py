"""Render vault ticker research files into static Terminal pages.

Reads YOUNG-BULL/Research/Tickers/*.md (YAML-ish frontmatter + markdown body)
and writes docs/t/<TICKER>.html. Stdlib only, no yaml/markdown deps: the
parsers below handle exactly the subset these files use.
"""

import re
from html import escape

from sections import FAVICON, og_tags
from pathlib import Path

TICKERS_DIR = Path.home() / "Quinn/YOUNG-BULL/Research/Tickers"

CSS = """
:root {
  --bg: #080a0f;
  --surface: #0d1017;
  --border: #191f2d;
  --text: #c8cdd6;
  --bright: #e8ecf2;
  --dim: #4e5a6e;
  --gold: #c8952e;
  --green: #22c55e;
  --red: #ef4444;
  --line: #191f2d;
  --mono: 'SF Mono', 'JetBrains Mono', Menlo, Consolas, monospace;
  --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; }
body {
  background: var(--bg); color: var(--text);
  font: 15px/1.6 var(--sans); padding: 0;
  -webkit-font-smoothing: antialiased;
}
main { max-width: 860px; margin: 0 auto; padding: 24px 16px 80px; }
a { color: var(--gold); text-decoration: none; }
a:hover { text-decoration: underline; }
h1 {
  font-size: 18px; letter-spacing: 3px; color: var(--gold);
  font-weight: 700; text-transform: uppercase;
}
section {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 20px; margin-bottom: 14px;
}
h2 {
  font-size: 10px; letter-spacing: 2px; color: var(--dim);
  text-transform: uppercase; margin-bottom: 14px; font-weight: 600;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}
.sub { color: var(--dim); font-size: 12px; line-height: 1.5; }
.stats { display: flex; gap: 20px; flex-wrap: wrap; }
.stat b {
  display: block; font-size: 20px; font-family: var(--mono);
  font-variant-numeric: tabular-nums; color: var(--bright);
}
.stat span {
  color: var(--dim); font-size: 10px; text-transform: uppercase;
  letter-spacing: 1px;
}
table {
  width: 100%; border-collapse: collapse; font-size: 13px;
  font-variant-numeric: tabular-nums;
}
th {
  text-align: left; color: var(--dim); font-weight: 500;
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;
  padding: 8px; border-bottom: 1px solid var(--border);
}
th:not(:first-child) { text-align: right; }
td { padding: 9px 8px; border-bottom: 1px solid rgba(25, 31, 45, 0.5); }
td:not(:first-child) { text-align: right; font-family: var(--mono); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(25, 31, 45, 0.4); }
.tk { color: var(--gold); font-weight: 700; font-family: var(--mono); }
.up { color: var(--green); } .down { color: var(--red); }
.chip {
  display: inline-block; background: var(--bg); border: 1px solid var(--border);
  border-radius: 6px; padding: 4px 10px; margin: 3px 4px 3px 0;
  font-size: 12px; font-family: var(--mono); transition: border-color 0.15s;
  color: var(--text);
}
a.chip:hover { border-color: var(--gold); text-decoration: none; }
.chip.up { border-color: rgba(34, 197, 94, 0.3); }
.chip.down { border-color: rgba(239, 68, 68, 0.2); }
.read { font-size: 15px; line-height: 1.7; }
.note {
  border-left: 2px solid var(--gold); padding-left: 14px;
  color: var(--dim); font-size: 12px; margin-bottom: 16px;
}
footer {
  color: var(--dim); font-size: 11px; margin-top: 32px;
  text-align: center; line-height: 1.6;
}

/* Research body styles */
.body h1 { font-size: 17px; margin: 18px 0 8px; letter-spacing: 0; color: var(--bright); text-transform: none; }
.body h2 { font-size: 15px; margin: 16px 0 8px; color: var(--bright); text-transform: none; letter-spacing: 0; border: none; padding: 0; }
.body h3 { font-size: 14px; margin: 14px 0 6px; color: var(--gold); text-transform: none; letter-spacing: 0; border: none; padding: 0; }
.body p { margin: 8px 0; }
.body ul { margin: 8px 0 8px 20px; }
.body blockquote { border-left: 2px solid var(--border); padding: 4px 14px; color: var(--dim); margin: 10px 0; }
.body table { margin: 10px 0; }
.body code { color: var(--gold); font-size: 13px; }
.kill li { color: var(--red); }

@media (max-width: 600px) {
  td:nth-child(3), th:nth-child(3) { display: none; }
  .stats { gap: 14px; }
  .stat b { font-size: 18px; }
  section { padding: 16px; }
  main { padding: 16px 12px 80px; }
}
"""


def parse_frontmatter(text):
    """Parse the leading --- block into a dict. Returns (meta, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    meta = {}
    for line in text[3:end].strip().splitlines():
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw.startswith("[") and raw.endswith("]"):
            meta[key] = [v.strip().strip("'\"") for v in raw[1:-1].split(",") if v.strip()]
        else:
            meta[key] = raw.strip("'\"")
    return meta, text[end + 4:]


def _inline(s):
    s = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
               r'<a href="\2" rel="noopener">\1</a>', s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md_to_html(md):
    """Minimal markdown renderer for the subset in the ticker files."""
    out, para, ul, bq, table = [], [], [], [], []

    def flush():
        if para:
            out.append("<p>" + " ".join(para) + "</p>"); para.clear()
        if ul:
            out.append("<ul>" + "".join(ul) + "</ul>"); ul.clear()
        if bq:
            out.append("<blockquote>" + "".join(bq) + "</blockquote>"); bq.clear()
        if table:
            out.append("<table>" + "".join(table) + "</table>"); table.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        s = _inline(escape(line.strip()))
        if not line.strip():
            flush(); continue
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            flush(); out.append(f"<h{len(m.group(1))}>{_inline(escape(m.group(2)))}</h{len(m.group(1))}>")
        elif line.strip().startswith(">"):
            if para or ul or table: flush()
            bq.append("<p>" + _inline(escape(line.strip()[1:].strip())) + "</p>")
        elif re.match(r"^\s*[-*]\s+", line):
            if para or bq or table: flush()
            ul.append("<li>" + _inline(escape(re.sub(r"^\s*[-*]\s+", "", line))) + "</li>")
        elif line.strip().startswith("|"):
            if para or ul or bq: flush()
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue
            tag = "th" if not table else "td"
            table.append("<tr>" + "".join(
                f"<{tag}>{_inline(escape(c))}</{tag}>" for c in cells) + "</tr>")
        else:
            if ul or bq or table: flush()
            para.append(s)
    flush()
    return "\n".join(out)


def render_ticker_page(ticker, meta, body_html, quote, row, generated_at):
    price = quote.get("price") if quote else None
    change = quote.get("changePct") if quote else None

    def c(v):
        return "" if v is None else ("up" if v >= 0 else "down")

    stats = []
    if price is not None:
        stats.append(f"<div class='stat'><b>${price:,.2f}</b><span>Live</span></div>")
        stats.append(f"<div class='stat'><b class='{c(change)}'>{change:+.2f}%</b><span>Today</span></div>")
    if row:
        if row.get("cost"):
            stats.append(f"<div class='stat'><b>${row['cost']:,.2f}</b><span>My avg cost</span></div>")
        if row.get("gain") is not None:
            stats.append(f"<div class='stat'><b class='{c(row['gain'])}'>{row['gain']:+.1f}%</b><span>My gain</span></div>")
        if row.get("weight"):
            stats.append(f"<div class='stat'><b>{row['weight']:.1f}%</b><span>Of book</span></div>")
    held = "HELD" if row else str(meta.get("status", "coverage")).upper()

    chips = "".join(
        f"<span class='chip'>{escape(str(meta[k]))}</span>"
        for k in ("layer", "sleeve", "moat_type") if meta.get(k) and meta[k] != "null"
    )
    kills = ""
    kv = meta.get("kill_vectors") or []
    if kv:
        kills = ("<section><h2>What Kills The Thesis</h2><ul class='kill'>"
                 + "".join(f"<li>{escape(k)}</li>" for k in kv) + "</ul></section>")
    thesis = escape(str(meta.get("thesis_short", "")))
    edited = escape(str(meta.get("last_edited", "?")))

    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(ticker)} | Young Bull</title>
{f'<meta name="description" content="{thesis}">' if thesis else ''}
{og_tags(f"{ticker} | Young Bull", str(meta.get("thesis_short") or f"{ticker} research"), f"t/{ticker}.html")}
{FAVICON}
<style>{CSS}</style></head><body><main>
<div class="sub" style="margin-bottom:16px"><a href="../">&larr; Terminal</a></div>
<h1>{escape(ticker)} <span class="chip" style="font-size:11px">{escape(held)}</span></h1>
<div class="sub" style="margin-bottom:16px">Research page. Generated {escape(generated_at)}.</div>
<section><div class="stats">{''.join(stats) or '<span class="sub">no live quote</span>'}</div></section>
{f'<section><h2>Why I Own It</h2><p class="read">{thesis}</p><div style="margin-top:12px">{chips}</div></section>' if thesis else ''}
{kills}
<section><h2>The Research Note</h2>
<div class="note">Written by me, last edited {edited}. Prices and position sizes inside
reflect that date. The live numbers above are current.</div>
<div class="body">{body_html}</div></section>
<footer>Young Bull. Not advice, it is my book, my research, my machine.</footer>
</main></body></html>"""


def list_research_tickers():
    if not TICKERS_DIR.is_dir():
        return []
    return sorted(p.stem for p in TICKERS_DIR.glob("*.md") if p.stem != "INDEX")


def build_research(out_dir, quotes, rows_by_ticker, generated_at):
    """Write docs/t/<T>.html for every research file. Returns set of tickers built."""
    built = set()
    tdir = out_dir / "t"
    tdir.mkdir(parents=True, exist_ok=True)
    for ticker in list_research_tickers():
        try:
            meta, body = parse_frontmatter(
                (TICKERS_DIR / f"{ticker}.md").read_text(encoding="utf-8"))
            html = render_ticker_page(
                ticker, meta, md_to_html(body),
                quotes.get(ticker), rows_by_ticker.get(ticker), generated_at)
            (tdir / f"{ticker}.html").write_text(html, encoding="utf-8")
            built.add(ticker)
        except Exception as e:
            print(f"  WARN: skipped {ticker}: {e}")
    return built
