# Blaque Baux Basic

**Convertible arb & capital-structure RV — the classic hedge-fund trade, taken plain. Via ETFs: beta plus a crash risk.**

Basic fills a white space the corpus never touched: **convertible arbitrage** and **capital-structure relative
value** — "nothing added, just the classic take." The canonical trade is long the convertible bond, delta-hedged
short the underlying equity, isolating the cheap embedded vol and the carry. The honest first pass runs it with
ETF proxies — and finds the packaged version is mostly equity beta wearing a bond wrapper, with a liquidity tail
you don't get paid for.

> **Not investment advice.** Educational/research software. See [DISCLAIMER](DISCLAIMER.md) and [LICENSE](LICENSE).

```bash
python3 research/basic_1_convert_arb.py   # needs Alpaca data keys in the environment
```

## The finding (honest null)

[`research/basic_1_convert_arb.py`](research/basic_1_convert_arb.py) — all total return, causal, vs SPY.

**(A) Convertibles as an asset class** (CWB/ICVT/FCVT) are ~0.68-beta equity:

| fund | Sharpe | CAGR | maxDD | β/SPY | M² exc |
|---|---|---|---|---|---|
| CWB | +0.84 | +11.8% | −32% | 0.68 | −0.7% |
| ICVT | +0.82 | +12.4% | −33% | 0.68 | −1.1% |
| FCVT | +0.68 | +10.8% | −32% | 0.63 | −3.6% |
| SPY | +0.88 | +15.0% | −34% | 1.00 | — |

The embedded call adds a little convexity, but risk-adjusted they sit *just under* the index — it's SPY + credit.

**(B) Convertible arb** (long CWB, causal rolling-beta delta-hedge short SPY) — the hedged residual is supposed to
be the premium. It isn't: **Sharpe +0.19, +1.2%/yr**, and the hedge makes the tail *worse* — residual **maxDD −36%
vs CWB's own −32% unhedged**, excess kurtosis +11.9, COVID-2020 trough −14%. A lagged ETF-level beta hedge
misfires in fast crises: the opposite of protection.

**(C) Capital-structure RV** (long HYG/LQD credit, delta-hedged short SPY): the HY-credit residual Sharpe is
−0.03, IG +0.10 — no premium left once equity beta is hedged out.

## Verdict

**NULL-ish — the ETF-packaged version is beta plus a crash risk.** Once you hedge the equity, neither convertibles
nor the credit cap-structure trade leaves a premium worth the liquidity tail. And the honest caveat matters: these
ETFs launched *after* 2008, so the canonical convert-arb catastrophe (the funding/liquidity dislocation that broke
the strategy) is **out of sample** — the measured tail understates the real one. The classic arb earns its cheap-vol
and liquidity premium only at the **issuer level** — hedging each name's equity, vega, and credit — which ETFs can't
replicate. That construction is a `basic_2`; the ETF look says the shrink-wrapped version is not it.

## Status

**Research.** Honest null — a mapped-and-closed white space, in the family tradition where the red scorecard is the
point (and where a hedge that *adds* drawdown is exactly the kind of result worth publishing). Fat-tail scorecard
(Sharpe / CAGR / maxDD / skew / excess-kurtosis / β / M²), causal rolling-beta delta-hedge, Alpaca SIP daily total
return. No live capital.
