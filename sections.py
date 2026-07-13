"""HTML builders for the Terminal's v2 sections: tape, thesis cards, record.

Pure string builders, no network. Everything rendered here arrives already
computed; missing values render as blanks or are skipped entirely.
"""

from html import escape

EXTRA_CSS = """
  /* Badges + cards + tape (v2 sprint) */
  .badge { display:inline-block; border-radius:5px; padding:2px 8px; font-size:11px;
           font-weight:700; letter-spacing:1px; }
  .badge.INTACT { color:var(--green); border:1px solid var(--green); }
  .badge.STRESSED { color:var(--gold); border:1px solid var(--gold); }
  .badge.BROKEN { color:var(--red); border:1px solid var(--red); }
  .tape-item { padding:10px 0; border-bottom:1px solid var(--line); }
  .tape-item:last-child { border-bottom:none; }
  .wire { font-size:12px; color:var(--dim); margin-top:4px; }
  .cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr));
           gap:12px; }
  .card { background:var(--bg); border:1px solid var(--line); border-radius:8px;
          padding:14px; }
  .card .row { display:flex; justify-content:space-between; align-items:baseline;
               margin-bottom:6px; }
  .card .meta { color:var(--dim); font-size:12px; margin-top:8px; }
  .card .thesis { font-size:13px; line-height:1.5; margin-top:6px; }

  /* Nav */
  .yb-nav {
    position: sticky; top: 0; z-index: 10;
    background: rgba(8, 10, 15, 0.92);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 0 16px;
  }
  .yb-nav-inner {
    max-width: 860px; margin: 0 auto;
    display: flex; align-items: center; justify-content: space-between;
    height: 52px;
  }
  .yb-nav .brand {
    font-size: 13px; letter-spacing: 3px; color: var(--gold);
    font-weight: 700; text-transform: uppercase; text-decoration: none;
  }
  .yb-nav-links { display: flex; gap: 6px; }
  .yb-nav-links a {
    font-size: 12px; color: var(--dim); padding: 6px 12px;
    border-radius: 6px; transition: color 0.15s, background 0.15s;
    text-decoration: none; letter-spacing: 0.3px;
  }
  .yb-nav-links a:hover { color: var(--bright); background: var(--surface); }
  .yb-nav-links a.ext { color: var(--gold); }

  /* Hero stats grid */
  .hero-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1px; background: var(--border); border-radius: 8px;
    overflow: hidden; margin-bottom: 14px;
  }
  .hero-cell {
    background: var(--surface); padding: 18px 16px;
  }
  .hero-cell b {
    display: block; font-size: 22px; font-family: var(--mono);
    font-variant-numeric: tabular-nums; color: var(--bright);
  }
  .hero-cell span {
    color: var(--dim); font-size: 10px; text-transform: uppercase;
    letter-spacing: 1px; margin-top: 4px; display: block;
  }

  /* Moves */
  .move { margin: 6px 0; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .move .chip { margin: 0; font-size: 11px; padding: 2px 8px; }

  /* Tracker */
  .tracker-form {
    display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap;
  }
  .tracker-form input {
    background: var(--bg); border: 1px solid var(--border); color: var(--text);
    padding: 10px 14px; border-radius: 6px; font-family: var(--mono);
    font-size: 13px; width: 100%;
  }
  .tracker-form input:focus { outline: none; border-color: var(--gold); }
  .tracker-form .field { flex: 1; min-width: 100px; }
  .tracker-form .field label {
    display: block; font-size: 10px; color: var(--dim);
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;
  }
  .btn-gold {
    background: var(--gold); color: var(--bg); border: none;
    padding: 10px 20px; border-radius: 6px; font-weight: 700;
    font-size: 12px; letter-spacing: 0.5px; text-transform: uppercase;
    cursor: pointer; transition: opacity 0.15s; align-self: flex-end;
  }
  .btn-gold:hover { opacity: 0.85; }
  .btn-rm {
    background: none; border: 1px solid var(--border); color: var(--dim);
    width: 24px; height: 24px; border-radius: 4px; cursor: pointer;
    font-size: 12px; display: inline-flex; align-items: center;
    justify-content: center; transition: border-color 0.15s, color 0.15s;
  }
  .btn-rm:hover { border-color: var(--red); color: var(--red); }
  #tracker-summary {
    font-family: var(--mono); font-size: 14px; margin-bottom: 12px;
  }
  .tracker-empty {
    text-align: center; padding: 24px; color: var(--dim); font-size: 13px;
  }

  /* CTA */
  .cta-section {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 32px; margin-bottom: 14px;
    text-align: center;
  }
  .cta-section h2 { border: none; padding: 0; margin-bottom: 10px; }
  .cta-section p { color: var(--dim); font-size: 14px; margin-bottom: 18px; }
  .cta-btn {
    display: inline-block; background: var(--gold); color: var(--bg);
    padding: 12px 28px; border-radius: 8px; font-weight: 700;
    font-size: 14px; text-decoration: none; transition: opacity 0.15s;
  }
  .cta-btn:hover { opacity: 0.85; text-decoration: none; }

  /* Tagline */
  .tagline {
    text-align: center; padding: 32px 16px 8px; color: var(--dim);
    font-size: 14px;
  }
  .tagline b { color: var(--bright); }

  @media (max-width: 600px) {
    .hero-grid { grid-template-columns: repeat(2, 1fr); }
    .yb-nav-links a { padding: 6px 8px; font-size: 11px; }
    .tracker-form { flex-direction: column; }
    .tracker-form .field { min-width: unset; }
    .cards { grid-template-columns: 1fr; }
  }
"""


