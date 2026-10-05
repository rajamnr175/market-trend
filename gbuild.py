import json, statistics as st
from collections import Counter
F="key sym name bars px chg1d r1w r1m r3m r6m r1y d20 d50 d200 s50slope s200slope s50v200 rsi rsi5 hist hist5 adx dmi atrp fromHi fromLo hhhl vr udv spark y1 y3 y5 c3 c5 since".split()
R={}
for ln in open('graw.txt'):
    p=ln.rstrip('\n').split('|')
    if len(p)!=len(F): print("BAD",p[0],len(p)); continue
    d=dict(zip(F,p))
    for k in F:
        if k in('key','sym','name','hhhl','spark','since'): continue
        d[k]=float(d[k]) if d[k]!='' else None
    d['hh']=d['hhhl'][0]=='1'; d['hl']=d['hhhl'][1]=='1'
    R[d['key']]=d
G={
"Semiconductors":"NVDA AMD INTC TSM MU AVGO SNPS",
"Storage & AI hardware":"SNDK STX WDC DELL SMCI",
"Big Tech & software":"AAPL PLTR NOW SNOW",
"Crypto stocks & fintech":"COIN MSTR HOOD CRCL GEMI SBET IREN CIFR RKT",
"Defense & drones":"LMT RTX KTOS ONDS UMAC",
"EV, energy & power":"TSLA BE TE XLE INDO",
"US indices & futures":"SPX NDX DJI RUS2000 ES1! NQ1! QQQ",
"Commodities":"GOLD SILVER WTI NATGAS COPPER",
"Currencies":"DXY EURUSD USDJPY USDEUR USDINR EURINR",
"US Treasury yields":"US13W US2Y US5Y US10Y US30Y",
"Crypto majors":"BTC ETH SOL XRP BNB DOGE ADA TRX AVAX LINK DOT LTC BCH ETC XLM HBAR XMR ZEC SUI APT NEAR HYPE BTC1! ETH1!",
"DeFi & exchanges":"UNI AAVE LDO CRV ENA ONDO PENDLE ETHFI EIGEN ENS INJ RUNE JUP RAY DRIFT KMNO JTO FLUID PYTH SWELL CPOOL RSR WOO LIT ASTER DEEP TNSR",
"Layer 1s & Layer 2s":"OP ARB STRK ZK LINEA MNT SEI TIA S BERA MOVE STACKS ZRO",
"AI, DePIN & gaming":"TAO FET RENDER AR FIL GRT ARKM IO AKT ATH GRASS VIRTUAL AIXBT GRIFFAIN ZEREBRO COOKIE ACT GOAT PIPPIN VVV WLD SUPER PRIME ZIG CHIP",
"Memecoins":"BONK WIF FLOKI PEPE POPCAT FARTCOIN TRUMP SPX6900 USELESS PUMP BROCCOLI CASHCAT CHILLGUY PENGU",
"Crypto ratios":"ETHBTC SOLBTC SOLETH",
}
CLS={"Semiconductors":"US stocks","Storage & AI hardware":"US stocks","Big Tech & software":"US stocks","Crypto stocks & fintech":"US stocks","Defense & drones":"US stocks","EV, energy & power":"US stocks","US indices & futures":"Indices","Commodities":"Commodities","Currencies":"Currencies","US Treasury yields":"Bonds","Crypto majors":"Crypto","DeFi & exchanges":"Crypto","Layer 1s & Layer 2s":"Crypto","AI, DePIN & gaming":"Crypto","Memecoins":"Crypto","Crypto ratios":"Crypto"}
CFG=json.load(open("config.json"))
if CFG["global"].get("usgroups"):
    OLDUS=[g for g,c in CLS.items() if c in("US stocks","Indices")]
    old_t=set(sum((G[g].split() for g in OLDUS),[]))
    for g in OLDUS: G.pop(g); CLS.pop(g)
    NG={}; NC={}
    for x in CFG["global"]["usgroups"]: NG[x["g"]]=" ".join(x["tickers"]); NC[x["g"]]=x["cls"]
    new_t=set(" ".join(NG.values()).split())
    left=[t for t in old_t if t not in new_t and t!="VIX"]
    if left: NG["Other A-list stocks"]=" ".join(sorted(left)); NC["Other A-list stocks"]="US stocks"
    G={**NG,**G}; CLS={**NC,**CLS}
