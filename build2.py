import json
D=json.load(open('data.json'))
# long-term stock returns
LT={}
for ln in open('lt.txt'):
    p=ln.strip().split('|')
    if len(p)<7: continue
    f=lambda x: float(x) if x else None
    LT[p[0]]=dict(y1=f(p[1]),y3=f(p[2]),y5=f(p[3]),c3=f(p[4]),c5=f(p[5]),since=p[6])
# indices
IDX=[]
for ln in open('idx.txt'):
    p=ln.strip().split('|')
    f=lambda x: float(x) if x else None
    IDX.append(dict(n=p[0].replace('NIFTY ','').title().replace('It','IT').replace('Fmcg','FMCG').replace('Psu','PSU').replace('Cpse','CPSE').replace('Pse','PSE').replace('Ev ','EV ').replace('50','50'),
      raw=p[0],px=float(p[1]),m1=f(p[2]),m3=f(p[3]),m6=f(p[4]),y1=f(p[5]),y3=f(p[6]),y5=f(p[7]),c3=f(p[8]),c5=f(p[9]),d200=f(p[10]),hi=f(p[11]),ser=[int(x) for x in p[12].split(',')]))
for i in IDX:
    if i['raw']=='NIFTY 50': i['n']='Nifty 50'
    if i['raw']=='NIFTY 500': i['n']='Nifty 500'
KIND={"NIFTY 50":"Broad","NIFTY 500":"Broad","NIFTY MIDCAP 100":"Broad","NIFTY SMALLCAP 100":"Broad",
 "NIFTY INDIA CONSUMPTION":"Theme","NIFTY INDIA MANUFACTURING":"Theme","NIFTY INDIA DIGITAL":"Theme","NIFTY CPSE":"Theme","NIFTY PSE":"Theme","NIFTY COMMODITIES":"Theme","NIFTY EV & NEW AGE AUTOMOTIVE":"Theme","NIFTY INDIA DEFENCE":"Sector","NIFTY INFRASTRUCTURE":"Theme"}
