#!/usr/bin/python3
# =============================================================================
# _basic_common.py — shared helpers for Blaque Baux BASIC (convertible arb & capital-structure RV).
# Alpaca SIP daily bars (adjustment=all → TOTAL return, coupons/distributions counted); read-only.
#
# BASIC fills a classic hedge-fund white space the corpus never touched: CONVERTIBLE ARBITRAGE and
# CAPITAL-STRUCTURE relative value ("nothing added, just the classic take"). The canonical trade is long the
# convertible bond, DELTA-HEDGED short the underlying equity — isolating the embedded cheap vol + the carry,
# neutral to equity direction. The ETF proxy: long a convertibles fund (CWB/ICVT/FCVT), short a causal rolling
# beta of SPY → the hedged residual IS the arb premium. Cap-structure RV is the sibling: long credit
# (HYG/LQD), short equity-beta → the credit residual. The honest frame: convert arb earns a modest premium for
# selling cheap vol + bearing LIQUIDITY risk — a real edge with a fat left tail in funding crises (2008, 2020),
# the mirror of the vol-selling family (brace/bushel). And a true caveat: the ETFs launched AFTER 2008, so the
# canonical convert-arb catastrophe is OUT of sample — the measured tail UNDERSTATES the real one.
# =============================================================================
import os, json, urllib.request, math
import numpy as np

H = {"APCA-API-KEY-ID": os.environ["ALPACA_KEY_ID"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
START, END = "2016-01-01", "2026-08-01"
_cache = {}

def bars(s):
    if s in _cache: return _cache[s]
    u = (f"https://data.alpaca.markets/v2/stocks/bars?symbols={s}&timeframe=1Day"
         f"&start={START}&end={END}&adjustment=all&feed=sip&limit=10000")
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40))
        _cache[s] = {b["t"][:10]: b["c"] for b in d.get("bars", {}).get(s, [])}
    except Exception:
        _cache[s] = {}
    return _cache[s]

def panel(syms):
    D = {s: bars(s) for s in syms}; D = {s: v for s, v in D.items() if len(v) > 250}
    if not D: return {}, []
    u = list(D); dates = sorted(set.intersection(*[set(D[s]) for s in u]))
    return {s: np.array([D[s][d] for d in dates], float) for s in u}, dates

def rets(px): return px[1:] / px[:-1] - 1

def stats(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 30 or r.std() == 0: return dict(sh=float('nan'), cagr=float('nan'), dd=float('nan'), vol=float('nan'))
    cum = np.cumprod(1 + r)
    return dict(sh=r.mean()/r.std()*math.sqrt(252), cagr=cum[-1]**(252/len(r))-1,
                dd=(cum/np.maximum.accumulate(cum)-1).min(), vol=r.std()*math.sqrt(252))

def jarque_bera(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]; n = len(r)
    if n < 30 or r.std() == 0: return dict(jb=float('nan'), p=float('nan'), skew=float('nan'), exkurt=float('nan'))
    z = (r - r.mean())/r.std(); sk = float(np.mean(z**3)); ku = float(np.mean(z**4)-3.0)
    jb = n/6.0*(sk**2 + ku**2/4.0)
    return dict(jb=jb, p=math.exp(-jb/2.0), skew=sk, exkurt=ku)

def jensens_alpha(r, rb, rf=0.0):
    r = np.asarray(r, float); rb = np.asarray(rb, float); m = np.isfinite(r) & np.isfinite(rb); r, rb = r[m], rb[m]
    if len(r) < 30 or np.var(rb) == 0: return dict(alpha_ann=float('nan'), beta=float('nan'))
    beta = float(np.cov(r, rb)[0, 1]/np.var(rb))
    return dict(alpha_ann=(r.mean() - beta*rb.mean())*252, beta=beta)

def m_squared(r, rb, rf=0.0):
    r = np.asarray(r, float); rb = np.asarray(rb, float); r = r[np.isfinite(r)]; rb = rb[np.isfinite(rb)]
    if len(r) < 30 or r.std() == 0 or rb.std() == 0: return dict(m2_excess=float('nan'))
    shp = r.mean()/r.std()*math.sqrt(252); shb = rb.mean()/rb.std()*math.sqrt(252)
    return dict(m2_excess=(shp - shb)*rb.std()*math.sqrt(252))

def riskadj(r, rb, rf=0.0):
    out = dict(stats(r)); out.update(jarque_bera(r)); out.update(jensens_alpha(r, rb, rf)); out.update(m_squared(r, rb, rf))
    return out

def delta_hedge(r, rb, win=60):
    """CAUSAL delta-hedge: at each day use the trailing-`win` beta (estimated through yesterday) to short the
    hedge leg. residual_t = r_t − beta_{t-1}·rb_t. Returns (residual, mean beta) aligned to r[win:]."""
    r = np.asarray(r, float); rb = np.asarray(rb, float); m = min(len(r), len(rb)); r, rb = r[-m:], rb[-m:]
    out = []; betas = []
    for t in range(win, m):
        w_r, w_b = r[t-win:t], rb[t-win:t]           # trailing window, strictly before t
        b = float(np.cov(w_r, w_b)[0, 1] / np.var(w_b)) if np.var(w_b) > 0 else 0.0
        betas.append(b); out.append(r[t] - b * rb[t])
    return np.array(out), float(np.mean(betas)) if betas else float('nan')
