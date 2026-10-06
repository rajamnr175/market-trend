"""Market News Desk — collect market-only headlines from public RSS feeds.

Writes news.json (headline, source, link, time, categories, importance). Headlines and links only: no article text.
Usage: python3 news.py
"""
import json, os, re, time, html, datetime, email.utils, concurrent.futures as cf
import urllib.request, urllib.parse
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept": "application/rss+xml,application/xml,text/xml,*/*"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
WINDOW_H = 48          # keep headlines from the last 48 hours
MAX_ITEMS = 300

def gn(q, region="US"):
    hl, gl, ce = ("en-IN", "IN", "IN:en") if region == "IN" else ("en-US", "US", "US:en")
    return f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl={hl}&gl={gl}&ceid={ce}"

# name, url, region hint (US / IN / CRYPTO / GLOBAL), kind (news / official / aggregator)
FEEDS = [
    ("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss", "GLOBAL", "news"),
    ("Bloomberg", "https://feeds.bloomberg.com/economics/news.rss", "GLOBAL", "news"),
    ("Bloomberg", "https://feeds.bloomberg.com/crypto/news.rss", "CRYPTO", "news"),
    ("Bloomberg", gn("site:bloomberg.com markets when:1d"), "GLOBAL", "aggregator"),
    ("Bloomberg", gn("site:bloomberg.com India markets when:2d", "IN"), "IN", "aggregator"),
    ("Reuters", gn("site:reuters.com markets when:1d"), "GLOBAL", "aggregator"),
    ("Reuters", gn("site:reuters.com India markets when:2d", "IN"), "IN", "aggregator"),
    ("CNN Business", gn("site:cnn.com/business markets when:2d"), "GLOBAL", "aggregator"),
    ("CNBC", gn("site:cnbc.com markets when:1d"), "GLOBAL", "aggregator"),
    ("Wall Street Journal", "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain", "US", "news"),
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories", "US", "news"),
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_marketpulse", "US", "news"),
    ("Financial Times", "https://www.ft.com/markets?format=rss", "GLOBAL", "news"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex", "US", "news"),
    ("Investing.com", "https://www.investing.com/rss/news.rss", "GLOBAL", "news"),
    ("Economic Times", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "IN", "news"),
    ("Economic Times", "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms", "IN", "news"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/marketreports.xml", "IN", "news"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/business.xml", "IN", "news"),
    ("Mint", "https://www.livemint.com/rss/markets", "IN", "news"),
    ("Business Standard", "https://www.business-standard.com/rss/markets-106.rss", "IN", "news"),
    ("BusinessLine", "https://www.thehindubusinessline.com/markets/feeder/default.rss", "IN", "news"),
    ("NDTV Profit", "https://feeds.feedburner.com/ndtvprofit-latest", "IN", "news"),
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/", "CRYPTO", "news"),
    ("Cointelegraph", "https://cointelegraph.com/rss", "CRYPTO", "news"),
    ("The Block", "https://www.theblock.co/rss.xml", "CRYPTO", "news"),
    ("Decrypt", "https://decrypt.co/feed", "CRYPTO", "news"),
    ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml", "US", "official"),
    ("RBI", "https://www.rbi.org.in/pressreleases_rss.xml", "IN", "official"),
    ("US SEC", "https://www.sec.gov/news/pressreleases.rss", "US", "official"),
    ("SEBI", "https://www.sebi.gov.in/sebirss.xml", "IN", "official"),
    ("ECB", "https://www.ecb.europa.eu/rss/press.html", "GLOBAL", "official"),
]

def kw(*words):
    return re.compile(r"\b(" + "|".join(words) + r")", re.I)

CATS = {
    "rates":  kw("fed\\b", "fomc", "federal reserve", "powell", "rate cut", "rate hike", "rates? (?:decision|path|outlook)", "interest rate",
                 "monetary policy", "repo rate", "rbi\\b", "reserve bank", "mpc\\b", "ecb\\b", "bank of japan", "boj\\b", "bank of england",
                 "central bank", "inflation", "cpi\\b", "pce\\b", "basis points?", "bps\\b", "hawkish", "dovish", "rate-cut", "rate-hike"),
    "bonds":  kw("treasur(y|ies)", "dated securities", "treasury bills?", "state development loans?", "government securities", "yields?\\b", "bonds?\\b", "g-sec", "gilts?", "bunds?", "10-year", "2-year", "30-year", "debt market",
                 "fixed income", "t-bills?", "sovereign debt", "credit spread"),
    "crypto": kw("bitcoin", "btc\\b", "crypto", "ether\\b", "ethereum", "solana", "stablecoin", "blockchain", "token", "defi\\b",
                 "coinbase", "binance", "xrp\\b", "memecoin", "digital asset", "web3", "altcoin"),
    "reg":    kw("sec\\b", "sebi", "regulat", "rule(s|making)?\\b", "ban(s|ned)?\\b", "approv", "lawsuit", "probe", "investigat",
                 "fine[ds]?\\b", "penalt", "circular", "compliance", "cftc", "legislation", "bill\\b", "tariff", "sanction", "framework",
                 "guideline", "antitrust", "licen[cs]e"),
    "india":  kw("sensex", "nifty", "india", "indian", "rupee", "rbi\\b", "sebi", "nse\\b", "bse\\b", "dalal", "mumbai", "fii", "fpi",
                 "mutual fund", "adani", "reliance", "tata", "infosys", "hdfc", "icici"),
    "us":     kw("wall street", "s&p", "dow\\b", "nasdaq", "russell", "u\\.s\\. stocks", "us stocks", "nyse", "nvidia", "apple", "tesla",
                 "microsoft", "amazon", "alphabet", "meta\\b", "fed\\b", "treasury", "earnings"),
    "world":  kw("china", "chinese", "japan", "nikkei", "europe", "stoxx", "ftse", "dax\\b", "hang seng", "asia", "emerging market",
                 "yen\\b", "yuan", "euro\\b", "opec", "global market", "world market", "kospi", "korea", "uk\\b", "britain"),
    "cmdty":  kw("oil\\b", "crude", "brent", "wti\\b", "gold\\b", "silver", "copper", "opec", "natural gas", "commodit"),
}
MARKET = kw("stock", "share", "market", "index", "indices", "rate", "yield", "bond", "treasur", "crypto", "bitcoin", "fed\\b", "rbi\\b",
            "sebi", "sec\\b", "earning", "ipo\\b", "investor", "fund", "rupee", "dollar", "currenc", "oil\\b", "gold\\b", "inflation", "gdp",
            "econom", "bank", "tariff", "trade", "profit", "revenue", "sensex", "nifty", "nasdaq", "s&p", "dow\\b", "wall street",
            "token", "etf\\b", "valuation", "rally", "sell-?off", "futures", "commodit", "debt", "deficit", "fiscal", "monetary", "regulat")
BIG = kw("rate cut", "rate hike", "cuts? rates", "raises? rates", "hikes? rates", "holds? rates", "keeps? rates", "repo rate",
         "fomc", "emergency", "record high", "all-time high", "record low", "crash", "plunge", "plummet", "tumble", "slump", "rout",
         "sell-?off", "soar", "surge", "jump", "spike", "biggest", "worst", "best day", "worst day", "halt", "circuit", "default",
         "bankrupt", "collapse", "recession", "ban\\b", "bans\\b", "approves?", "approval", "lawsuit", "liquidat", "hack", "exploit",
         "yields? (?:jump|surge|spike|soar|climb|hit|top)", "inflation (?:jump|surge|cool|eas)", "selloff", "turmoil")
NOISE = kw("my (?:wife|husband|mom|dad|son|daughter|parents)", "should i\\b", "i'm \\d", "i am \\d", "retire(?:ment)? (?:savings|plan)",
            "market talk", "roundup", "stock picks?", "stocks to buy", "buy,? sell or hold", "buy or sell", "trade setup", "share options",
            "initiates? .{0,40}coverage", "price target", "reiterates?", "maintains? .{0,30}rating", "horoscope", "recipe", "quiz")
RBI_NOISE = kw("sahakari", "co-?operative bank", "urban (?:co-?operative )?bank", "section 35a", "nagrik", "souharda",
               "cancels? (?:the )?(?:certificate|licence|license)", "lost/stolen", "compounding")
SEBI_NOISE = kw("order in (?:the )?(?:matter|respect)", "adjudication", "settlement order", "recovery certificate", "exemption order",
                "summons", "notice of demand", "attachment")

def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()
    return re.sub(r"\s+", " ", s)

def parse_time(s):
    if not s: return None
    try:
        d = email.utils.parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception: return None
    if d.tzinfo is None: d = d.replace(tzinfo=datetime.timezone.utc)
    return d.astimezone(datetime.timezone.utc)

def fetch(feed):
    name, url, region, kind = feed
    for a in range(2):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            root = ET.fromstring(data)
            break
        except Exception as e:
            err = str(e)[:80]; time.sleep(2)
    else:
        return feed, [], err
    out = []
    atom = "{http://www.w3.org/2005/Atom}"
    nodes = root.findall(".//item") or root.findall(f".//{atom}entry")
    for it in nodes:
        g = lambda tag: (it.findtext(tag) or it.findtext(atom + tag) or "")
        title = clean(g("title"))
        link = g("link").strip()
        if not link:
            le = it.find(atom + "link"); link = le.get("href") if le is not None else ""
        ts = parse_time(g("pubDate") or g("published") or g("updated") or it.findtext("{http://purl.org/dc/elements/1.1/}date"))
        src = name
        if kind == "aggregator":       # Google News: "Headline - Publisher"
            s_el = it.find("source")
            pub = clean(s_el.text) if s_el is not None and s_el.text else ""
            m = re.match(r"^(.*)\s+-\s+([^-]{2,60})$", title)
            if m: title = m.group(1).strip(); pub = pub or m.group(2).strip()
            if pub and not re.search(r"bloomberg|reuters|cnn|cnbc", pub, re.I): continue   # keep the requested outlets only
            src = pub or name
            src = {"Bloomberg.com": "Bloomberg"}.get(src, src)
        if not title or not link or not ts: continue
        out.append(dict(t=title, u=link, src=src, ts=ts, region=region, kind=kind))
    return feed, out, None

def norm(t):
    return set(w for w in re.findall(r"[a-z0-9]+", t.lower()) if len(w) > 2 and w not in
               {"the", "and", "for", "with", "after", "amid", "from", "says", "into", "over", "its", "are", "has", "will", "this", "that"})

def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(hours=WINDOW_H)
    items, status = [], {}
    with cf.ThreadPoolExecutor(8) as ex:
        for feed, got, err in ex.map(fetch, FEEDS):
            st = status.setdefault(feed[0], {"ok": 0, "n": 0, "err": None})
            if err: st["err"] = err
            else: st["ok"] += 1
            for x in got:
                if x["ts"] < cutoff or x["ts"] > now + datetime.timedelta(hours=1): continue
                text = x["t"]
                if x["src"] == "SEBI" and SEBI_NOISE.search(text): continue
                if NOISE.search(text): continue
                if x["src"] == "RBI" and RBI_NOISE.search(text): continue
                if re.search(r"hits (?:all-time|52-week|record) (?:high|low) at", text, re.I): continue
                if x["kind"] != "official" and not MARKET.search(text) and x["region"] != "CRYPTO": continue
                cats = [c for c, rx in CATS.items() if rx.search(text)]
                if x["region"] == "CRYPTO" and "crypto" not in cats: cats.append("crypto")
                geo = {"india", "us", "world"} & set(cats)
                if not geo and x["region"] == "IN": cats.append("india")
                if not geo and x["region"] == "US" and "crypto" not in cats: cats.append("us")
                if x["kind"] == "official":
                    if x["src"] in ("Federal Reserve", "RBI", "ECB") and "rates" not in cats and re.search(r"policy|rate|monetary|statement|minutes", text, re.I):
                        cats.append("rates")
                    if x["src"] in ("US SEC", "SEBI") and "reg" not in cats: cats.append("reg")
                if not cats: cats = ["world"] if x["region"] == "GLOBAL" else []
                if not cats: continue
                x["cats"] = cats
                x["imp"] = (3 if BIG.search(text) else 0) + (3 if x["kind"] == "official" and x["src"] in ("Federal Reserve", "RBI", "ECB") and
                    re.search(r"monetary policy|policy (?:statement|decision)|fomc|minutes|governor.s statement|interest rates?", text, re.I) else 0)
                items.append(x)
    # de-duplicate the same story across outlets; keep the earliest, note the other outlets
    items.sort(key=lambda x: x["ts"])
    kept = []
    for x in items:
        w = norm(x["t"]); dup = None
        for k in kept[-400:]:
            if not w or not k["_w"]: continue
            j = len(w & k["_w"]) / len(w | k["_w"])
            if j >= 0.6 or x["t"].lower() == k["t"].lower(): dup = k; break
        if dup:
            if x["src"] not in dup["also"] and x["src"] != dup["src"]: dup["also"].append(x["src"])
            dup["cats"] = sorted(set(dup["cats"]) | (set(x["cats"]) - {"india", "us", "world"}))
            dup["imp"] = max(dup["imp"], x["imp"])
            continue
        x["_w"] = w; x["also"] = []; kept.append(x)
    for k in kept:
        if len(k["also"]) >= 2: k["imp"] += 1      # several outlets on the same story
    kept.sort(key=lambda x: x["ts"], reverse=True)
    kept = kept[:MAX_ITEMS]
    out = [dict(t=k["t"], u=k["u"], src=k["src"], also=k["also"], ts=int(k["ts"].timestamp()), cats=k["cats"], imp=k["imp"]) for k in kept]
    asof = datetime.datetime.now(IST)
    res = dict(asof=asof.strftime("%-d %b %Y, %H:%M IST"), iso=now.strftime("%Y-%m-%dT%H:%M:%SZ"), window_h=WINDOW_H,
               sources=[dict(name=k, **v) for k, v in status.items()], items=out)
    json.dump(res, open("news.json", "w"), ensure_ascii=False, separators=(",", ":"))
    ok = sum(1 for v in status.values() if v["ok"]); print(f"news.json: {len(out)} headlines from {ok}/{len(status)} sources")
    for k, v in status.items():
        if not v["ok"]: print("  source failed:", k, v["err"])

if __name__ == "__main__":
    main()