def _cls(v):
    if v is None:
        return ""
    return "up" if v >= 0 else "down"


def _pct(v, spec="+.2f"):
    return format(v, spec) + "%" if v is not None else "-"


def tape_html(tape):
    if not tape:
        return ""
    items = []
    for i in tape:
        t = escape(i["t"])
        wire = ""
        if i.get("wire"):
            w = i["wire"]
            wire = (f"<div class='wire'>On the wire: <a href='{escape(w['url'])}' "
                    f"rel='noopener'>{escape(w['title'])}</a> "
                    f"({escape(w['source'])})</div>")
        items.append(
            f"<div class='tape-item'>"
            f"<span class='tk'>{t}</span> "
            f"<span class='chip {_cls(i['change'])}'>{_pct(i['change'])}</span> "
            f"<span style='font-size:13px'>{escape(i['line'])}</span>{wire}</div>")
    return ("<section><h2>The Tape: What Changed Today</h2>"
            "<div class='sub' style='margin-bottom:6px'>Every held name, biggest move "
            "first, each one framed against the written thesis. Rebuilt automatically "
            "at every refresh.</div>" + "".join(items) + "</section>")


def _card(c):
    badge = (f"<span class='badge {c['health']}'>{c['health']}</span>"
             if c["health"] else "")
    conviction = ""
    if c.get("conviction") is not None:
        conviction = (f"<div class='meta'>Machine desk: {int(c['conviction'])}/100 "
                      f"{escape(c.get('stance') or '')}</div>")
    receipt = ""
    if c.get("receipt"):
        r = c["receipt"]
        receipt = (f"<div class='meta'>The call: <a href='{escape(r['url'])}' "
                   f"rel='noopener'>{escape(r['title'])}</a> "
                   f"({escape(r['date'])}, at ${r['price']:,.2f})</div>"
                   if r.get("price") else
                   f"<div class='meta'>The call: <a href='{escape(r['url'])}' "
                   f"rel='noopener'>{escape(r['title'])}</a> ({escape(r['date'])})</div>")
    catalyst = ""
    if c.get("catalyst"):
        catalyst = (f"<div class='meta'>Next catalyst: "
                    f"{escape(c['catalyst']['label'])} {escape(c['catalyst']['date'])}</div>")
    thesis = (f"<div class='thesis'>{escape(c['thesis_short'])}</div>"
              if c["thesis_short"] else "")
    layer = (f"<span class='chip'>{escape(c['layer'])}</span>" if c["layer"] else "")
    gain = (f"<span class='{_cls(c['gain'])}'>{_pct(c['gain'], '+.1f')} on cost</span>"
            if c["gain"] is not None else "")
    return (f"<div class='card'><div class='row'>"
            f"<span><a class='tk' href='t/{escape(c['t'])}.html'>{escape(c['t'])}</a> "
            f"{badge}</span><span style='font-size:12px'>{gain}</span></div>"
            f"{thesis}<div style='margin-top:8px'>{layer}</div>"
            f"{receipt}{catalyst}{conviction}</div>")


def cards_html(cards):
    if not cards:
        return ""
    return ("<section><h2>Living Thesis Cards</h2>"
            "<div class='sub' style='margin-bottom:10px'>One card per position. The "
            "health badge is pure math against my entry, INTACT within 15% of cost, "
            "STRESSED past that, BROKEN past 30%. The receipt links the post where I "
            "made the call in public.</div>"
            "<div class='cards'>" + "".join(_card(c) for c in cards) + "</div></section>")


