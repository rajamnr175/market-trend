import json, statistics as st
F="key sym name bars px chg1d r1w r1m r3m r6m r1y d20 d50 d200 s50slope s200slope s50v200 rsi rsi5 hist hist5 adx dmi atrp fromHi fromLo hhhl vr udv spark".split()
rows={}
for ln in open('raw.txt'):
    p=ln.rstrip('\n').split('|')
    if len(p)!=len(F): print("BAD",p[0],len(p)); continue
    d=dict(zip(F,p))
    for k in F:
        if k in ('key','sym','name','hhhl','spark'): continue
        d[k]=float(d[k]) if d[k] not in ('',) else None
    d['hh']=d['hhhl'][0]=='1'; d['hl']=d['hhhl'][1]=='1'
    rows[d['key']]=d
SECT={
"IT Services & Software":"HCLTECH COFORGE TCS INFY WIPRO TECHM PERSISTENT KPITTECH TATAELXSI TATATECH",
"AI / Data-centre & Cloud":"E2E NETWEB ASMTEC",
"Electronics, EMS & Semis":"KAYNES SYRMA AVALON DIXON MOSCHIP SPELS RPTECH EBGNG DLINKINDIA",
"Telecom & Networking":"HFCL STLTECH TEJASNET TATACOMM BHARTIARTL NELCO",
"Defence & Aerospace":"HAL BEL BDL MAZDOCK DATAPATTNS PARAS MTARTECH ZENTEC SOLARINDS ASTRAMICRO IDEAFORGE DRONACHRYA",
"Capital Goods & Electricals":"ABB CGPOWER BHEL LT KEC POLYCAB GENUSPOWER JNKINDIA PRAJIND TITAGARH APLAPOLLO WEL AEL",
"Power & Renewables":"SUZLON WAAREEENER VIKRAMSOLR ALPEXSOLAR ADANIGREEN NTPC TATAPOWER ADANIPOWER RPOWER CESC ADANIENSOL IEX",
"Oil, Gas & Coal":"RELIANCE ONGC OIL BPCL HINDPETRO MRPL CASTROLIND ATGL IRMENERGY COALINDIA",
"Metals & Mining":"TATASTEEL JSWSTEEL SAIL HINDALCO VEDL HINDZINC HINDCOPPER",
"Pharma & Healthcare":"DRREDDY SUNPHARMA CIPLA AUROPHARMA DIVISLAB GLAND GRANULES LAURUSLABS GLENMARK APOLLOHOSP NH FISCHER",
"Banks":"HDFCBANK ICICIBANK SBIN AXISBANK KOTAKBANK INDUSINDBK BANDHANBNK",
"NBFC & Insurance":"BAJFINANCE SHRIRAMFIN JIOFIN HDFCLIFE ICICIPRULI MFSL NIACL POLICYBZR",
"Capital Markets":"BSE MCX CDSL CAMS GROWW",
"Auto & Auto Components":"MARUTI M&M TMPV BAJAJ-AUTO HEROMOTOCO EICHERMOT ASHOKLEY ESCORTS OLAELEC ARE&M EXIDEIND BELRISE NRBBEARING KROSS",
"FMCG, Retail & Consumer":"HINDUNILVR ITC NESTLEIND TATACONSUM MARICO KRBL LTFOODS DMART TRENT TITAN ETERNAL MEESHO ASIANPAINT PIDILITIND BLUESTARCO",
"Chemicals":"GUJALKALI TATACHEM AETHER GULPOLY INDIAGLYCO DCMSHRIRAM GODREJIND",
"Agri, Fertilisers & Sugar":"PIIND UPL DHANUKA COROMANDEL CHAMBLFERT RCF FACT NFL EIDPARRY DALMIASUG",
"Logistics, Travel & Infra":"ADANIPORTS CONCOR IRCTC INDIGO SADHAV DREAMFOLKS ADANIENT ANANTRAJ AMBUJACEM",
}
sec={}
for s,l in SECT.items():
    for t in l.split(): sec[t]=s
stocks=[k for k in rows if not k.startswith('#')]
missing=[k for k in stocks if k not in sec]; print("unmapped",missing)
N=rows['#NIFTY']
clamp=lambda x:max(0,min(1,x))
DATAFLAG={"INDIAGLYCO":"3-way demerger effective 1 Sep 2026 — price history not adjusted; trend readings invalid",
 "VEDL":"5-way demerger (ex-date ~May 2026) — pre-demerger prices not adjusted; long-term readings invalid",
 "SPELS":"Only ~30 trading sessions of data available — too little history for a reliable read"}
