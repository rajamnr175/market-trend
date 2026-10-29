"""Bull vs bear — distance from the all-time high for every stock, index, commodity and coin on the Global list.

Stocks, indices and commodities: Yahoo Finance monthly bars over the full history (range=max), split-adjusted intraday highs.
Crypto: weekly bars from Binance (OKX / Bitget / Gate fallback), Yahoo <coin>-USD when that has a longer history.
Writes drawdown.json. Usage: python3 drawdown.py
"""
import json, os, sys, datetime, concurrent.futures as cf
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
sys.argv = sys.argv[:1]
import scan   # Yahoo session (cookie + crumb), retrying HTTP and crypto exchange helpers

SKIP = {"US2Y", "US13W", "US10Y", "US5Y", "US30Y", "VIX", "USDINR", "USDEUR", "EURINR", "EURUSD", "USDJPY", "DXY"}

def ath_of(rows):
    """rows: [ts_ms, o, h, l, c, v] -> (ath, ath_ts_ms)"""
    best = None
    for r in rows:
        h = r[2] if r[2] is not None else r[4]
        if h is not None and h > 0 and (best is None or h > best[0]): best = (h, r[0])
    return best

def low_since(rows, ms):
    L = [r[3] if r[3] is not None else r[4] for r in rows if r[0] >= ms]
    L = [x for x in L if x and x > 0]
    return min(L) if L else None

def y_item(it):
    k, sym, nm = it
    if k in SKIP or sym.endswith("=X"): return None
    try:
        m = scan.yahoo(sym, "max", "1mo")
        if not m or len(m["rows"]) < 3: return None
        meta = m["meta"]; rows = m["rows"]
        px = meta.get("regularMarketPrice") or rows[-1][4]
        a = ath_of(rows)
        hi52, lo52 = meta.get("fiftyTwoWeekHigh"), meta.get("fiftyTwoWeekLow")
        if px and a and px > a[0]: a = (px, rows[-1][0])
        return dict(t=k, ys=sym, px=px, ath=a[0], athTs=a[1], first=rows[0][0], hi52=hi52, lo52=lo52, src="Yahoo")
    except Exception as e:
        print("yahoo failed", k, e); return None

def c_item(it, ycrypto):
    k, src, nm = it; kind, sym = src.split(":")
    rows = []
    try:
        if kind in ("bn", "bnp"):
            rows = scan.binance(sym if kind == "bnp" else sym + "USDT", "w")
        if len(rows) < 30 and kind != "bnp": rows = scan.alt_crypto(sym, "w")
    except Exception:
        rows = []
    srcname = "Binance" if kind in ("bn", "bnp") and rows else "OKX/Bitget/Gate"
    if kind == "bnp": return None            # ratio pairs (e.g. ETH/BTC) have no all-time high in dollars
    if k in ycrypto:                          # Yahoo often has the longer history (pre-Binance listing)
        try:
            y = scan.yahoo(ycrypto[k], "max", "1wk")
            if y and y["rows"] and (not rows or y["rows"][0][0] < rows[0][0] - 86400e3 * 60): rows, srcname = y["rows"], "Yahoo"
        except Exception:
            pass
    if len(rows) < 8: return None
    a = ath_of(rows); px = rows[-1][4]
    now = rows[-1][0]
    return dict(t=k, ys=sym, px=px, ath=a[0], athTs=a[1], first=rows[0][0], hi52=max(r[2] for r in rows if r[0] >= now - 365 * 864e5),
                lo52=low_since(rows, now - 365 * 864e5), src=srcname)

def main():
    cfg = json.load(open("config.json"))["global"]
    out = []
    with cf.ThreadPoolExecutor(6) as ex:
        for r in ex.map(y_item, cfg["yahoo"]):
            if r: out.append(r)
    yc = cfg.get("ycrypto", {})
    with cf.ThreadPoolExecutor(5) as ex:
        for r in ex.map(lambda it: c_item(it, yc), cfg["crypto"]):
            if r: out.append(r)
    # market cap and type (Yahoo batch quote) so the page can focus on large companies and coins
    qs = {}
    coins = {c[0] for c in cfg["crypto"]}
    syms = [r["t"] + "-USD" if r["t"] in coins else r["ys"] for r in out]
    for r, s_ in zip(out, syms): r["_q"] = s_
    import urllib.parse
    cr = scan.yahoo_session()
    for i in range(0, len(syms), 50):
        b = syms[i:i + 50]
        try:
            st, body = scan.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + urllib.parse.quote(",".join(b)) + "&crumb=" + urllib.parse.quote(cr or ""))
            for q in (json.loads(body) if st == 200 else {}).get("quoteResponse", {}).get("result", []): qs[q["symbol"]] = q
        except Exception as e:
            print("quote batch failed:", e)
    for r in out:
        q = qs.get(r.pop("_q")) or {}
        r["qt"] = q.get("quoteType"); r["mcap"] = q.get("marketCap")
        if r["mcap"]: r["mcap"] = float(f"{r['mcap']:.3g}")
    for r in out:
        r["dd"] = round((r["px"] / r["ath"] - 1) * 100, 1)
        r["athD"] = datetime.datetime.fromtimestamp(r["athTs"] / 1000, datetime.timezone.utc).strftime("%Y-%m")
        r["fromLo"] = round((r["px"] / r["lo52"] - 1) * 100, 1) if r.get("lo52") else None
        r["first"] = datetime.datetime.fromtimestamp(r["first"] / 1000, datetime.timezone.utc).strftime("%Y-%m")
        for f in ("px", "ath", "hi52", "lo52"):
            if r.get(f) is not None: r[f] = float(f"{r[f]:.6g}")
        del r["athTs"]
    now = datetime.datetime.now(datetime.timezone.utc); ist = now.astimezone(ZoneInfo("Asia/Kolkata"))
    res = dict(asof=ist.strftime("%-d %b %Y, %H:%M IST"), iso=now.strftime("%Y-%m-%dT%H:%M:%SZ"), items=sorted(out, key=lambda r: r["dd"]))
    json.dump(res, open("drawdown.json", "w"), ensure_ascii=False, separators=(",", ":"))
    n20 = sum(1 for r in out if r["dd"] <= -20)
    print(f"drawdown.json: {len(out)} tickers, {n20} at least 20% below their all-time high")

if __name__ == "__main__":
    main()