def record_page_html(rows, unscored, stats, generated_at, css):
    avg = stats["bull_avg_pct"]
    stat_blocks = f"""
<div class="stats">
  <div class="stat"><b>{stats['bull_scored']}</b><span>Calls scored</span></div>
  <div class="stat"><b class="up">{stats['bull_winners']}</b><span>Winners</span></div>
  <div class="stat"><b class="down">{stats['bull_losers']}</b><span>Losers</span></div>
  <div class="stat"><b class="{_cls(avg)}">{_pct(avg, '+.1f')}</b><span>Avg call, equal weight</span></div>
  <div class="stat"><b>{stats['avoid_aged_well']}/{stats['avoid_scored']}</b><span>Avoid calls aged well</span></div>
</div>"""
    unscored_html = ""
    if unscored:
        items = "".join(
            f"<li><span class='tk'>{escape(u['t'])}</span> {escape(u['call_date'])}, "
            f"<a href='{escape(u['url'])}' rel='noopener'>{escape(u['title'])}</a>. "
            f"{escape(u.get('note', ''))}</li>"
            for u in unscored)
        unscored_html = (
            "<section><h2>Unscored Calls</h2><div class='sub' style='margin-bottom:8px'>"
            "Public calls with no verifiable price receipt at call time. They stay on "
            "the page because hiding them would be curating the record.</div>"
            f"<ul style='margin-left:20px;font-size:13px'>{items}</ul></section>")
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Track Record | Young Bull Terminal</title>
<style>{css}{EXTRA_CSS}</style></head><body><main>
<div class="sub"><a href="index.html">&larr; Terminal</a></div>
<h1>THE RECORD</h1>
<div class="sub">Every public call, scored. Generated {escape(generated_at)}.
Winners and losers on the same page, because a track record you can edit is not
a track record.</div>
<section>{stat_blocks}</section>
<section><h2>Every Public Call</h2>
<div class='sub' style='margin-bottom:8px'>Price at call is the price printed in the
post itself, or the capture from my own price feed on the call day. Open calls score
against the live quote at refresh time. Closed calls are frozen at the exit-day price.
No third-party backfill, no adjustments, no exceptions. Blank means no verifiable
receipt exists.</div>
<table><thead><tr><th>Ticker</th><th>Call</th><th>Date</th><th>At call</th>
<th>Now / exit</th><th>Return</th><th>Receipt</th></tr></thead>
<tbody>{record_rows_html(rows)}</tbody></table></section>
{unscored_html}
<footer>Young Bull Terminal. Not advice, it is my book and my record. The losers
stay up. That is the product.</footer>
</main></body></html>"""


def pricing_page_html(css):
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pricing | Young Bull Terminal</title>
<style>{css}{EXTRA_CSS}</style></head><body><main>
<div class="sub"><a href="index.html">&larr; Terminal</a></div>
<h1>WHAT HAPPENS JULY 22</h1>
<div class="sub">The short version: the Terminal stays free until my 18th birthday,
July 22, 2026. After that it becomes a paid-subscriber perk.</div>

<section><h2>Why July 22</h2>
<p class="read">I am 17. I legally cannot charge you until I am 18. So everything I
have built this year has been free while the pledges stacked up. On July 22 the
paid tier switches on, the pledges convert, and this page stops being hypothetical.
If you have already pledged, thank you. You do not need to do anything, Substack
handles it on the day.</p></section>

<section><h2>What stays free</h2>
<ul style="margin-left:20px;font-size:14px;line-height:1.8">
<li>The free posts on the Substack, same as always.</li>
</ul></section>

<section><h2>What paid gets you</h2>
<ul style="margin-left:20px;font-size:14px;line-height:1.8">
<li><b>The Terminal.</b> This site. My live book with real entries and real weights,
the daily Tape, the thesis card on every position, and the moves feed that posts my
buys and sells automatically. No one else my size shows you this much.</li>
<li><b>The deep dives.</b> The full research notes behind every position, the
paywalled posts, and every teardown that goes behind the paywall from here on.</li>
<li><b>The machine.</b> The same AI research desk that runs my book runs this site.
Paid subscribers are the reason it exists and the first to get whatever it builds
next.</li>
</ul></section>

<section><h2>The price</h2>
<div class="stats">
  <div class="stat"><b>$99/yr</b><span>Founding, locked for life</span></div>
  <div class="stat"><b>$199/yr</b><span>Standard, after founding closes</span></div>
</div>
<p class="read" style="margin-top:10px">Founding members lock in $99 a year for life
before the price goes up. That is the whole pitch. No tiers inside tiers, no upsells.
<a href="https://youngbullinvests.substack.com/subscribe" rel="noopener">Subscribe on
Substack</a> and the Terminal link lands in your welcome email on the 22nd.</p></section>

<footer>Young Bull Terminal. Not advice, it is my book and my machine. Questions?
Reply to any post, I read everything.</footer>
</main></body></html>"""


def record_rows_html(rows):
    out = []
    for r in rows:
        title = f"{escape(r['title'])}"
        link = f"<a href='{escape(r['url'])}' rel='noopener'>{title}</a>"
        status = "CLOSED" if r.get("status") == "closed" else r["direction"].upper()
        now_label = (f"${r['price_now']:,.2f}" if r.get("price_now") is not None else "-")
        at_call = (f"${r['price_at_call']:,.2f}"
                   if r.get("price_at_call") is not None else "-")
        color_pct = r["pct"]
        if r["direction"] == "avoid" and color_pct is not None:
            color_pct = -color_pct  # an avoid call ages well when price falls
        out.append(
            f"<tr><td class='tk'>{escape(r['t'])}</td>"
            f"<td><span class='chip'>{status}</span></td>"
            f"<td>{escape(r['call_date'])}</td>"
            f"<td>{at_call}</td><td>{now_label}</td>"
            f"<td class='{_cls(color_pct)}'>{_pct(r['pct'], '+.1f')}</td>"
            f"<td style='font-size:12px'>{link}</td></tr>")
    return "".join(out)
