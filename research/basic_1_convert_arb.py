#!/usr/bin/python3
# =============================================================================
# basic_1_convert_arb.py — does convertible arb / capital-structure RV earn a premium, or just bear hidden beta?
#
# All TOTAL return, causal, vs SPY. Three legs:
#  (A) CONVERTIBLES AS AN ASSET CLASS — CWB/ICVT/FCVT vs SPY: convexity (upside participation, downside cushion)
#      or just equity+credit beta? Beta, skew, M². A convertible is debt + an embedded equity call; unhedged,
#      most of the return is beta — the question is whether the embedded option adds risk-adjusted value.
#  (B) CONVERTIBLE ARB (the real trade) — long CWB, CAUSAL rolling-beta delta-hedge short SPY. The hedged
#      residual isolates the embedded CHEAP VOL + carry, neutral to equity direction. Does it earn, and what is
#      the CRISIS tail (COVID 2020 = the in-sample funding/liquidity stress)? Convert arb sells cheap vol and
#      bears liquidity risk — a modest premium with a fat left tail, the mirror of the vol-selling family.
#  (C) CAPITAL-STRUCTURE RV — long credit (HYG high-yield, LQD IG), delta-hedged short SPY. The credit residual:
#      a harvestable credit-risk premium net of equity beta, or just more equity in a bond wrapper?
# HONEST CAVEAT: these ETFs launched AFTER 2008, so the canonical convert-arb catastrophe is OUT of sample —
# the measured left tail UNDERSTATES the true one. Read the crisis column as a floor on the risk, not the worst.
# =============================================================================
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _basic_common import panel, rets, riskadj, stats, delta_hedge
import numpy as np

P, dates = panel(["SPY", "CWB", "ICVT", "FCVT", "HYG", "LQD"])
R = {s: rets(P[s]) for s in P}; D = dates[1:]; spy = R["SPY"]
print("="*98); print(f"BASIC #1 — convertible arb & capital-structure RV  ({dates[0]} → {dates[-1]}, {len(dates)} days)"); print("="*98)

def crisis_sh(r):                                  # COVID 2020 funding/liquidity stress (in-sample)
    n = len(r); d = D[-n:]
    mk = np.array(["2020-02" <= x < "2020-05" for x in d])
    sub = r[mk]; return (sub.mean()/sub.std()*np.sqrt(252)) if sub.std() > 0 else float('nan'), (np.cumprod(1+sub).min()/np.cumprod(1+sub)[0]-1 if len(sub) else float('nan'))

# ---- (A) convertibles as an asset class -------------------------------------------------------------
print(f"\n(A) CONVERTIBLES vs SPY             {'Sharpe':>8}{'CAGR':>8}{'maxDD':>8}{'β/SPY':>7}{'skew':>7}{'M²exc':>8}")
for s in ["CWB","ICVT","FCVT"]:
    if s not in R: print(f"  {s:5} — absent"); continue
    a = riskadj(R[s], spy[-len(R[s]):])
    print(f"  {s:5} convertibles       {a['sh']:>+8.2f}{a['cagr']*100:>+7.1f}%{a['dd']*100:>+7.0f}%{a.get('beta',float('nan')):>+7.2f}{a['skew']:>+7.2f}{a['m2_excess']*100:>+7.1f}%")
spa = stats(spy); print(f"  SPY   index              {spa['sh']:>+8.2f}{spa['cagr']*100:>+7.1f}%{spa['dd']*100:>+7.0f}%{1.0:>+7.2f}")

# ---- (B) convertible ARB: delta-hedged residual -----------------------------------------------------
print(f"\n(B) CONVERTIBLE ARB (long CWB − βSPY, causal)   {'Sharpe':>8}{'CAGR':>8}{'maxDD':>8}{'skew':>7}{'exKurt':>8}{'~β':>6}")
arb, bmean = delta_hedge(R["CWB"], spy)
aA = riskadj(arb, spy[-len(arb):]); c_sh, c_dd = crisis_sh(arb)
print(f"  hedged residual (the arb premium)            {aA['sh']:>+8.2f}{aA['cagr']*100:>+7.1f}%{aA['dd']*100:>+7.0f}%{aA['skew']:>+7.2f}{aA['exkurt']:>+8.1f}{bmean:>+6.2f}")
print(f"    COVID-2020 stress: Sharpe {c_sh:+.2f}, trough {c_dd*100:+.0f}%  (the in-sample liquidity tail)")