grp={}
for g,l in G.items():
    for t in l.split(): grp[t]=g
miss=[k for k in R if k not in grp and k!='VIX']; print("unmapped",miss)
NOVERDICT={"US Treasury yields","Crypto ratios"}
clamp=lambda x:max(0,min(1,x))
SPX=R['SPX']; BTC=R['BTC']
NEWS={
"INTC":"Up about 260% in 2026 on its foundry comeback. On 18 Jun, President Trump announced Apple would work with Intel to design and build chips in the US (Intel 18A-P, lower-end parts; TSMC keeps over 90% of Apple volume).",
"AMD":"On 4 Aug AMD guided data-centre revenue to more than double in 2027. A July deal with Anthropic covers up to 2 GW of MI450 GPUs from H1 2027. The stock hit record highs above $600.",
"MU":"Memory and storage are the tightest part of the AI build-out. Storage stocks took off after Nvidia's CEO called storage a 'completely unserved market' at CES (Jan 2026).",
"SNDK":"Up about 12x in a year on the AI memory and storage shortage that started with Nvidia's CES comments (Jan 2026).",
"STX":"Part of the AI storage rally since Jan 2026 (hard drives for data centres).",
"WDC":"Part of the AI storage rally since Jan 2026 (hard drives for data centres).",
"BE":"Fuel cells for AI data centres. A multi-billion deal to power Nebius AI data centres (May 2026) re-rated the stock.",
"ZEC":"Rallied above $1,000 in September. Drivers: more coins moving into the shielded (private) pool, the Ironwood upgrade fixing a counterfeiting bug, and a Grayscale spot ETF with about $34 M of inflows in its first two weeks.",
"BTC":"Down about 32% over a year and 34% below its high, but up about 40% in 3 months. It traded near $85,700 on 23 Sep.",
"US10Y":"Topped 5% on 14 Sep for the first time since 2023 and is now 5.26%, the highest since 2007. Drivers: oil-driven inflation worries, heavy deficits, and a Fed that hiked to 3.75–4.00% on 16 Sep.",
"WTI":"Up about 46% over a year on West Asia tensions. This feeds US inflation and bond yields.",
}
GWHY={
"Semiconductors":"The AI spending boom carries on even with 5% bond yields. AMD and Intel lead on new deals. Broadcom and Synopsys are lagging.",
"Storage & AI hardware":"The strongest group on your list over 1 year (Sandisk about +1,250%, Micron +470%). Memory and storage are the bottleneck of the AI build-out. After runs this big, pullbacks can be sharp.",
"Big Tech & software":"Apple and Palantir hold up. ServiceNow is in a downtrend, and Snowflake is range-bound after a big run.",
"Crypto stocks & fintech":"These trade as leveraged bets on Bitcoin, which is down 32% over a year. Most are bouncing in the last 3 months but remain far below their highs.",
"Defense & drones":"Weak: Lockheed, RTX and Kratos are all below falling 200-day averages.",
"EV, energy & power":"Split. Bloom Energy is strong on AI data-centre power demand. Tesla and T1 Energy are weak.",
"US indices & futures":"The S&P 500 sits about 2% below its high and the Nasdaq-100 about 1%. The Dow and the Russell 2000 (small caps) are weaker, hurt by 5% yields.",
"Commodities":"Crude is up 46% in a year (West Asia). Gold and silver are correcting hard from record highs. Copper is near its highs.",
"Currencies":"The dollar is firm as US yields rise and the Fed hikes. The rupee is weak: USD/INR is near 96, up 8% in a year.",
"US Treasury yields":"Yields are rising across the curve: 10-year 5.26%, 30-year 5.59%. Rising yields mean falling bond prices, and they pressure stocks and crypto.",
"Crypto majors":"Crypto is in a bear-market recovery. Most coins are 30–70% below their highs but up 30–60% in the last 3 months. Privacy coins (Zcash, Monero) and NEAR lead.",
"DeFi & exchanges":"A strong 3-month rebound (Uniswap, Ethena, Raydium, Kamino) from very deep lows. Most coins are still 40–90% below their highs.",
"Layer 1s & Layer 2s":"Bouncing, but long-term trends are poor. Most Layer 2 tokens are down 50–90% in a year.",
"AI, DePIN & gaming":"Mixed. Venice (VVV), Grass and Bittensor are strong. Many AI-agent tokens are down 70–90% from their highs.",
"Memecoins":"Mostly weak and very volatile. Useless and Pump.fun are the only real momentum names.",
"Crypto ratios":"ETH/BTC and SOL/BTC show whether altcoins are beating Bitcoin. Both are rising over 3 months.",
}
USWHY={
"US & world indices":"Benchmarks for the US and Asian markets you watch: S&P 500, Nasdaq-100, Dow, Russell 2000, their futures, plus Nikkei and KOSPI.",
"Magnificent 7":"The mega-cap leaders (plus SpaceX's listed shares, SPCX) that drive most of the S&P 500's moves.",
"Memory & storage":"DRAM, NAND and hard-drive makers, including Samsung and SK hynix (prices in KRW). Memory is a key bottleneck of the AI build-out.",
"AI compute silicon":"GPU, accelerator and foundry names that supply AI compute, plus ASML's lithography machines.",
"Server OEMs & cooling":"Server builders and the power and cooling suppliers for AI data centres.",
"Networking & connectivity":"Switching, interconnect and optical-network suppliers that link AI clusters together.",
"Neo-clouds & AI infrastructure":"GPU cloud providers and data-centre developers renting AI compute.",
"Optical & photonics":"Laser, fibre and co-packaged-optics suppliers (SIVE trades in SEK).",
"Energy & power":"Utilities, fuel cells, storage and grid names riding AI data-centre power demand.",
"Software":"Enterprise software, data and cybersecurity platforms.",
"AI, defence & industrials":"Defence, space, rare earths and industrial names from your list, plus the Korea ETF.",
"Other US stocks & ETFs":"The rest of your US list: consumer, banks, energy, healthcare, fintech and sector ETFs.",
"AI data-centre supply chain":"Smaller chip, power-semiconductor and equipment makers across the US, Europe and Asia (non-US prices are in local currency).",
"Roundhill & thematic ETFs":"Thematic ETFs (humanoid robots, space, Magnificent 7, generative AI, semiconductors) and a few related names.",
"Other A-list stocks":"Stocks from your A-list watchlist that are not on the US stocks list.",
}
for g in G: GWHY.setdefault(g,USWHY.get(g,""))
def decision(o):
    b=o['b']; t=o['tags']
    if b in("Strong momentum","Uptrend"):
        if "Extended — don't chase" in t or (o['d50'] or 0)>(25 if o['cls']=="Crypto" else 15): return "Wait for pullback"
        if o['d50'] is not None and o['d50']<=0: return "Watch: pullback"
        if (o['rsi'] or 0)>=50 and o['rs3']>=0: return "Buy candidate"
        return "Watch: pullback"
    if b=="Sideways / correcting": return "No edge yet"
    if b=="Info": return "Info"
    return "Avoid for now"
