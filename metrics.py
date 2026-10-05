"""Technical metrics — a line-for-line port of the browser scan used for the 30 Sep 2026 dashboard.
rows: list of [ts_ms, open, high, low, close, volume] (oldest first)
weekly: same shape, weekly bars (for 1Y/3Y/5Y and CAGR)
P: bars per [1W, 1M, 3M, 6M, 1Y] — equities [5,21,63,126,250], crypto [7,30,91,182,365]
Returns the pipe-delimited line the builders (analyze.py / build2.py / gbuild.py) read.
"""
import math, datetime

def sma(a, n, end=None):
    end = len(a) if end is None else end
    if end < n: return None
    s = a[end-n:end]
    return sum(s) / n

def ema(a, n):
    k = 2 / (n + 1); e = a[0]; out = [e]
    for x in a[1:]:
        e = x * k + e * (1 - k); out.append(e)
    return out

def rsi(c, n=14):
    if len(c) < n + 1: return None
    g = l = 0.0
    for i in range(1, n + 1):
        d = c[i] - c[i-1]
        if d > 0: g += d
        else: l -= d
    g /= n; l /= n
    for i in range(n + 1, len(c)):
        d = c[i] - c[i-1]
        g = (g * (n - 1) + max(d, 0)) / n
        l = (l * (n - 1) + max(-d, 0)) / n
    return 100.0 if l == 0 else 100 - 100 / (1 + g / l)

def adx(h, l, c, n=14):
    if len(c) < 2 * n + 2: return (None, None, None, None)
    tr, pdm, mdm = [], [], []
    for i in range(1, len(c)):
        up = h[i] - h[i-1]; dn = l[i-1] - l[i]
        pdm.append(up if (up > dn and up > 0) else 0)
        mdm.append(dn if (dn > up and dn > 0) else 0)
        tr.append(max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1])))
    atr = sum(tr[:n]); p = sum(pdm[:n]); m = sum(mdm[:n]); dx = []; pdi = mdi = None
    for i in range(n, len(tr)):
        atr = atr - atr / n + tr[i]; p = p - p / n + pdm[i]; m = m - m / n + mdm[i]
        pdi = 100 * p / atr if atr else 0; mdi = 100 * m / atr if atr else 0
        dx.append(100 * abs(pdi - mdi) / ((pdi + mdi) or 1))
    ad = sum(dx[:n]) / n
    for i in range(n, len(dx)): ad = (ad * (n - 1) + dx[i]) / n
    return (ad, pdi, mdi, sum(tr[-n:]) / n)

def f(x, d=1):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))): return ""
    return f"{x:.{d}f}"

def pc(a, b):
    return (a / b - 1) * 100 if (a and b) else None

def prec(x, p=6):
    return float(f"{x:.{p}g}")

def line(key, sym, name, R, W, P):
    c = [r[4] for r in R]; h = [r[2] for r in R]; l = [r[3] for r in R]; v = [r[5] or 0 for r in R]
    N = len(c); px = c[-1]
    ret = lambda k: (px / c[N-1-k] - 1) * 100 if N > k and c[N-1-k] else None
    e12 = ema(c, 12); e26 = ema(c, 26); macd = [a - b for a, b in zip(e12, e26)]; sig = ema(macd, 9)
    hist = [a - b for a, b in zip(macd, sig)]
    ADX, PDI, MDI, ATR = adx(h, l, c)
    w = min(P[4], N); hi = max(h[-w:]); lo = min(l[-w:])
    hh = N >= 40 and max(h[-20:]) > max(h[-40:-20])
    hl = N >= 40 and min(l[-20:]) > min(l[-40:-20])
    upv = dnv = 0
    for i in range(max(1, N - 50), N):
        if c[i] > c[i-1]: upv += v[i]
        else: dnv += v[i]
    span = min(P[4], N); step = max(1, round(span / 26)); sp = [c[i] for i in range(N - span, N, step)] + [px]
    mn, mx = min(sp), max(sp)
    code = "".join(chr(48 + round((x - mn) / ((mx - mn) or 1) * 61)) for x in sp).replace("|", "!")
    s20, s50, s200 = sma(c, 20), sma(c, 50), sma(c, 200)
    wc = [(r[0], r[4]) for r in W]; now = R[-1][0]
    def atY(y):
        t = now - y * 365.25 * 864e5
        if not wc or wc[0][0] > t + 14 * 864e5: return None
        val = None
        for ts, cl in wc:
            if ts <= t: val = cl
            else: break
        return val
    y1, y3, y5 = atY(1), atY(3), atY(5)
    vr = f(sma(v, 20) / (sma(v, 50) or 1), 2) if any(x > 0 for x in v[-50:]) and sma(v, 50) is not None else ""
    since = datetime.datetime.utcfromtimestamp((W[0][0] if W else R[0][0]) / 1000).strftime("%Y-%m")
    rsi5 = rsi(c[:N-5])
    return "|".join(str(x) for x in [
        key, sym, (name or key).replace("|", "/"), N, prec(px), f(ret(1)), f(ret(P[0])), f(ret(P[1])), f(ret(P[2])), f(ret(P[3])), f(ret(P[4])),
        f(pc(px, s20)), f(pc(px, s50)), f(pc(px, s200)), f(pc(s50, sma(c, 50, N - 10)) if s50 else None), f(pc(s200, sma(c, 200, N - 20)) if s200 else None), f(pc(s50, s200) if s50 and s200 else None),
        f(rsi(c), 0), f(rsi5, 0), f(hist[-1] / px * 1000, 2), f(hist[-6] / px * 1000, 2) if N >= 6 else "",
        f(ADX, 0), f((PDI - MDI) if PDI is not None else None, 0), f(ATR / px * 100 if ATR else None), f(pc(px, hi)), f(pc(px, lo), 0),
        ("1" if hh else "0") + ("1" if hl else "0"), vr, f(upv / dnv, 2) if dnv else "", code,
        f(pc(px, y1)), f(pc(px, y3)), f(pc(px, y5)),
        f((math.pow(px / y3, 1/3) - 1) * 100) if y3 else "", f((math.pow(px / y5, 1/5) - 1) * 100) if y5 else "", since])