# ---- (C) capital-structure RV: credit residual ------------------------------------------------------
print(f"\n(C) CAP-STRUCTURE RV (long credit − βSPY)       {'Sharpe':>8}{'CAGR':>8}{'maxDD':>8}{'skew':>7}{'~β':>6}")
cred = {}
for s in ["HYG","LQD"]:
    res, bm = delta_hedge(R[s], spy); ra = riskadj(res, spy[-len(res):]); cred[s] = ra
    lab = "high-yield" if s=="HYG" else "investment-grade"
    print(f"  {s:4} {lab:16} residual  {ra['sh']:>+8.2f}{ra['cagr']*100:>+7.1f}%{ra['dd']*100:>+7.0f}%{ra['skew']:>+7.2f}{bm:>+6.2f}")

# ---- verdict ----------------------------------------------------------------------------------------
arb_earns   = aA['sh'] > 0.3 and aA['cagr'] > 0.01
arb_tailed  = aA['skew'] < -0.5 or (np.isfinite(c_dd) and c_dd < -0.08)   # fat left tail / crisis crater
hy_earns    = cred.get("HYG",{}).get('sh',0) > 0.3
print("\n"+"="*98); print("READ:")
print(f"  • CONVERTIBLES unhedged are ~{riskadj(R['CWB'],spy[-len(R['CWB']):]).get('beta',0):.2f}-beta equity in a bond wrapper — the embedded call gives some")
print("    convexity but most of the line is just SPY + credit; as an asset class it doesn't beat the index risk-adjusted.")
cwb_dd = riskadj(R['CWB'], spy[-len(R['CWB']):])['dd']
print(f"  • CONVERT ARB (delta-hedged) residual Sharpe {aA['sh']:+.2f} — {'a real modest premium (cheap vol + carry)' if arb_earns else 'does not clear the bar once equity beta is hedged out'}")
print(f"    and the hedge makes it WORSE: residual maxDD {aA['dd']*100:+.0f}% vs CWB's own {cwb_dd*100:+.0f}% unhedged — a lagged ETF-level")
print(f"    beta hedge misfires in fast crises (COVID trough {c_dd*100:+.0f}%, exKurt {aA['exkurt']:+.1f}), the opposite of protection.")
print(f"  • CAP-STRUCTURE: the hedged HY-credit residual Sharpe {cred.get('HYG',{}).get('sh',float('nan')):+.2f} — the credit-risk premium net of equity beta;")
print("    IG is thinner. Credit RV is real but small and shares the same crisis-correlated tail as the arb.")

if arb_earns and arb_tailed:
    v = ("CONDITIONAL: convertible arb is a REAL premium — the delta-hedged residual earns (cheap embedded vol + "
         "carry) where unhedged converts are just beta. BUT it is insurance-selling in disguise: a fat left tail "
         "that detonates in funding/liquidity crises, and 2008 (the canonical blowup) is OUT of sample so the true "
         "tail is worse than measured. Size it tiny as risk, gate on liquidity/credit stress — the mirror of "
         "brace/bushel on the credit side. Cap-structure credit RV is the smaller sibling, same tail.")
elif arb_earns:
    v = ("CONDITIONAL: the delta-hedged convert-arb residual earns a modest premium net of equity beta; tail muted "
         "in this sample but 2008 is out of window — treat the liquidity risk as understated. A niche RV carry.")
else:
    v = ("NULL-ish: once you hedge the equity beta, neither convertibles nor the credit cap-structure trade leaves a "
         "premium worth the liquidity tail — the return was beta. The classic arb needs issuer-level converts + true "
         "delta/vega hedging (a basic_2), not ETF proxies; the ETF look says the packaged version is beta + a crash risk.")
print(f"\n  VERDICT: {v}")
print("  (ETF proxies hedge only the INDEX delta — real convert arb hedges each issuer's equity + vega + credit and")
print("   earns the cheap-vol/liquidity premium at the name level. That issuer-level construction is a basic_2.)")