for i in IDX: i['k']=KIND.get(i['raw'],'Sector')
# map watchlist sector -> NSE index
S2I={"IT Services & Software":"NIFTY IT","AI / Data-centre & Cloud":"NIFTY INDIA DIGITAL","Electronics, EMS & Semis":"NIFTY CONSUMER DURABLES","Telecom & Networking":"NIFTY INDIA DIGITAL","Defence & Aerospace":"NIFTY INDIA DEFENCE","Capital Goods & Electricals":"NIFTY INDIA MANUFACTURING","Power & Renewables":"NIFTY ENERGY","Oil, Gas & Coal":"NIFTY OIL & GAS","Metals & Mining":"NIFTY METAL","Pharma & Healthcare":"NIFTY PHARMA","Banks":"NIFTY BANK","NBFC & Insurance":"NIFTY FINANCIAL SERVICES","Capital Markets":"NIFTY CAPITAL MARKETS","Auto & Auto Components":"NIFTY AUTO","FMCG, Retail & Consumer":"NIFTY FMCG","Chemicals":"NIFTY CHEMICALS","Agri, Fertilisers & Sugar":"NIFTY COMMODITIES","Logistics, Travel & Infra":"NIFTY INFRASTRUCTURE"}
SECWHY={
"Pharma & Healthcare":"Defensive leader of 2026: Nifty Pharma +25% in 1Y while Nifty fell. Domestic pharma market grew 13.5% in Q1 FY27, big names posted 16–19% growth, and a weak rupee helps exporters.",
"AI / Data-centre & Cloud":"India's AI-infrastructure build-out (sovereign AI, GPU cloud, data centres) is the strongest theme in the list, even though the broad market is falling.",
"Electronics, EMS & Semis":"Riding the same AI-hardware and electronics-manufacturing wave (PCB plants, government incentives). Leaders are strong, but Kaynes, Dixon and D-Link lag, so the sector is split.",
"Telecom & Networking":"Optical-fibre and data-centre connectivity names (STL, HFCL) are strong. Telecom service majors (Bharti, Tata Comm) are weak.",
"Metals & Mining":"Nifty Metal is the best sector index over 1 year (+30%), on steel import protection and firm commodity prices. September cooled it only slightly.",
"Capital Markets":"Commodity-exchange volumes are booming (MCX), but broker and depository stocks (BSE, CDSL, CAMS, Groww) are correcting with the market.",
"Defence & Aerospace":"Best 3- and 5-year performer in India (Defence index +650% in 5Y), but now 8% off its high and consolidating. Order wins still drive individual names.",
"Oil, Gas & Coal":"Crude spiked in September on West Asia tensions, which squeezes refiners and oil marketing companies. Coal India and Castrol are the exceptions.",
"Auto & Auto Components":"Autos fell 9% in September on weak sales data. Small component makers (Kross, NRB, Belrise) are much stronger than the OEMs.",
"Capital Goods & Electricals":"Long-term winners (ABB, CG Power, BHEL) are correcting after a big run. KEC and Prajind are breaking down.",
"Chemicals":"Mostly weak. Aether is the standout on strong results.",
"Logistics, Travel & Infra":"Adani Ports is the only leader (Sept top Nifty gainer). Cement, IRCTC and Concor are weak.",
"Banks":"Bank Nifty fell 5.6% in September with FII selling. No bank in the list is in an uptrend. PSU banks lead over 5 years, but private banks have been flat.",
"FMCG, Retail & Consumer":"FMCG is the second-worst sector index over 1 year (−18.5%). Slowing consumption and high valuations. Avoid until the trend turns.",
"IT Services & Software":"Worst large sector: Nifty IT −18% 1Y, −22% 5Y. Fears that AI coding agents will cut services revenue (sell-off since Feb 2026), plus the US slowdown.",
"Power & Renewables":"Solar and wind makers (Suzlon, Waaree, Vikram) are in steep downtrends on pricing and overcapacity worries. Utilities are range-bound.",
"NBFC & Insurance":"IRDAI's proposal to cut insurance commissions (24 Sep) crushed PB Fintech and hit insurers. Financial Services index −5% 1Y.",
"Agri, Fertilisers & Sugar":"Weakest group in the list: 9 of 10 stocks in downtrends. Subsidy and input-cost worries, and agrochem exports are soft.",
}
NEWS={
"STLTECH":"Won a multi-year AI data-centre optical-connectivity award worth over $1 bn from a US hyperscaler (22 May 2026). The stock is up roughly 5x in 2026.",
"E2E":"Largest-ever GPU cloud contract: ₹1,000 cr of NVIDIA Blackwell capacity for an Indian sovereign-AI firm, plus a ₹1,500 cr fundraise approved (31 Aug 2026).",
"RPTECH":"AI-led enterprise IT demand. FY26 revenue ₹15,827 cr, semiconductor segment +131%, and a new Dell commercial-distribution deal.",
"SYRMA":"60:40 JV with Italy's Elemaster for high-value electronics (completed Apr 2026). Andhra Pradesh approved a ₹856 cr incentive for its PCB mega-plant.",
"MTARTECH":"₹467 cr international order win. Order book ₹5,363 cr across nuclear, aerospace and clean-energy segments.",
"LAURUSLABS":"Q1 FY27 profit more than doubled (~+125% YoY) on record CDMO business. Joined the ₹1 lakh cr market-cap club.",
"DIVISLAB":"Q1 FY27 net profit +66% YoY to ₹902 cr, revenue +28%.",
"GLAND":"Q1 FY27 (11 Aug): profit +47% to ₹317 cr, revenue +19.5%, EBITDA +33%. Hit a 52-week high after the results.",
"CASTROLIND":"June-quarter results (4 Aug): total income +25% YoY, net profit +42.5% to ₹348 cr.",
"AETHER":"Q1 FY27 profit +33% to ₹63 cr, revenue +27%, growth across all verticals.",
"KROSS":"Q1 FY27 revenue +32% to ₹184 cr. New axle-beam, seamless-tube and forging capacity coming on stream. Q1 margins dipped.",
"NRBBEARING":"Turnaround in Q4 FY26 (₹41 cr profit). Singapore's Arohi Capital bought a 4.5% stake (Jun 2026).",
"MCX":"Record gold and silver trading volumes. Analysts flag resistance at ₹3,400–3,500 (price ₹3,306).",
"SAIL":"Steel stocks got a policy boost (import protection). SAIL hit multi-year highs in 2026 with FII buying.",
"ADANIPORTS":"Top Nifty gainer in September (+9.5%). Capacity expansion and a target of 17% of India's cargo by FY31.",
"COALINDIA":"August supplies +5.5% YoY. One of only 10 Nifty stocks up in September.",
"DRREDDY":"Up 5.8% in September, one of the few Nifty gainers, on pharma sector strength.",
"POLICYBZR":"Crashed about 32% on 24 Sep after IRDAI proposed cutting insurance commissions sharply (health 40%→5%).",
"TCS":"Worst Nifty stock in September (−13.7%) on AI-disruption fears for IT services.",
"INFY":"Down 11.5% in September on AI-disruption fears for IT services.",
"WIPRO":"Down 12.4% in September on AI-disruption fears for IT services.",
"INDIAGLYCO":"Split into three companies from 1 Sep 2026. Price history is not adjusted.",
"VEDL":"Demerged into five companies (May 2026). The ~62% price drop is an adjustment, not a loss.",
}
secsc={s['s']:s for s in D['sectors']}
sec_rank={s['s']:i+1 for i,s in enumerate(D['sectors'])}
nsec=len(D['sectors'])
def decision(o):
    b=o['b']; t=o['tags']
    if b=="Data caveat": return "Data caveat"
    if b in("Strong momentum","Uptrend"):
        if "Extended — don't chase" in t or (o['d50'] or 0)>15: return "Wait for pullback"
        if o['d50'] is not None and o['d50']<=0: return "Watch: pullback"
        if (o['rsi'] or 0)>=50 and o['rs3']>=0: return "Buy candidate"
        return "Watch: pullback"
    if b=="Sideways / correcting": return "No edge yet"
    return "Avoid for now"