out=[]
for k,d in R.items():
    if k=='VIX': continue
    g=grp.get(k,'Other A-list stocks'); cls=CLS.get(g,'US stocks'); gv=lambda f:d[f] if d[f] is not None else 0
    bench=BTC if cls=="Crypto" else SPX
    rs3=gv('r3m')-(bench['r3m'] or 0); rs6=gv('r6m')-(bench['r6m'] or 0)
    trend=(5*(gv('d20')>0)+8*(gv('d50')>0)+10*(gv('d200')>0)+8*(gv('s50v200')>0)+7*(gv('s200slope')>0)+5*(gv('s50slope')>0)+3.5*d['hh']+3.5*d['hl'])
    mom=(15*clamp((rs3+20)/40)+10*clamp((rs6+30)/60)+10*clamp((gv('rsi')-30)/40)+5*(gv('hist')>0)+3*(gv('hist')>gv('hist5'))+4*(gv('dmi')>0)+3*(gv('adx')>=25 and gv('dmi')>0))
    sc=round(trend+mom)
    up=gv('d200')>0 and gv('s50v200')>0 and gv('s200slope')>0
    enough=d['bars']>=210
    tags=[]
    if g in NOVERDICT: b="Info"
    elif not enough:
        b="Sideways / correcting" if not(gv('d50')>0 and gv('r3m')>0) else "Uptrend"; tags.append("Short history")
    elif up and gv('d50')>0 and rs3>=15 and gv('rsi')>=55 and gv('fromHi')>=-12: b="Strong momentum"
    elif up and gv('d50')>-6: b="Uptrend"
    else:
        down=gv('d200')<0 and (gv('s50v200')<0 or gv('s200slope')<0)
        bad=sum([gv('rsi')<40, gv('adx')>=25 and gv('dmi')<0, gv('fromLo')<8, gv('r1m')<-8, gv('d50')<-5])
        b="Avoid now" if down and bad>=3 else ("Downtrend" if down else "Sideways / correcting")
    if gv('rsi')>=70 or (d['atrp'] and gv('d20')/d['atrp']>3.5) or gv('d50')>(40 if cls=="Crypto" else 25): tags.append("Extended — don't chase")
    if up and gv('d50')<0: tags.append("Pullback in uptrend")
    if gv('fromHi')>=-3: tags.append("Near 52w high")
    if d['fromLo'] is not None and gv('fromLo')<=5: tags.append("Near 52w low")
    if gv('adx')>=25 and gv('dmi')<0: tags.append("Strong downtrend (ADX)")
    if gv('rsi')<=30: tags.append("Oversold")
    if cls=="Crypto" and gv('fromHi')<=-70: tags.append("70%+ below high")
    if gv('d200')<0 and gv('d50')>0 and b not in("Info",): tags.append("Bouncing below 200D")
    o=dict(t=k,n=d['name'],g=g,cls=cls,src=d['sym'],px=d['px'],d1=d['chg1d'],w=d['r1w'],m=d['r1m'],q=d['r3m'],h=d['r6m'],y=d['r1y'],d20=d['d20'],d50=d['d50'],d200=d['d200'],rsi=d['rsi'],adx=d['adx'],dmi=d['dmi'],atr=d['atrp'],hi=d['fromHi'],lo=d['fromLo'],rs3=round(rs3,1),sc=sc,b=b,tags=tags,sp=d['spark'],y1=d['y1'],y3=d['y3'],y5=d['y5'],c3=d['c3'],c5=d['c5'],bars=int(d['bars']),since=d['since'])
    if d['d50'] is not None: o['s50']=float(f"{d['px']/(1+d['d50']/100):.6g}")
    if d['d200'] is not None: o['s200']=float(f"{d['px']/(1+d['d200']/100):.6g}")
    if g=="US Treasury yields":
        for f in('w','m','q','h','y','y1','y3','y5'):
            v=o[f]; o[f+'_bp']=None if v is None else round((d['px']-d['px']/(1+v/100))*100)
    w=[]
    if b in("Strong momentum","Uptrend"):
        w.append("Above rising 50D and 200D" if (o['d50'] or 0)>0 else "Above rising 200D, pulling back to the 50D")
        if rs3>=10: w.append(f"beating {'Bitcoin' if cls=='Crypto' else 'the S&P 500'} by {rs3:.0f} pts over 3M")
        if gv('fromHi')>=-5: w.append("within 5% of 52-week high")
        if o['rsi'] and o['rsi']>=55: w.append(f"RSI {o['rsi']:.0f}")
    elif b in("Downtrend","Avoid now"):
        w.append("Below a falling 200D")
        if o['rsi'] and o['rsi']<40: w.append(f"weak RSI {o['rsi']:.0f}")
        if gv('adx')>=25 and gv('dmi')<0: w.append("strong seller trend (ADX)")
        if o['lo'] is not None and o['lo']<8: w.append("near 52-week low")
        if o['hi'] is not None and o['hi']<-50: w.append(f"{-o['hi']:.0f}% below 52-week high")
    elif b=="Info": w.append("Tracked for context")
    else:
        w.append("Mixed signals")
        if "Bouncing below 200D" in tags: w.append("bouncing above the 50D but still under a falling 200D")
    o['why']="; ".join(w)+"."
    o['news']=NEWS.get(k,""); o['gwhy']=GWHY[g]
    o['dec']=decision(o)
    out.append(o)
