"""Earnings Calendar — upcoming report dates and recent results for every stock on the dashboard.

Source: Yahoo Finance (batch quote for dates, quoteSummary for estimates and last results).
Writes earnings.json. Usage: python3 earnings.py
"""
import json, os, sys, datetime, urllib.parse, concurrent.futures as cf
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
sys.argv = sys.argv[:1]
import scan   # reuses the Yahoo session (cookie + crumb) and retrying HTTP helper

AHEAD_DAYS = 45      # upcoming window
DETAIL_DAYS = 21     # fetch estimates for reports in the next 21 days
RECENT_DAYS = 14     # show results from the last 14 days
TZ = {"US": ZoneInfo("America/New_York"), "IN": ZoneInfo("Asia/Kolkata")}

def universe():
    cfg = json.load(open("config.json")); out = {}
    raw = {}
    if os.path.exists("raw.txt"):
        for ln in open("raw.txt"):
            p = ln.split("|")
            if len(p) > 2 and not p[0].startswith("#"): raw[p[0]] = (p[1], p[2])
    for k in cfg["india"]["stocks"]:
        sym, name = raw.get(k, (k, k))
        ys = sym[:-2] + ".BO" if sym.endswith("@B") else k + ".NS"
        out[ys] = dict(t=k, region="IN", name=name, group="")
    grp = {}
    for g in cfg["global"].get("usgroups", []):
        for t in g["tickers"]: grp[t] = g["g"]
    for k, ys, name in cfg["global"]["yahoo"]:
        if ys.startswith("^") or "=" in ys: continue
        out.setdefault(ys, dict(t=k, region="US", name=name, group=grp.get(k, "")))
    return out

def yget(url):
    cr = scan.yahoo_session()
    st, body = scan.get(url + ("&" if "?" in url else "?") + "crumb=" + urllib.parse.quote(cr or ""))
    return json.loads(body) if st == 200 and body else None

def raw(v):
    return v.get("raw") if isinstance(v, dict) else v

def main():
    U = universe(); syms = list(U)
    now = datetime.datetime.now(datetime.timezone.utc); nts = now.timestamp()
    quotes = {}
    for i in range(0, len(syms), 50):
        b = syms[i:i + 50]
        try:
            j = yget("https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + urllib.parse.quote(",".join(b)))
            for q in (j or {}).get("quoteResponse", {}).get("result", []): quotes[q["symbol"]] = q
        except Exception as e:
            print("quote batch failed:", e)
    up, recent, need = [], [], []
    for ys, q in quotes.items():
        if q.get("quoteType") != "EQUITY": continue
        u = U[ys]
        region = "IN" if ys.endswith((".NS", ".BO")) else ("US" if "." not in ys else "INTL")
        tz = TZ["IN"] if region == "IN" else TZ["US"] if region == "US" else datetime.timezone.utc
        nxt = q.get("earningsTimestampStart") or q.get("earningsTimestamp")
        if q.get("earningsTimestamp") and q["earningsTimestamp"] > nts - 3600 * 12: nxt = q["earningsTimestamp"]
        last = q.get("earningsTimestamp") if q.get("earningsTimestamp") and q["earningsTimestamp"] <= nts else None
        base = dict(t=u["t"], ys=ys, name=q.get("longName") or q.get("shortName") or u["name"], region=region,
                    group=u["group"], cur=q.get("financialCurrency") or q.get("currency"), mcap=q.get("marketCap"))
        if nxt and nts - 3600 * 12 <= nxt <= nts + AHEAD_DAYS * 86400:
            d = datetime.datetime.fromtimestamp(nxt, tz)
            when = ""
            if region == "US":
                h = d.hour + d.minute / 60
                when = "BMO" if h < 9.5 else ("AMC" if h >= 16 else "DMH")
            e = dict(base, ts=int(nxt), d=d.strftime("%Y-%m-%d"), est=bool(q.get("isEarningsDateEstimate")), when=when)
            up.append(e)
            if nxt <= nts + DETAIL_DAYS * 86400: need.append(("up", e))
        if last and last >= nts - RECENT_DAYS * 86400:
            d = datetime.datetime.fromtimestamp(last, tz)
            r = dict(base, ts=int(last), d=d.strftime("%Y-%m-%d")); recent.append(r); need.append(("rec", r))

    def detail(item):
        kind, e = item
        try:
            j = yget(f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{urllib.parse.quote(e['ys'])}?modules=calendarEvents,earningsHistory")
            res = (j or {}).get("quoteSummary", {}).get("result") or [{}]
            r0 = res[0]
            ce = (r0.get("calendarEvents") or {}).get("earnings") or {}
            if kind == "up":
                e["epsEst"] = raw(ce.get("earningsAverage")); e["epsLo"] = raw(ce.get("earningsLow")); e["epsHi"] = raw(ce.get("earningsHigh"))
                e["revEst"] = raw(ce.get("revenueAverage"))
            hist = (r0.get("earningsHistory") or {}).get("history") or []
            if hist:
                h = hist[-1]
                tgt = e if kind == "rec" else e.setdefault("prev", {})
                tgt["epsAct"] = raw(h.get("epsActual")); tgt["epsEst2"] = raw(h.get("epsEstimate"))
                sp = raw(h.get("surprisePercent")); tgt["surp"] = None if sp is None else round(sp * 100, 1)
                tgt["qtr"] = (h.get("quarter") or {}).get("fmt")
        except Exception as ex:
            pass
        return e
    with cf.ThreadPoolExecutor(6) as ex:
        list(ex.map(detail, need))
    # a "recent" entry only counts once the reported quarter is actually in (avoid stale history)
    for r in recent:
        if r.get("qtr"):
            qd = datetime.date.fromisoformat(r["qtr"])
            if (datetime.date.fromisoformat(r["d"]) - qd).days > 120: r["epsAct"] = None
    up.sort(key=lambda e: (e["d"], -(e.get("mcap") or 0)))
    recent.sort(key=lambda e: (-e["ts"]))
    ist = datetime.datetime.now(TZ["IN"])
    res = dict(asof=ist.strftime("%-d %b %Y, %H:%M IST"), iso=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
               checked=len(quotes), upcoming=up, recent=recent)
    json.dump(res, open("earnings.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"earnings.json: {len(up)} upcoming reports (next {AHEAD_DAYS} days), {len(recent)} recent results, {len(quotes)} stocks checked")

if __name__ == "__main__":
    main()
