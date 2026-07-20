"""HTML builders for the Terminal's v2 sections: tape, thesis cards, record.

Pure string builders, no network. Everything rendered here arrives already
computed; missing values render as blanks or are skipped entirely.
"""

from html import escape

# Canonical public base: the Terminal IS youngbullinvests.com (Quinn retired
# the old site 07-18). One line to change if it ever moves again.
SITE_BASE = "https://youngbullinvests.com/"

# Stripe Payment Links. QUINN: mint these in the Stripe Dashboard (steps in
# the session report), paste the two URLs here, and the buy buttons appear on
# the pricing page at the next refresh. While either is empty the page keeps
# the Substack subscribe path only, so a dead buy button can never ship.
STRIPE_LINK_FOUNDER = "https://buy.stripe.com/eVq7sN4I91deaJo17X5c400"  # $99/yr founding
STRIPE_LINK_ANNUAL = "https://buy.stripe.com/00w4gB8Yp7BC3gW5od5c401"  # $200/yr standard

FAVICON = ("<link rel=\"icon\" href=\"data:image/svg+xml,<svg xmlns='http://www."
           "w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='14' "
           "fill='%23c8952e'/></svg>\">")


def og_tags(title, description, path=""):
    """Minimal OpenGraph + twitter card block for a public page."""
    url = f"{SITE_BASE}{path}"
    return (f'<meta property="og:title" content="{escape(title)}">\n'
            f'<meta property="og:description" content="{escape(description)}">\n'
            f'<meta property="og:url" content="{url}">\n'
            f'<meta property="og:type" content="website">\n'
            f'<meta name="twitter:card" content="summary">')


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
    background: rgba(247, 249, 252, 0.92);
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

  /* Today at the desk (members triage) */
  #today h2 span { font-size:13px; }
  .today-row { display:flex; gap:10px; padding:7px 0; font-size:13px;
               border-bottom:1px solid var(--line); align-items:baseline; }
  .today-row:last-child { border-bottom:none; }
  .today-tag { font-family:var(--mono); font-size:10px; letter-spacing:1px;
               flex-shrink:0; width:72px; color:var(--dim); }
  .today-tag.gold { color:var(--gold); }
  .today-tag.down { color:var(--red); } .today-tag.up { color:var(--green); }

  /* Tracker tools + watchlist */
  .tracker-tools { display:flex; gap:6px; align-items:center; flex-wrap:wrap;
                   margin-bottom:8px; }
  .watch-hit { border-left:2px solid var(--gold); padding-left:8px; }
  .watch-hit .tk { color:var(--gold); }

  /* Market scan + proving ground */
  .scan-head { font-family:var(--mono); font-size:12px; color:var(--bright);
               letter-spacing:1px; text-transform:uppercase; margin-top:14px; }
  .scan-head:first-of-type { margin-top:0; }
  .stale { color:var(--red); font-size:11px; letter-spacing:1px; }
  .dim { color:var(--dim); }

  /* The Wire */
  .wire-row { display:flex; gap:10px; padding:7px 0; font-size:13px;
              border-bottom:1px solid var(--line); align-items:baseline; }
  .wire-row:last-child { border-bottom:none; }
  .wire-row a { color:var(--text); }
  .wire-row a:hover { color:var(--gold); }
  .wire-src { font-family:var(--mono); font-size:10px; letter-spacing:1px;
              color:var(--dim); flex-shrink:0; width:88px; text-transform:uppercase;
              overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .wire-src.gold { color:var(--gold); }
  .wire-odds-head { font-family:var(--mono); font-size:10px; letter-spacing:2px;
                    color:var(--gold); text-transform:uppercase; margin:12px 0 2px;
                    border-bottom:1px solid var(--border); padding-bottom:4px; }

  /* Catalyst calendar */
  .cal-item { display:flex; gap:12px; padding:8px 0; border-bottom:1px solid var(--line);
              font-size:13px; align-items:baseline; }
  .cal-item:last-child { border-bottom:none; }
  .cal-date { font-family:var(--mono); color:var(--gold); flex-shrink:0; width:44px;
              font-size:12px; }
  .cal-body { flex:1; }
  .cal-why { color:var(--dim); font-size:12px; margin-top:2px; line-height:1.5; }
  .cal-receipt { font-size:11px; border:1px solid var(--border); border-radius:5px;
                 padding:1px 7px; margin-left:6px; }
  .cal-day { margin-bottom:14px; }
  .cal-dayhead { font-family:var(--mono); font-size:11px; color:var(--dim);
                 letter-spacing:1px; border-bottom:1px solid var(--border);
                 padding-bottom:4px; margin-bottom:2px; }

  /* Pro tools: visualizer + scanner */
  .viz-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
              gap:16px; }
  .viz-grid h3, #screens h3 { font-size:11px; letter-spacing:1.5px; color:var(--dim);
              text-transform:uppercase; margin:14px 0 8px; font-weight:600; }
  .bar-row { display:flex; align-items:center; gap:8px; margin:5px 0; font-size:12px;
             font-family:var(--mono); }
  .bar-row .lbl { width:64px; flex-shrink:0; }
  .bar-row .val { width:84px; flex-shrink:0; text-align:right; }
  .bar-track { flex:1; background:var(--bg); border-radius:4px; height:14px;
               overflow:hidden; }
  .bar-fill { display:block; height:100%; background:var(--gold); border-radius:4px; }
  .bar-fill.up { background:var(--green); } .bar-fill.down { background:var(--red); }
  .spark { display:inline-block; margin:4px 10px 4px 0; text-align:center; }
  .spark svg { display:block; }
  .spark .lbl { font-size:11px; font-family:var(--mono); color:var(--dim); }
  .scan-bar { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px;
              align-items:center; }
  .scan-chip { background:var(--bg); border:1px solid var(--border); color:var(--dim);
               border-radius:6px; padding:5px 10px; font-size:11px; cursor:pointer;
               font-family:var(--mono); }
  .scan-chip.active { border-color:var(--gold); color:var(--gold); }
  .viz-note { font-size:12px; color:var(--dim); margin-top:6px; }

  @media (max-width: 600px) {
    .hero-grid { grid-template-columns: repeat(2, 1fr); }
    .yb-nav .brand { font-size: 11px; letter-spacing: 2px; white-space: nowrap; }
    .yb-nav-links a { padding: 6px 6px; font-size: 11px; white-space: nowrap; }
    .yb-nav-links { gap: 0; overflow-x: auto; scrollbar-width: none; }
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


def _card(c, pages):
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
    name = (f"<a class='tk' href='t/{escape(c['t'])}.html'>{escape(c['t'])}</a>"
            if c["t"] in pages else f"<span class='tk'>{escape(c['t'])}</span>")
    return (f"<div class='card'><div class='row'>"
            f"<span>{name} "
            f"{badge}</span><span style='font-size:12px'>{gain}</span></div>"
            f"{thesis}<div style='margin-top:8px'>{layer}</div>"
            f"{receipt}{catalyst}{conviction}</div>")


def cards_html(cards, pages=frozenset()):
    if not cards:
        return ""
    return ("<section><h2>Living Thesis Cards</h2>"
            "<div class='sub' style='margin-bottom:10px'>One card per position. The "
            "health badge is pure math against my entry, INTACT within 15% of cost, "
            "STRESSED past that, BROKEN past 30%. The receipt links the post where I "
            "made the call in public.</div>"
            "<div class='cards'>" + "".join(_card(c, pages) for c in cards) + "</div></section>")


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


WEEK_STRIP_LABELS = (
    ("desknote", "desk notes filed"),
    ("content", "drafts staged for review"),
    ("reviews", "reviews run"),
    ("fixes", "pipelines self-healed"),
    ("briefings", "morning briefings compiled"),
    ("monitoring", "health alerts triaged"),
)


def week_strip_html(counts):
    """What the machine actually did in the last 7 days, from the mission
    log. Zero activity renders nothing rather than an empty boast."""
    parts = [f"<div class='stat'><b>{counts[k]}</b><span>{label}</span></div>"
             for k, label in WEEK_STRIP_LABELS if counts.get(k)]
    if not parts:
        return ""
    return (f"<section><h2>What Members Got This Week</h2>"
            f"<div class='sub' style='margin-bottom:10px'>Straight from the "
            f"machine's own action log, last 7 days. Counts, not promises.</div>"
            f"<div class='stats'>{''.join(parts)}</div></section>")


def _buy_buttons():
    if not (STRIPE_LINK_FOUNDER and STRIPE_LINK_ANNUAL):
        return ("<a href=\"https://youngbullinvests.substack.com/subscribe\" "
                "rel=\"noopener\" class=\"cta-btn\">Subscribe on Substack</a>")
    return (f"<a href=\"{escape(STRIPE_LINK_FOUNDER)}\" rel=\"noopener\" "
            f"class=\"cta-btn\">Lock $99/yr founding</a> "
            f"<a href=\"{escape(STRIPE_LINK_ANNUAL)}\" rel=\"noopener\" "
            f"class=\"cta-btn\" style=\"background:none;border:1px solid "
            f"var(--gold);color:var(--gold)\">$200/yr standard</a>")


FOUNDER_NOTE = """<section><h2>From Me</h2>
<p class="read">I built this machine because I could not afford a Bloomberg and
refused to invest blind. $99 is what it costs to sit at the same desk I sit at,
with my real book, my receipts, and the staff that never sleeps. If that is not
worth $8.25 a month, do not buy it, the free posts stay free.</p></section>"""


def pricing_page_html(css, week_counts=None):
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pricing | Young Bull</title>
<meta name="description" content="What stays free and what paid adds when Young Bull flips paid on July 22, 2026. Founding members lock $99 a year for life.">
{og_tags("Pricing | Young Bull", "Founding members lock $99 a year for life before the price goes up.", "pricing.html")}
{FAVICON}
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
<li><b>The tools.</b> Track your own book, see it visualized, run it against my
coverage with the Scanner: layers, health badges, machine conviction, and real
earnings dates. All computed from data the machine actually has, never invented.</li>
<li><b>The deep dives.</b> The full research notes behind every position, the
paywalled posts, and every teardown that goes behind the paywall from here on.</li>
<li><b>The machine.</b> The same AI research desk that runs my book runs this site.
Paid subscribers are the reason it exists and the first to get whatever it builds
next.</li>
</ul></section>

{week_strip_html(week_counts or {})}

<section><h2>The price</h2>
<div class="stats">
  <div class="stat"><b>$99/yr</b><span>Founding, locked for life</span></div>
  <div class="stat"><b>$200/yr</b><span>Standard, after founding closes</span></div>
</div>
<p class="read" style="margin-top:10px;margin-bottom:16px">Founding members lock in
$99 a year for life before the price goes up. That is the whole pitch. No tiers
inside tiers, no upsells. The Terminal members link lands in your welcome email
on the 22nd.</p>
{_buy_buttons()}</section>

{FOUNDER_NOTE}

<footer>Young Bull Terminal. Not advice, it is my book and my machine. Questions?
Reply to any post, I read everything.</footer>
</main></body></html>"""


def wire_html(items, limit):
    """The Wire: what the desk's scout is reading right now, scored against
    the Physical Layer beats, plus the odds board (prediction-market implied
    probabilities). Real headlines, real links, or nothing at all."""
    if not items:
        return ""
    odds = [i for i in items if i.get("source") == "Polymarket"]
    news = [i for i in items if i.get("source") != "Polymarket"][:limit]
    if not news and not odds:
        return ""
    rows = "".join(
        f"<div class='wire-row'><span class='wire-src'>{escape(i['source'])}</span>"
        f"<a href='{escape(i['url'])}' rel='noopener'>{escape(i['title'])}</a></div>"
        for i in news)
    odds_rows = ""
    if odds:
        odds_rows = ("<div class='wire-odds-head'>The odds board</div>" + "".join(
            f"<div class='wire-row'><span class='wire-src gold'>ODDS</span>"
            f"<a href='{escape(i['url'])}' rel='noopener'>{escape(i['title'])}</a></div>"
            for i in odds[:5]))
    return (f"<section id='wire'><h2>The Wire</h2>"
            f"<div class='sub' style='margin-bottom:8px'>What the desk's scout is "
            f"reading, scored against the Physical Layer beats. The odds rows are "
            f"prediction-market implied probabilities, the closest thing to "
            f"tomorrow's consensus you can read today.</div>"
            f"{rows}{odds_rows}</section>")


def scanner_html(tools_tickers, quotes, pages, conv_deltas=None):
    """Server-rendered coverage scanner. One row per name the machine has
    real data on; filters and sorting are client-side over these rows."""
    covered = {t: d for t, d in tools_tickers.items() if d}
    if not covered:
        return ""
    rows = []
    order = sorted(covered,
                   key=lambda t: -abs((quotes.get(t) or {}).get("changePct") or 0))
    layers = sorted({d["layer"] for d in covered.values() if d.get("layer")})
    for t in order:
        d = covered[t]
        q = quotes.get(t) or {}
        ch = q.get("changePct")
        name = (f"<a class='tk' href='t/{escape(t)}.html'>{escape(t)}</a>"
                if t in pages else f"<span class='tk'>{escape(t)}</span>")
        held = f"{d['held']:.1f}%" if d.get("held") is not None else ""
        health = (f"<span class='badge {d['health']}'>{d['health']}</span>"
                  if d.get("health") else "")
        conv = ""
        if d.get("conviction") is not None:
            conv = f"{int(d['conviction'])} {escape(d.get('stance') or '')}".strip()
            delta = (conv_deltas or {}).get(t)
            if delta:
                dc = "up" if delta > 0 else "down"
                conv += f" <span class='{dc}'>{delta:+d} 7d</span>"
        price = f"${q['price']:,.2f}" if q.get("price") is not None else "-"
        rows.append(
            f"<tr data-layer=\"{escape(d.get('layer') or '')}\" "
            f"data-held=\"{1 if d.get('held') is not None else 0}\" "
            f"data-day=\"{ch if ch is not None else ''}\" "
            f"data-conv=\"{d.get('conviction') if d.get('conviction') is not None else ''}\">"
            f"<td>{name}</td>"
            f"<td style='font-size:12px'>{escape(d.get('layer') or '')}</td>"
            f"<td>{price}</td>"
            f"<td class='{_cls(ch)}'>{_pct(ch)}</td>"
            f"<td>{held}</td><td>{health}</td>"
            f"<td style='font-size:12px'>{conv}</td>"
            f"<td style='font-size:12px'>{escape(d.get('earnings') or '')}</td></tr>")
    chips = "".join(
        f"<button class='scan-chip' data-filter-layer=\"{escape(l)}\">{escape(l)}</button>"
        for l in layers)
    return f"""<section id="scanner">
<h2>The Scanner <span class="chip" style="border-color:var(--gold);color:var(--gold)">Pro, free until July 22</span></h2>
<div class="sub" style="margin-bottom:10px">Every name the machine has real coverage on:
layer and thesis from my research files, health from my entries, conviction from the
machine desk, earnings dates from the calendar it tracks. Blank means no data, not
no opinion worth guessing at.</div>
<div class="scan-bar">
  <button class="scan-chip active" data-filter-layer="*">All</button>
  <button class="scan-chip" data-filter-held="1">In my book</button>
  {chips}
  <span style="flex:1"></span>
  <button class="scan-chip" data-sort="day">Sort: day move</button>
  <button class="scan-chip" data-sort="conv">Sort: conviction</button>
</div>
<div style="overflow-x:auto">
<table id="scan-table"><thead><tr>
<th>Ticker</th><th>Layer</th><th>Price</th><th>Today</th><th>My weight</th>
<th>Health</th><th>Machine</th><th>Earnings</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table>
</div>
</section>"""


def request_line_html():
    """Members-only pointer to the Request Line. Requests really do feed the
    agent queue: Quinn dispatches research missions from them."""
    chat = "https://youngbullinvests.substack.com/chat"
    return (f"<section id='request-line'><h2>The Request Line</h2>"
            f"<div class='sub' style='margin-bottom:10px'>Want a name run through "
            f"the machine? Drop a ticker or a question in the subscriber chat, or "
            f"reply to any post. Member requests feed my agent queue directly: I "
            f"dispatch research missions from them, and the answers come back as "
            f"Request Line posts and research pages here.</div>"
            f"<a class='cta-btn' href='{chat}' target='_blank' "
            f"rel='noopener'>Drop a request in the chat</a></section>")


def _cal_row(e, pages):
    tick = ""
    if e["t"]:
        tick = (f"<a class='tk' href='t/{escape(e['t'])}.html'>{escape(e['t'])}</a>"
                if e["t"] in pages else f"<span class='tk'>{escape(e['t'])}</span>")
    why = (f"<div class='cal-why'>{escape(e['why'])}</div>" if e["why"] else "")
    receipt = ""
    if e["receipt"]:
        receipt = (f" <a class='cal-receipt' href='{escape(e['receipt'])}' "
                   f"rel='noopener'>receipt</a>")
    return (f"<div class='cal-item'><span class='cal-date'>{escape(e['date'][5:])}"
            f"</span><span class='cal-body'>{tick} "
            f"<span>{escape(e['what'])}</span>{receipt}{why}</span></div>")


def calendar_public_html(entries):
    """Next 7 days, compact, with the members tease. Empty week says so."""
    inner = ("".join(_cal_row(e, frozenset()) for e in entries)
             or "<div class='viz-note'>no dated catalysts in the next 7 days</div>")
    return f"""<section id="calendar">
<h2>Catalyst Calendar, Next 7 Days</h2>
<div class="sub" style="margin-bottom:10px">Every dated event the desk actually has a
source for. Earnings from the machine's calendar, the rest hand-verified. Members see
the full quarter. <a href="pricing.html">How to get in</a>.</div>
{inner}
</section>"""


def calendar_members_html(entries, pages):
    """The full quarter, grouped by date, receipts linked."""
    if not entries:
        return ""
    groups, order = {}, []
    for e in entries:
        if e["date"] not in groups:
            order.append(e["date"])
        groups.setdefault(e["date"], []).append(e)
    blocks = []
    for d in order:
        rows = "".join(_cal_row(e, pages) for e in groups[d])
        blocks.append(f"<div class='cal-day'><div class='cal-dayhead'>{escape(d)}"
                      f"</div>{rows}</div>")
    return f"""<section id="calendar-full">
<h2>Catalyst Calendar, The Quarter <span class="chip" style="border-color:var(--gold);color:var(--gold)">Members</span></h2>
<div class="sub" style="margin-bottom:10px">Every dated event across the coverage
universe with a real source behind it: earnings from the machine's calendar table,
everything else verified by hand before it lands here. No date is ever guessed. If a
name you care about is missing a date, it is because nobody has announced one.</div>
{''.join(blocks)}
</section>"""


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