print(Counter(o['dec'] for o in out))
groups=[]
for g in G:
    L=[o for o in out if o['g']==g]
    med=lambda f:(round(st.median([o[f] for o in L if o[f] is not None]),1) if any(o[f] is not None for o in L) else None)
    groups.append(dict(g=g,cls=CLS[g],n=len(L),sc=round(st.mean(o['sc'] for o in L)),d1=med('d1'),w=med('w'),m=med('m'),q=med('q'),h=med('h'),y1=med('y1'),y3=med('y3'),y5=med('y5'),
        up=sum(o['b'] in("Strong momentum","Uptrend") for o in L),dn=sum(o['b'] in("Downtrend","Avoid now") for o in L),
        breadth=round(100*sum((o['d200'] or 0)>0 for o in L)/len(L)),best=max(L,key=lambda o:o['sc'])['t'],worst=min(L,key=lambda o:o['sc'])['t'],why=GWHY[g]))
rank=[x for x in groups if x['g'] not in NOVERDICT]; rank.sort(key=lambda x:-x['sc'])
for i,x in enumerate(rank): x['rank']=i+1
for x in rank: print(x['rank'],x['g'],x['sc'],x['m'],x['q'],x['y1'],x['up'],x['dn'])
for dcs in ["Buy candidate","Wait for pullback","Watch: pullback"]:
    print(dcs,[o['t'] for o in sorted(out,key=lambda o:-o['sc']) if o['dec']==dcs])
