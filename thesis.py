"""Living thesis cards: health rules, machine conviction, receipts, catalysts.

Health badge is deterministic price-vs-anchor math, no model in the loop:
  gain on cost >= -15%  -> INTACT     (normal volatility, anchor holds)
  -30% <= gain < -15%   -> STRESSED   (thesis under real pressure)
  gain < -30%           -> BROKEN     (the market is saying the call was wrong)
Missing data renders blank. Blank beats fake.

Committee conviction comes from Supabase committee_thesis_live and is only
trusted when updated_at is within FRESH_HOURS (the scorer has gone cold
before; a stale number shown as live is fabrication).
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SECRETS = Path.home() / ".young-bull/secrets.env"
FRESH_HOURS = 48
TIMEOUT = 15


def de_dash(text):
    """House rule: no em dashes on any public surface, ever."""
    for dash in (" — ", "—", " – ", "–"):
        text = text.replace(dash, ", ")
    return text


def health_badge(price, cost):
    if price is None or not cost:
        return ""
    gain = (price - cost) / cost * 100
    if gain >= -15:
        return "INTACT"
    if gain >= -30:
        return "STRESSED"
    return "BROKEN"


def parse_env(text):
    env = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip().isidentifier():
            env[key.strip()] = value.strip()
    return env


def fresh_committee(rows, now=None):
    """Keep only rows updated within FRESH_HOURS with a real conviction."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=FRESH_HOURS)
    out = {}
    for r in rows:
        ts, conviction = r.get("updated_at"), r.get("aggregated_conviction")
        if not ts or conviction is None:
            continue
        try:
            when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when < cutoff:
            continue
        out[r["ticker"]] = {"conviction": conviction,
                            "stance": r.get("current_stance") or ""}
    return out


def fetch_committee(tickers):
    """Pull live committee conviction. Any failure degrades to {}."""
    try:
        env = parse_env(SECRETS.read_text(encoding="utf-8"))
        base, key = env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"]
        params = urllib.parse.quote(f"in.({','.join(tickers)})", safe="in.(),")
        url = (f"{base}/rest/v1/committee_thesis_live"
               f"?select=ticker,aggregated_conviction,current_stance,updated_at"
               f"&ticker={params}")
        req = urllib.request.Request(
            url, headers={"apikey": key, "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return fresh_committee(json.loads(r.read().decode("utf-8")))
    except Exception as e:
        print(f"WARN: committee fetch failed, cards go without conviction: {e}")
        return {}


def nearest_catalysts(rows, today):
    """Earliest strictly-future report_date per ticker -> catalyst dict."""
    out = {}
    for r in rows:
        t, d = r.get("ticker"), r.get("report_date")
        if not t or not d or d < today:
            continue
        if t not in out or d < out[t]["date"]:
            out[t] = {"date": d, "label": "earnings"}
    return out


def fetch_catalysts(today):
    """Pull upcoming earnings dates. Any failure degrades to {}."""
    try:
        env = parse_env(SECRETS.read_text(encoding="utf-8"))
        base, key = env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"]
        url = (f"{base}/rest/v1/earnings_calendar?select=ticker,report_date"
               f"&report_date=gte.{today}&order=report_date.asc&limit=200")
        req = urllib.request.Request(
            url, headers={"apikey": key, "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return nearest_catalysts(json.loads(r.read().decode("utf-8")), today)
    except Exception as e:
        print(f"WARN: catalyst fetch failed, cards go without dates: {e}")
        return {}


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def build_cards(rows, meta_by_ticker, committee, receipts, catalysts):
    """One card per held row, heaviest weight first. Missing pieces stay blank."""
    cards = []
    for r in sorted(rows, key=lambda x: -(x["weight"] or 0)):
        t = r["t"]
        meta = meta_by_ticker.get(t) or {}
        com = committee.get(t) or {}
        cards.append({
            "t": t,
            "price": r.get("price"),
            "change": r.get("change"),
            "gain": r.get("gain"),
            "weight": r.get("weight"),
            "thesis_short": str(meta.get("thesis_short") or ""),
            "layer": str(meta.get("layer") or ""),
            "sleeve": str(meta.get("sleeve") or ""),
            "health": health_badge(r.get("price"), r.get("cost")),
            "conviction": com.get("conviction"),
            "stance": com.get("stance", ""),
            "receipt": receipts.get(t),
            "catalyst": catalysts.get(t),
        })
    return cards
