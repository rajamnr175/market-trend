"""Market Trend scan — fetch, compute, classify, render.
Usage:  python3 scan.py            (full run: India + Global, writes out/scan_visual.html)
        python3 scan.py --check    (connectivity check only)
Needs network access to: query1/query2.finance.yahoo.com, www.niftyindices.com, api.binance.com, api.bybit.com, api.coingecko.com
"""
import json, os, sys, time, math, datetime, subprocess, concurrent.futures as cf
import urllib.request, urllib.parse, http.cookiejar, threading
from metrics import line, sma

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36", "Accept": "*/*"}
CFG = json.load(open("config.json"))
LOG = []
def log(*a): s = " ".join(str(x) for x in a); LOG.append(s); print(s, flush=True)

CJ = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CJ))
CRUMB = {"v": None}; _clock = threading.Lock()
def get(url, data=None, headers=None, timeout=25, tries=4):
    last = None
    for a in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
            with OPENER.open(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 400): return e.code, ""
            last = e; time.sleep((6 if e.code == 429 else 1.5) * (a + 1))
        except Exception as e:
            last = e; time.sleep(1.2 * (a + 1))
    raise RuntimeError(f"{url[:90]} -> {last}")

# ---------------- sources ----------------
def yahoo_session():
    with _clock:
        if CRUMB["v"]: return CRUMB["v"]
        try: OPENER.open(urllib.request.Request("https://fc.yahoo.com/", headers=UA), timeout=15)
        except Exception: pass
        st, c = get("https://query1.finance.yahoo.com/v1/test/getcrumb", tries=3)
        CRUMB["v"] = c.strip() if st == 200 and c and "<" not in c else ""
        return CRUMB["v"]

def yahoo(sym, rng, iv):
    cr = yahoo_session()
    for host in ("query1", "query2"):
        try:
            st, body = get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range={rng}&interval={iv}" + (f"&crumb={urllib.parse.quote(cr)}" if cr else ""))
        except Exception:
            continue
        if st == 404 or not body: return None
        j = json.loads(body); res = (j.get("chart", {}).get("result") or [None])[0]
        if not res or not res.get("timestamp"): return None
        q = res["indicators"]["quote"][0]; rows = []
        for i, ts in enumerate(res["timestamp"]):
            cl = q["close"][i]
            if cl is None: continue
            rows.append([ts * 1000, q["open"][i] if q["open"][i] is not None else cl, q["high"][i] if q["high"][i] is not None else cl,
                         q["low"][i] if q["low"][i] is not None else cl, cl, q["volume"][i] or 0])
        return {"rows": rows, "name": res["meta"].get("longName") or res["meta"].get("shortName"), "meta": res["meta"]}
    return None

def binance(sym, iv):
    st, body = get(f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={'1d' if iv=='d' else '1w'}&limit=1000")
    if st != 200 or not body.startswith("["):
        st, body = get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={'1d' if iv=='d' else '1w'}&limit=1000")
    return [[k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[7])] for k in json.loads(body)]

def okx(base, iv):
    out = {}; after = ""
    for _ in range(8):
        st, b = get(f"https://www.okx.com/api/v5/market/history-candles?instId={base}-USDT&bar={'1Dutc' if iv=='d' else '1Wutc'}&limit=100" + (f"&after={after}" if after else ""))
        L = (json.loads(b).get("data") or []) if st == 200 and b else []
        if not L: break
        for k in L: out[int(k[0])] = [int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[7] if len(k) > 7 else k[5])]
        after = L[-1][0]
        if len(L) < 100: break
    return [out[k] for k in sorted(out)]

def bitget(base, iv):
    st, b = get(f"https://api.bitget.com/api/v2/spot/market/candles?symbol={base}USDT&granularity={'1day' if iv=='d' else '1week'}&limit=1000")
    L = (json.loads(b).get("data") or []) if st == 200 and b else []
    return [[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[6])] for k in L]

def gate(base, iv):
    st, b = get(f"https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair={base}_USDT&interval={'1d' if iv=='d' else '7d'}&limit=1000")
    L = json.loads(b) if st == 200 and b.startswith("[") else []
    r = [[int(k[0]) * 1000, float(k[5]), float(k[3]), float(k[4]), float(k[2]), float(k[1])] for k in L]
    while r and r[-1][5] == 0 and r[-1][2] == r[-1][3]: r.pop()   # drop empty placeholder candle
    return r

def alt_crypto(base, iv):
    best = []
    for fn in (okx, bitget, gate):
        try: r = fn(base, iv)
        except Exception: r = []
        if len(r) > len(best): best = r
        if len(best) >= 400: break
    return best

def bybit(sym, cat, iv):
    st, body = get(f"https://api.bybit.com/v5/market/kline?category={cat}&symbol={sym}&interval={'D' if iv=='d' else 'W'}&limit=1000")
    L = (json.loads(body).get("result") or {}).get("list") or []
    return [[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[6])] for k in reversed(L)]

def nifty_index(name, start, end):
    cinfo = json.dumps({"name": name, "startDate": start, "endDate": end, "indexName": name}).replace('"', "'")
    st, body = get("https://www.niftyindices.com/BackPage/getHistoricaldatatabletoString", data=json.dumps({"cinfo": cinfo}).encode(),
                   headers={"Content-Type": "application/json; charset=utf-8", "Origin": "https://www.niftyindices.com", "Referer": "https://www.niftyindices.com/reports/historical-data", "X-Requested-With": "XMLHttpRequest"})
    try: return json.loads(body)
    except Exception: return []

def check():
    cr = yahoo_session()
    tests = {"yahoo": "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?range=5d&interval=1d&crumb=" + urllib.parse.quote(cr or ""), "niftyindices": "https://www.niftyindices.com/",
             "binance": "https://data-api.binance.vision/api/v3/ping", "okx": "https://www.okx.com/api/v5/public/time", "bybit": "https://api.bybit.com/v5/market/time", "coingecko": "https://api.coingecko.com/api/v3/ping"}
    ok = {}
    for k, u in tests.items():
        try: st, _ = get(u, tries=1, timeout=12); ok[k] = st
        except Exception as e: ok[k] = f"blocked ({str(e)[-60:]})"
    return ok

def prev_lines(path):
    try: return {l.split("|")[0]: l.rstrip("\n") for l in open(path) if l.strip()}
    except FileNotFoundError: return {}

# ---------------- India ----------------
def scan_india():
    P = [5, 21, 63, 126, 250]; raw = []; lt = []; miss = []; meta = {}
    jobs = [(t, [t + ".NS", t + ".BO"], False) for t in CFG["india"]["stocks"]] + [("#" + k, [v], True) for k, v in CFG["india"]["bench"].items()]
    def one(job):
        key, tries, isb = job
        for s in tries:
            d = yahoo(s, "2y", "1d")
            if d and len(d["rows"]) >= 20:
                w = yahoo(s, "10y", "1wk") or {"rows": []}
                return key, s, d, w
        return key, None, None, None
    with cf.ThreadPoolExecutor(6) as ex:
        for key, s, d, w in ex.map(one, jobs):
            if not d: miss.append(key); continue
            if key == "#NIFTY": meta["t"] = d["meta"].get("regularMarketTime")
            if len(d["rows"]) < 30: miss.append(key + "(short)"); continue
            symtag = (s[:-3] if s.endswith(".NS") else s) if key.startswith("#") else (s[:-3] if s.endswith(".NS") else s[:-3] + "@B")
            L = line(key, symtag, d["name"], d["rows"], w["rows"], P).split("|")
            raw.append("|".join(L[:30]))
            if not key.startswith("#"): lt.append("|".join([key] + L[30:36]))
    PR, PL = prev_lines("raw.txt"), prev_lines("lt.txt"); stale = []
    for k in miss:
        k0 = k.replace("(short)", "")
        if k0 in PR:
            raw.append(PR[k0]); stale.append(k0)
            if k0 in PL: lt.append(PL[k0])
    open("raw.txt", "w").write("\n".join(raw) + "\n"); open("lt.txt", "w").write("\n".join(lt) + "\n")
    log(f"India: {len(raw)} series, missing {miss}, kept previous data for {stale}")
    return meta, miss

def scan_indices():
    now = datetime.datetime.now(IST); out = []; miss = []
    chunks = []
    s = now - datetime.timedelta(days=5 * 366 + 5)
    while s < now:
        e = min(s + datetime.timedelta(days=364), now)
        chunks.append((s.strftime("%d-%b-%Y"), e.strftime("%d-%b-%Y"))); s = e + datetime.timedelta(days=1)
    M = {m: i for i, m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}
    def one(name):
        rows = []
        for a, b in chunks:
            for o in nifty_index(name, a, b):
                try:
                    d, m, y = o["HistoricalDate"].split(" ")
                    ts = datetime.datetime(int(y), M[m[:3]] + 1, int(d)).timestamp() * 1000
                    rows.append((ts, float(str(o["CLOSE"]).replace(",", ""))))
                except Exception: pass
        rows = sorted(set(rows)); return name, rows
    with cf.ThreadPoolExecutor(4) as ex:
        res = list(ex.map(one, CFG["india"]["indices"]))
    for name, rows in res:
        if len(rows) < 200: miss.append(name); continue
        lt_, last = rows[-1]
        def at(days):
            t = lt_ - days * 864e5; v = None
            for ts, c in rows:
                if ts <= t: v = c
                else: break
            return v
        def atY(y):
            d = datetime.datetime.fromtimestamp(lt_ / 1000); t = d.replace(year=d.year - y).timestamp() * 1000; v = None
            for ts, c in rows:
                if ts <= t: v = c
                else: break
            return v
        R = lambda b: f"{(last / b - 1) * 100:.1f}" if b else ""
        c5, c3, c1 = atY(5), atY(3), atY(1)
        mon = []; cur = None
        for ts, c in rows:
            dd = datetime.datetime.fromtimestamp(ts / 1000); k = dd.year * 12 + dd.month
            if k != cur: mon.append(c); cur = k
            else: mon[-1] = c
        base = c5 or rows[0][1]; ser = ",".join(str(round(v / base * 100)) for v in mon)
        cl = [c for _, c in rows]; s200 = sum(cl[-200:]) / 200; hi = max(cl[-250:])
        out.append("|".join([name, f"{last}", R(at(30)), R(at(91)), R(at(182)), R(c1), R(c3), R(c5),
                             f"{(math.pow(last / c3, 1/3) - 1) * 100:.1f}" if c3 else "", f"{(math.pow(last / c5, 1/5) - 1) * 100:.1f}" if c5 else "",
                             f"{(last / s200 - 1) * 100:.1f}", f"{(last / hi - 1) * 100:.1f}", ser]))
    if len(out) >= 10:
        open("idx.txt", "w").write("\n".join(out) + "\n")
    else:
        log("Sector indices: too few fetched — keeping the previous idx.txt")
    log(f"Sector indices: {len(out)} ok, missing {miss}")
    return miss

# ---------------- Global ----------------
def scan_global(crypto_only=False):
    out = []; miss = []
    def y_one(it):
        k, s, nm = it
        d = yahoo(s, "2y", "1d"); w = yahoo(s, "10y", "1wk") or {"rows": []}
        if not d or len(d["rows"]) < 30: return k, None
        return k, line(k, s, nm or d["name"], d["rows"], w["rows"], [5, 21, 63, 126, 250])
    def c_one(it):
        k, src, nm = it; kind, sym = src.split(":")
        try:
            if kind in ("bn", "bnp"):
                pair = sym if kind == "bnp" else sym + "USDT"; d = binance(pair, "d"); w = binance(pair, "w")
            else:
                cat = "spot" if kind == "bs" else "linear"
                try: d = bybit(sym + "USDT", cat, "d"); w = bybit(sym + "USDT", cat, "w")
                except Exception: d = w = []
                if len(d) < 30: d = alt_crypto(sym, "d"); w = alt_crypto(sym, "w")
        except Exception as e:
            d = w = []
        if len(d) < 30 and CFG["global"].get("ycrypto", {}).get(k):
            yd = yahoo(CFG["global"]["ycrypto"][k], "2y", "1d"); yw = yahoo(CFG["global"]["ycrypto"][k], "10y", "1wk")
            if yd: d = yd["rows"]; w = (yw or {"rows": []})["rows"]
        if len(d) < 30: return k, None
        return k, line(k, src, nm, d, w, [7, 30, 91, 182, 365])
    PG = prev_lines("graw.txt")
    if crypto_only:   # keep the stock/index/FX/yield lines from the last full scan
        ck = {k for k, _, _ in CFG["global"]["crypto"]}
        out += [PG[k] for k, _, _ in CFG["global"]["yahoo"] if k in PG and k not in ck]
    else:
        with cf.ThreadPoolExecutor(6) as ex:
            for k, L in ex.map(y_one, CFG["global"]["yahoo"]):
                (out.append(L) if L else miss.append(k))
    with cf.ThreadPoolExecutor(5) as ex:
        for k, L in ex.map(c_one, CFG["global"]["crypto"]):
            (out.append(L) if L else miss.append(k))
    stale = [k for k in miss if k in PG]; out += [PG[k] for k in stale]
    # tidy fields the old scan blanked: yields' 5Y % on tiny bases
    fixed = []
    for L in out:
        p = L.split("|")
        if p[0] in ("US2Y", "US13W"): p[32] = ""; p[34] = ""
        fixed.append("|".join(p))
    open("graw.txt", "w").write("\n".join(fixed) + "\n")
    log(f"Global: {len(out)} series, missing {miss}, kept previous data for {stale}")
    # crypto market structure
    try:
        st, b = get("https://api.coingecko.com/api/v3/global"); g = json.loads(b)["data"]
        st, b = get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1")
        top = sum(x["market_cap"] for x in json.loads(b))
        tot = g["total_market_cap"]["usd"]; pct = g["market_cap_percentage"]
        btc, eth, usdt, usdc = pct.get("btc", 0), pct.get("eth", 0), pct.get("usdt", 0), pct.get("usdc", 0)
        cs = dict(total=tot, chg24=g.get("market_cap_change_percentage_24h_usd", 0), btcd=btc, ethd=eth, usdtd=usdt, stabled=usdt + usdc,
                  total2=tot * (1 - btc / 100), total3=tot * (1 - (btc + eth) / 100), others=max(0, tot - top),
                  asof=datetime.datetime.now(IST).strftime("%-d %b %Y, %H:%M IST"))
        json.dump(cs, open("cs.json", "w"))
    except Exception as e:
        log("CoinGecko failed, keeping previous crypto snapshot:", e)
    return miss

# ---------------- build + render ----------------
def build(india_meta, crypto_only=False):
    now = datetime.datetime.now(IST)
    if crypto_only:
        prev = json.load(open("scan_india.json")) if os.path.exists("scan_india.json") else {"label": "the last full scan"}
        note = (f"Crypto refreshed at this time from Binance (or OKX, Bitget or Gate). US stocks, indices, futures, FX and yields are from the last full scan ({prev['label']}). US economic figures are the latest official releases."
                if crypto_only == "crypto" else
                "Global refresh: US stocks, indices, futures and yields use the latest Yahoo prices (last close outside US hours); crypto is from Binance (or OKX, Bitget or Gate) at scan time. India data stays from its last scan. US economic figures are the latest official releases.")
        json.dump({"label": now.strftime("%-d %b %Y, %H:%M IST"), "iso": now.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "note": note},
                  open("scan_global.json", "w"))
        return render()
    t = india_meta.get("t")
    tl = datetime.datetime.fromtimestamp(t, IST) if t else now
    open_now = t is not None and (now - tl).total_seconds() < 1800 and (9 * 60 + 15) <= tl.hour * 60 + tl.minute < (15 * 60 + 30)
    json.dump({"label": tl.strftime("%-d %b %Y, %H:%M IST"), "iso": tl.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "note": ("NSE/BSE prices were taken during market hours." if open_now else f"NSE/BSE prices are from the last close ({tl.strftime('%-d %b')}).")
                       + " Automatic rescan by the scheduled task."}, open("scan_india.json", "w"))
    json.dump({"label": now.strftime("%-d %b %Y, %H:%M IST"), "iso": now.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "note": "US stocks, indices, futures and yields use the latest Yahoo prices (last close outside US hours). Crypto is from Binance (or OKX, Bitget or Gate where Binance doesn't list the coin) at scan time. US economic figures are the latest official releases."},
              open("scan_global.json", "w"))
    return render()

def render():
    for s in ("analyze.py", "build2.py", "gbuild.py"):
        r = subprocess.run([sys.executable, s], capture_output=True, text=True)
        if r.returncode: raise SystemExit(f"{s} failed:\n{r.stderr[-2000:]}")
        log(f"{s}: ok")
    os.makedirs("out", exist_ok=True)
    D = open("data2.json").read(); G = open("gdata.json").read()
    for tpl, out in (("template_visual.html", "out/scan_visual.html"), ("template_original.html", "out/scan.html")):
        html = open(tpl).read().replace("__DATA__", D, 1).replace("__GDATA__", G, 1)
        open(out, "w").write(html)
    log("Rendered out/scan_visual.html and out/scan.html")

if __name__ == "__main__":
    c = check(); log("connectivity:", c)
    if "--check" in sys.argv: sys.exit(0)
    blocked = [k for k, v in c.items() if not isinstance(v, int)]
    if "--crypto" in sys.argv:   # light run: crypto + CoinGecko only, stocks keep the last full scan
        if {"binance", "okx"} <= set(blocked): raise SystemExit("Binance and OKX are both blocked — cannot refresh crypto.")
        scan_global(crypto_only=True); build({}, crypto_only="crypto")
    elif "--global" in sys.argv:   # global refresh: US stocks/indices/FX/yields + crypto; India keeps its last scan
        if "yahoo" in blocked: raise SystemExit("Yahoo Finance is blocked — cannot refresh global data.")
        scan_global(); build({}, crypto_only="global")
    else:
        if "yahoo" in blocked: raise SystemExit("Yahoo Finance is blocked — cannot scan. Allow query1/query2.finance.yahoo.com.")
        meta, mi = scan_india()
        if "niftyindices" not in blocked: scan_indices()
        else: log("niftyindices blocked — keeping previous sector index data")
        if not {"binance", "okx"} <= set(blocked): scan_global()
        build(meta)
    # quality gate: refuse to publish a thin scan
    D = json.load(open("data2.json")); G = json.load(open("gdata.json"))
    ni, ng = len(D["stocks"]), len(G["items"])
    exp_i, exp_g = len(CFG["india"]["stocks"]), len(CFG["global"]["yahoo"]) + len(CFG["global"]["crypto"]) - 1
    log(f"quality: india {ni}/{exp_i}, global {ng}/{exp_g}")
    if ni < 0.95 * exp_i or ng < 0.95 * exp_g: raise SystemExit("QUALITY GATE FAILED — too many tickers missing; do not publish.")
    # run summary + verdict changes vs the previous run
    from collections import Counter
    cur = {"in": {o["t"]: o["dec"] for o in D["stocks"]}, "gl": {o["t"]: o["dec"] for o in G["items"]}}
    prev = json.load(open("decisions.json")) if os.path.exists("decisions.json") else {"in": {}, "gl": {}}
    R = {"Buy candidate": 4, "Wait for pullback": 3, "Watch: pullback": 2, "No edge yet": 1, "Avoid for now": 0}
    order = ["Buy candidate", "Wait for pullback", "Watch: pullback", "No edge yet", "Avoid for now"]
    lines = [f"Mode: {'crypto refresh' if '--crypto' in sys.argv else 'global refresh' if '--global' in sys.argv else 'full scan'}. India data: {D.get('scan', {}).get('label')}; global/crypto: {G.get('scan', {}).get('label')}.",
             f"Scanned: India {ni}/{exp_i} stocks, global {ng}/{exp_g} tickers. Missing/stale: " + ("; ".join(l for l in LOG if "kept previous" in l and not l.endswith("[], kept previous data for []")) or "none") + "."]
    for k, name in (("in", "India"), ("gl", "Global")):
        c = Counter(cur[k].values())
        ch = [(t, prev[k].get(t), d) for t, d in cur[k].items() if prev[k].get(t) and prev[k][t] != d]
        big = [f"{t} {a}→{b}" for t, a, b in ch if a in R and b in R and (abs(R[a] - R[b]) >= 2 or "Buy candidate" in (a, b))]
        lines.append(f"{name}: " + " / ".join(f"{o} {c.get(o, 0)}" for o in order) + (f" / Data caveat {c['Data caveat']}" if c.get("Data caveat") else "")
                     + f". {len(ch)} calls changed" + (f"; notable: {', '.join(big)}" if big else "") + ".")
    open("out/summary.txt", "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
    json.dump(cur, open("decisions.json", "w"))
    os.makedirs("out", exist_ok=True)
    json.dump({"at": datetime.datetime.now(IST).isoformat(), "log": LOG}, open("out/last_run.json", "w"), indent=1)
