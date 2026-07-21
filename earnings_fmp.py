"""FMP earnings-calendar feed: fills coverage-universe earnings dates the
in-house Supabase table does not have yet.

Key lives in ~/.young-bull/secrets.env as FMP_API_KEY. No key means no
feed, printed once per refresh, never a guess. The Supabase table always
outranks FMP on the same ticker (it is validated in-house). Any network
or vendor failure degrades to {} so the refresh can never break on FMP.
"""

import json
import urllib.request
from datetime import date, timedelta

from thesis import SECRETS, TIMEOUT, parse_env

FMP_URL = ("https://financialmodelingprep.com/stable/earnings-calendar"
           "?from={start}&to={end}&apikey={key}")
FETCH_DAYS = 92  # the members quarter is the widest window rendered


def fmp_key_from_env(text):
    """FMP_API_KEY from a dotenv blob, '' when absent."""
    return parse_env(text).get("FMP_API_KEY", "")


def parse_fmp_calendar(payload, universe, today):
    """Vendor rows -> earliest strictly-future date per covered ticker.

    Only tickers in the coverage universe survive; malformed, past, or
    symbol-less rows are dropped, never repaired.
    """
    if not isinstance(payload, list):
        return {}
    out = {}
    for r in payload:
        if not isinstance(r, dict):
            continue
        t = str(r.get("symbol") or "").upper()
        d = r.get("date")
        if not t or t not in universe:
            continue
        try:
            date.fromisoformat(d)
        except (TypeError, ValueError):
            continue
        if d < today:
            continue
        if t not in out or d < out[t]["date"]:
            out[t] = {"date": d, "label": "earnings"}
    return out


def merge_earnings(supabase, fmp):
    """Supabase rows win on a shared ticker; FMP fills the gaps."""
    return {**fmp, **supabase}


def fetch_fmp_earnings(universe, today):
    """Pull the next quarter of earnings dates. Any failure -> {}."""
    try:
        key = fmp_key_from_env(SECRETS.read_text(encoding="utf-8"))
    except OSError:
        key = ""
    if not key:
        print("NOTE: no FMP_API_KEY in secrets.env, earnings stay "
              "Supabase-only this refresh")
        return {}
    try:
        end = (date.fromisoformat(today) + timedelta(days=FETCH_DAYS)).isoformat()
        url = FMP_URL.format(start=today, end=end, key=key)
        req = urllib.request.Request(url, headers={"User-Agent": "yb-terminal"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            payload = json.loads(r.read().decode("utf-8"))
        return parse_fmp_calendar(payload, universe, today)
    except Exception as e:
        print(f"WARN: FMP earnings fetch failed, calendar goes without it: {e}")
        return {}
