"""Render vault ticker research files into static Terminal pages.

Reads YOUNG-BULL/Research/Tickers/*.md (YAML-ish frontmatter + markdown body)
and writes docs/t/<TICKER>.html. Stdlib only, no yaml/markdown deps: the
parsers below handle exactly the subset these files use.
"""

import re
from html import escape
from pathlib import Path

TICKERS_DIR = Path.home() / "Quinn/YOUNG-BULL/Research/Tickers"

CSS = """
  :root { --bg:#0a0e12; --panel:#11161d; --line:#1e2630; --text:#e8edf2;
          --dim:#8b98a5; --green:#2ecc71; --red:#ff5c5c; --gold:#f0b90b; }
  * { box-sizing:border-box; margin:0; }
  body { background:var(--bg); color:var(--text); padding:24px 16px 60px;
         font:15px/1.5 -apple-system, "SF Mono", Menlo, monospace; }
  main { max-width:820px; margin:0 auto; }
  h1 { font-size:20px; letter-spacing:2px; color:var(--gold); }
  a { color:var(--gold); text-decoration:none; }
  a:hover { text-decoration:underline; }
  .sub { color:var(--dim); font-size:12px; margin:4px 0 24px; }
  section { background:var(--panel); border:1px solid var(--line);
            border-radius:10px; padding:18px; margin-bottom:18px; }
  h2 { font-size:13px; letter-spacing:1.5px; color:var(--dim);
       text-transform:uppercase; margin-bottom:12px; }
  .stats { display:flex; gap:24px; flex-wrap:wrap; margin-bottom:6px; }
  .stat b { display:block; font-size:22px; }
  .stat span { color:var(--dim); font-size:11px; text-transform:uppercase; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th { text-align:left; color:var(--dim); font-weight:400; font-size:11px;
       text-transform:uppercase; padding:6px 8px; border-bottom:1px solid var(--line); }
  td { padding:7px 8px; border-bottom:1px solid var(--line); }
  tr:last-child td { border-bottom:none; }
  .tk { color:var(--gold); font-weight:700; }
  .up { color:var(--green); } .down { color:var(--red); }
  .chip { display:inline-block; background:var(--bg); border:1px solid var(--line);
          border-radius:6px; padding:3px 8px; margin:2px 4px 2px 0; font-size:12px; }
  .read { font-size:15px; line-height:1.7; }
  footer { color:var(--dim); font-size:11px; margin-top:24px; }
  .note { border-left:3px solid var(--gold); padding-left:12px; color:var(--dim);
          font-size:12px; margin-bottom:18px; }
  .body h1 { font-size:17px; margin:18px 0 8px; letter-spacing:0; color:var(--text); }
  .body h2 { font-size:15px; margin:16px 0 8px; color:var(--text);
             text-transform:none; letter-spacing:0; }
  .body h3 { font-size:14px; margin:14px 0 6px; color:var(--gold); }
  .body p { margin:8px 0; } .body ul { margin:8px 0 8px 20px; }
  .body blockquote { border-left:3px solid var(--line); padding:4px 12px;
                     color:var(--dim); margin:10px 0; }
  .body table { margin:10px 0; } .body code { color:var(--gold); }
  .kill li { color:var(--red); }
  @media (max-width:520px) { td:nth-child(3), th:nth-child(3) { display:none; } }
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
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)  # relative links: keep text only
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
<meta name="robots" content="noindex, nofollow">
<title>{escape(ticker)} | Young Bull Terminal</title>
<style>{CSS}</style></head><body><main>
<div class="sub"><a href="../index.html">&larr; Terminal</a></div>
<h1>{escape(ticker)} <span class="chip">{escape(held)}</span></h1>
<div class="sub">Research page. Generated {escape(generated_at)}.</div>
<section><div class="stats">{''.join(stats) or '<span class="sub">no live quote</span>'}</div></section>
{f'<section><h2>Why I Own It</h2><p class="read">{thesis}</p><div style="margin-top:10px">{chips}</div></section>' if thesis else ''}
{kills}
<section><h2>The Research Note</h2>
<div class="note">Written by me, last edited {edited}. Prices and position sizes inside
reflect that date. The live numbers above are current.</div>
<div class="body">{body_html}</div></section>
<footer>Young Bull Terminal. Not advice, it is my book, my research, my machine.</footer>
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
        except Exception as e:  # one bad file must not kill the build
            print(f"WARN: skipped {ticker}: {e}")
    return built
