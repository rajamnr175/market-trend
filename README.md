# Market Trend dashboard

A daily-chart technical scan of my Indian watchlist (NSE/BSE + NSE sector indices) and my global watchlist
(US stocks & indices, crypto, Treasury yields, commodities, FX). GitHub Actions rescans it automatically and
GitHub Pages hosts the dashboard.

**Website:** https://rajamnr175.github.io/market-trend/ (after GitHub Pages is switched on)

## Schedule (Monday–Friday, IST)
| Time  | What runs |
|-------|-----------|
| 09:45 | Full scan: India + US + crypto |
| 13:45 | Full scan |
| 15:45 | Full scan (after NSE close) |
| 20:45 | Global refresh: US stocks, indices, FX, yields, crypto (India keeps its 15:45 data) |

GitHub can start scheduled runs 5–30 minutes late at busy times. To run it right now:
**Actions → Market Trend rescan → Run workflow** (choose `full` or `global`).

## News section
`news.py` collects market-only headlines (last 48 h) from public RSS feeds: Bloomberg, Reuters, CNN Business, CNBC
(these four partly via Google News), WSJ, MarketWatch, FT, Yahoo Finance, Investing.com, Economic Times, Moneycontrol,
Mint, Business Standard, BusinessLine, NDTV Profit, CoinDesk, Cointelegraph, The Block, Decrypt, Federal Reserve, RBI,
US SEC, SEBI and ECB. Headlines are tagged (US, India, crypto, rates, bonds, regulation, world, commodities) and the
biggest stories are flagged "Top story". `.github/workflows/news.yml` refreshes `docs/news.json` every hour; the page
loads it automatically. Headlines and links only — no article text is copied.

## Files
- `scan.py` downloads prices and runs everything; `metrics.py` computes the indicators;
  `analyze.py`, `build2.py`, `gbuild.py` assign verdicts, decisions and sector/group rankings.
- `config.json` holds the ticker lists. `template_visual.html` is the page design.
- `raw.txt`, `lt.txt`, `idx.txt`, `graw.txt`, `cs.json`, `scan_*.json`, `decisions.json` are the latest data (updated by each run).
- `docs/index.html` is the published dashboard. `publish_site.py` copies each new scan into it.
- `.github/workflows/scan.yml` is the schedule.

## Data sources
Yahoo Finance (stocks, indices, futures, FX, yields), NSE Indices (niftyindices.com), Binance public data
(crypto; OKX/Bitget/Gate for coins Binance doesn't list), CoinGecko (crypto market size/dominance).
News blurbs and US macro figures are static text from the 30 Sep 2026 research.

Safeguard: if fewer than 95% of tickers download, the run fails and the website keeps the last good scan.

Educational technical screen only — not investment advice.