macro=dict(asof="30 Sep 2026",items=[
 dict(k="Fed funds rate",v="3.75–4.00%",note="Raised 0.25 pt on 16 Sep 2026, the first hike since 2023. Next meeting 27–28 Oct.",src="FOMC"),
 dict(k="US CPI inflation",v="3.4% YoY",note="August 2026, released 11 Sep. Unchanged from July.",src="BLS"),
 dict(k="Unemployment rate",v="4.1%",note="August 2026. Payrolls +162k, well above the 55k forecast. Wages +3.1% YoY.",src="BLS"),
 dict(k="30-year mortgage",v="6.71%",note="Freddie Mac weekly average, 3 Sep 2026 (15-year: 6.04%).",src="Freddie Mac"),
 dict(k="US 10-year yield",v=f"{R['US10Y']['px']:.2f}%",note="Above 5% since 14 Sep, the highest since 2007.",src="Market"),
])
import os
cs=json.load(open("cs.json")) if os.path.exists("cs.json") else dict(total=2.8827e12,chg24=-2.42,btcd=58.31,ethd=11.39,usdtd=6.36,stabled=6.36+2.57,total2=2.8827e12*(1-0.5831),total3=2.8827e12*(1-0.5831-0.1139),others=2.8827e12-2.6186e12,asof="30 Sep 2026, ~13:00 IST")
bench={k:dict(n=R[k]['name'],px=R[k]['px'],d1=R[k]['chg1d'],m=R[k]['r1m'],q=R[k]['r3m'],y=R[k]['r1y'],rsi=R[k]['rsi'],sp=R[k]['spark'],src=R[k]['sym']) for k in ["SPX","NDX","DJI","RUS2000","VIX","DXY","US10Y","US2Y","GOLD","SILVER","WTI","COPPER","BTC","ETH","SOL","USDINR"]}
scan=json.load(open('scan_global.json')) if os.path.exists('scan_global.json') else None
json.dump(dict(items=out,groups=groups,macro=macro,cs=cs,bench=bench,scan=scan),open('gdata.json','w'),separators=(',',':'),ensure_ascii=False)
import os; print(os.path.getsize('gdata.json'))