out=[]
for k in stocks:
    d=rows[k]; g=lambda f:d[f] if d[f] is not None else 0
    rs1=g('r1m')-N['r1m']; rs3=g('r3m')-N['r3m']; rs6=g('r6m')-N['r6m']
    trend=(5*(g('d20')>0)+8*(g('d50')>0)+10*(g('d200')>0)+8*(g('s50v200')>0)+7*(g('s200slope')>0)+5*(g('s50slope')>0)+3.5*d['hh']+3.5*d['hl'])
    mom=(15*clamp((rs3+20)/40)+10*clamp((rs6+30)/60)+10*clamp((g('rsi')-30)/40)+5*(g('hist')>0)+3*(g('hist')>g('hist5'))+4*(g('dmi')>0)+3*(g('adx')>=25 and g('dmi')>0))
    score=round(trend+mom)
    up_struct = g('d200')>0 and g('s50v200')>0 and g('s200slope')>0
    tags=[]
    if k in DATAFLAG: bucket="Data caveat"
    elif up_struct and g('d50')>0 and rs3>=15 and g('rsi')>=55 and g('fromHi')>=-12: bucket="Strong momentum"
    elif up_struct and g('d50')>-6: bucket="Uptrend"
    else:
        down = g('d200')<0 and (g('s50v200')<0 or g('s200slope')<0)
        bad = sum([g('rsi')<40, g('adx')>=25 and g('dmi')<0, g('fromLo')<8, g('r1m')<-8, g('d50')<-5])
        if down and bad>=3: bucket="Avoid now"
        elif down: bucket="Downtrend"
        else: bucket="Sideways / correcting"
    if g('rsi')>=70 or (g('atrp') and g('d20')/g('atrp')>3.5) or g('d50')>25: tags.append("Extended — don't chase")
    if up_struct and g('d50')<0 and g('d200')>0: tags.append("Pullback in uptrend")
    if g('fromHi')>=-3: tags.append("Near 52w high")
    if g('fromLo')<=5: tags.append("Near 52w low")
    if g('adx')>=25 and g('dmi')<0: tags.append("Strong downtrend (ADX)")
    if g('vr')>=1.3 and g('chg1d')>0: tags.append("Volume expanding")
    if g('rsi')<=30: tags.append("Oversold")
    if d['bars']<250: tags.append("Listed < 1 yr")
    if g('r1w')<-30: tags.append("Event-driven crash")
    out.append(dict(t=k,n=d['name'],s=sec[k],px=d['px'],d1=d['chg1d'],w=d['r1w'],m=d['r1m'],q=d['r3m'],h=d['r6m'],y=d['r1y'],
        d20=d['d20'],d50=d['d50'],d200=d['d200'],rsi=d['rsi'],adx=d['adx'],dmi=d['dmi'],atr=d['atrp'],hi=d['fromHi'],lo=d['fromLo'],
        rs3=round(rs3,1),rs6=round(rs6,1),sc=score,tr=round(trend),mo=round(mom),b=bucket,tags=tags,sp=d['spark'],note=DATAFLAG.get(k,""),bars=int(d['bars'])))
from collections import Counter
print(Counter(o['b'] for o in out))
# sectors
secs=[]
for s in SECT:
    L=[o for o in out if o['s']==s and o['b']!="Data caveat"]
    if not L: continue
    med=lambda f:round(st.median([o[f] for o in L if o[f] is not None]),1)
    up=sum(o['b'] in("Strong momentum","Uptrend") for o in L); dn=sum(o['b'] in("Downtrend","Avoid now") for o in L)
    secs.append(dict(s=s,n=len(L),sc=round(st.mean(o['sc'] for o in L)),m=med('m'),q=med('q'),h=med('h'),y=med('y'),rsi=med('rsi'),
       up=up,dn=dn,breadth=round(100*sum(o['d200']>0 for o in L)/len(L)),b50=round(100*sum(o['d50']>0 for o in L)/len(L)),
       best=max(L,key=lambda o:o['sc'])['t'],worst=min(L,key=lambda o:o['sc'])['t']))
secs.sort(key=lambda x:-x['sc'])
for x in secs: print(x)
bench={k[1:]:dict(n=rows[k]['name'],px=rows[k]['px'],d1=rows[k]['chg1d'],w=rows[k]['r1w'],m=rows[k]['r1m'],q=rows[k]['r3m'],h=rows[k]['r6m'],y=rows[k]['r1y'],rsi=rows[k]['rsi'],d50=rows[k]['d50'],d200=rows[k]['d200'],hi=rows[k]['fromHi'],sp=rows[k]['spark']) for k in rows if k.startswith('#')}
json.dump(dict(stocks=out,sectors=secs,bench=bench,asof="2026-09-30"),open('data.json','w'),separators=(',',':'))
for b in ["Strong momentum","Uptrend","Avoid now","Data caveat"]:
    L=sorted([o for o in out if o['b']==b],key=lambda o:-o['sc'])
    print("\n==",b,len(L)); print(", ".join(f"{o['t']}({o['sc']},q{o['q']},rsi{o['rsi']:.0f})" for o in L))
L=sorted([o for o in out if o['b']=="Downtrend"],key=lambda o:o['sc']); print("\n== Downtrend",len(L)); print(", ".join(o['t'] for o in L))
L=sorted([o for o in out if o['b']=="Sideways / correcting"],key=lambda o:-o['sc']); print("\n== Sideways",len(L)); print(", ".join(f"{o['t']}({o['sc']})" for o in L))