for o in D['stocks']:
    o.update({k:v for k,v in LT.get(o['t'],{}).items()})
    o['dec']=decision(o)
    o['srank']=sec_rank.get(o['s'])
    # support: 50D price
    if o['d50'] is not None: o['s50']=round(o['px']/(1+o['d50']/100),1)
    if o['d200'] is not None: o['s200']=round(o['px']/(1+o['d200']/100),1)
    # technical why
    w=[]
    if o['b'] in("Strong momentum","Uptrend"):
        w.append(f"Above rising 50D and 200D" if o['d50']>0 else "Above rising 200D, pulling back to the 50D")
        if o['rs3']>=10: w.append(f"beating Nifty by {o['rs3']:.0f} pts over 3M")
        if o['hi']>=-5: w.append("within 5% of 52-week high")
        if o['rsi'] and o['rsi']>=55: w.append(f"RSI {o['rsi']:.0f}")
    elif o['b'] in("Downtrend","Avoid now"):
        w.append("Below a falling 200D")
        if o['rsi'] and o['rsi']<40: w.append(f"weak RSI {o['rsi']:.0f}")
        if o['dmi'] is not None and o['adx'] and o['adx']>=25 and o['dmi']<0: w.append("strong seller trend (ADX)")
        if o['lo'] is not None and o['lo']<8: w.append("sitting near 52-week low")
    else:
        w.append("Mixed signals; price chopping around its averages")
    o['why']="; ".join(w)+"."
    o['news']=NEWS.get(o['t'],"")
    o['swhy']=SECWHY.get(o['s'],"")
    o['sidx']=S2I.get(o['s'])
SYM={}
for ln in open('raw.txt'):
    p=ln.split('|'); SYM[p[0]]=p[1]
def ysym(k):
    s=SYM.get(k,k)
    if s.startswith('^') or '=' in s: return s
    if s.endswith('@B'): return s[:-2]+'.BO'
    return s+'.NS'
for o in D['stocks']: o['ys']=ysym(o['t'])
for k,bv in D['bench'].items(): bv['ys']=ysym('#'+k)
IXS={"NIFTY 50":"^NSEI","NIFTY 500":"^CRSLDX","NIFTY MIDCAP 100":"NIFTY_MIDCAP_100.NS","NIFTY SMALLCAP 100":"^CNXSC","NIFTY IT":"^CNXIT","NIFTY PHARMA":"^CNXPHARMA","NIFTY HEALTHCARE":"NIFTY_HEALTHCARE.NS","NIFTY BANK":"^NSEBANK","NIFTY PSU BANK":"^CNXPSUBANK","NIFTY PRIVATE BANK":"NIFTY_PVT_BANK.NS","NIFTY FINANCIAL SERVICES":"NIFTY_FIN_SERVICE.NS","NIFTY CAPITAL MARKETS":"NIFTY_CAPITAL_MKT.NS","NIFTY REALTY":"^CNXREALTY","NIFTY AUTO":"^CNXAUTO","NIFTY EV & NEW AGE AUTOMOTIVE":"NIFTY_EV.NS","NIFTY METAL":"^CNXMETAL","NIFTY FMCG":"^CNXFMCG","NIFTY INDIA CONSUMPTION":"^CNXCONSUM","NIFTY CONSUMER DURABLES":"NIFTY_CONSR_DURBL.NS","NIFTY ENERGY":"^CNXENERGY","NIFTY OIL & GAS":"NIFTY_OIL_AND_GAS.NS","NIFTY INFRASTRUCTURE":"^CNXINFRA","NIFTY PSE":"^CNXPSE","NIFTY CPSE":"NIFTY_CPSE.NS","NIFTY MEDIA":"^CNXMEDIA","NIFTY INDIA DEFENCE":"NIFTY_IND_DEFENCE.NS","NIFTY CHEMICALS":"NIFTY_CHEMICALS.NS","NIFTY COMMODITIES":"^CNXCMDT","NIFTY INDIA MANUFACTURING":"NIFTY_INDIA_MFG.NS","NIFTY INDIA DIGITAL":"NIFTY_IND_DIGITAL.NS"}
for i in IDX: i['ys']=IXS[i['raw']]
from collections import Counter
print(Counter(o['dec'] for o in D['stocks']))
print([o['t'] for o in D['stocks'] if o['dec']=="Buy candidate"])
print([o['t'] for o in D['stocks'] if o['dec']=="Wait for pullback"])
print([o['t'] for o in D['stocks'] if o['dec']=="Watch: pullback"])
D['idx']=IDX; D['secwhy']=SECWHY; D['s2i']=S2I
import os
if os.path.exists('scan_india.json'): D['scan']=json.load(open('scan_india.json'))
json.dump(D,open('data2.json','w'),separators=(',',':'),ensure_ascii=False)
import os; print(os.path.getsize('data2.json'))
