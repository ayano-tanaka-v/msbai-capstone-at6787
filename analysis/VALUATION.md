# Chiba Lotte Marines New Stadium — Naming-Rights Valuation (v2: Global Basis)

**Method:** comparables (ratio) — fee-per-seat from real comparable deals, applied to the new stadium's capacity. **Still no regression cross-check** — that's the next step. **No market-size adjustment either, by design in this version** — see "Change of approach" below.

**Target:** Chiba Lotte Marines New Stadium (planned, Makuhari, Chiba — Greater Tokyo), NPB Pacific League, **33,000-seat outdoor ballpark**, opening targeted ~2034.

---

## Change of approach: v1 → v2

**v1** (previous pass) anchored the valuation on Japan/regional comparables and treated the current ZOZO Marine deal as a hard floor the estimate could not fall below.

**v2 supersedes that.** Decision: **do not discount for Japan's regional market.** Japan's naming-rights market is currently priced below global levels but is converging upward — so this version values the venue's **global-standard potential** (what a 33,000-seat modern ballpark commands worldwide), not what the local Japanese market pays today. Concretely:

- The comparable set is now **global OBSERVED ballparks, not segmented by country** — Japan rows are on the same footing as every other country's, neither excluded nor down-weighted.
- Segmentation is by **venue type and capacity size only** (ballpark; a 25,000–45,000 capacity band as the closest size peers), never by region.
- The ZOZO Marine floor is **kept only as a sanity check**, not a binding constraint. Where the global estimate sits above it, that gap **is the story** — the convergence upside this valuation is built to surface, not a discrepancy to correct.

v1's SQL is preserved at `sql/analysis/chiba_lotte_valuation_v1.sql` for reference; this document fully replaces it.

---

## Headline range (v2, global basis)

| | Annual naming-rights fee | vs. today's ZOZO Marine deal (¥400M / $2.67M) |
|---|---|---|
| **Conservative** (p25, size-matched global ballparks) | **¥217M (~$1.45M)** | 46% *below* |
| **Base** (median, size-matched global ballparks) | **¥482M (~$3.22M)** | 20% *above* |
| **Upside** (p75, size-matched global ballparks) | **¥1,296M (~$8.66M)** | 224% *above* |

(JPY at ¥149.66/$1 — the 2025 actual FX rate, carried forward to 2026 — see "Key uncertainties.")

**Read plainly:** the base and upside cases — the median and upper end of what similarly-sized ballparks worldwide actually charge — sit meaningfully **above** today's Japan-market deal, which is the convergence-upside case this valuation is built to make. The conservative end does **not** clear the floor: the bottom quartile of the global size-matched comparable set includes lower-fee markets and is genuinely below what Chiba Lotte already earns today. That's reported honestly below, not smoothed away — see "Where the range sits vs. the floor."

---

## The two global distributions

Every comparable is a real, disclosed (`OBSERVED`) ballpark naming-rights deal, from any country, normalized to real-2024-USD — no estimates, no target row, no sub-$10k data-entry-error rows. `fee_per_seat_real2024 = annual_fee_usd_real2024 / capacity`. Neither distribution below excludes or down-weights Japan; Japan rows simply appear wherever their own numbers place them.

### All global ballparks (n = 63, every country)

| Stat | $/seat | Implied fee @ 33,000 seats |
|---|---|---|
| Min | $3.62 | $0.12M |
| p25 | $35.78 | $1.18M (¥177M) |
| **Median** | **$75.26** | **$2.48M (¥372M)** |
| p75 | $143.84 | $4.75M (¥710M) |
| p90 | $296.41 | $9.78M (¥1,464M) |
| Max (Citi Field, USA — outlier) | $697.57 | $23.02M |

This full-size set includes many small minor-league ballparks (a few thousand seats) that pull the low end down — useful as the broadest reference, but the size-band below is the closer size match to a 33,000-seat venue.

### Global ballparks, 25,000–45,000 capacity (n = 19 — closest size peers)

The comparable rows driving this distribution, low to high:

| Venue | Country | Capacity | Contract start | $/seat |
|---|---|---|---|---|
| PNC Park | USA | 38,747 | 2021 | $8.96 |
| InfoCision Stadium-Summa Field | USA | 30,000 | 2011 | $34.86 |
| Gesa Field at Martin Stadium | USA | 32,952 | 2022 | $35.78 |
| Cajun Field at Our Lady of Lourdes Stadium | USA | 30,000 | 2021 | $38.59 |
| **Rakuten Mobile Saikyo Park Miyagi** | **Japan** | 30,508 | 2026 | $44.02 |
| Rate Field | USA | 40,615 | 2017 | $48.52 |
| John O'Quinn Field at TDECU Stadium | USA | 40,000 | 2025 | $50.00 |
| Petco Park | USA | 40,000 | 2021 | $86.82 |
| **ZOZO Marine Stadium** | **Japan** | 29,645 | 2026 | $90.16 |
| Comerica Park | USA | 41,083 | 2000 | $97.55 |
| Great American Ball Park | USA | 42,319 | 2003 | $100.74 |
| American Family Field | USA | 41,900 | 2021 | $110.52 |
| Citizens Bank Park | USA | 42,901 | 2005 | $142.28 |
| Dignity Health Sports Park | USA | 27,000 | 2021 | $257.26 |
| Daikin Park | USA | 41,168 | 2000 | $262.40 |
| Truist Park | USA | 41,149 | 2018 | $303.59 |
| Globe Life Field | USA | 40,300 | 2021 | $315.98 |
| Oracle Park | USA | 41,915 | 2020 | $469.89 |
| Citi Field | USA | 41,922 | 2009 | $697.57 |

Japan's two ballparks sit squarely in the **lower-middle** of this size-matched set (5th and 9th of 19 by $/seat) — not artificially depressed, not exceptional, just where they actually fall among global peers of similar size.

| Stat | $/seat | Implied fee @ 33,000 seats |
|---|---|---|
| Min (PNC Park) | $8.96 | $0.30M |
| **p25 (conservative)** | **$44.02** | **$1.45M (¥217M)** |
| **Median (base)** | **$97.55** | **$3.22M (¥482M)** |
| **p75 (upside)** | **$262.40** | **$8.66M (¥1,296M)** |
| p90 (stretch reference, not part of the 3-point range) | $469.89 | $15.51M (¥2,321M) |
| Max (Citi Field — outlier) | $697.57 | $23.02M |

The headline range above uses this size-matched distribution as the primary basis, since it's the closer size peer group to a 33,000-seat venue than the full 63-park global set.

---

## Where the range sits vs. the floor and today's Japan level

| | $/seat | Implied @ 33k | vs. ZOZO floor ($2.67M) |
|---|---|---|---|
| All-ballparks p25 | $35.78 | $1.18M | 56% below |
| All-ballparks median | $75.26 | $2.48M | 7% below (essentially at parity) |
| All-ballparks p75 | $143.84 | $4.75M | 78% above |
| All-ballparks p90 | $296.41 | $9.78M | 266% above |
| Size-band p25 (conservative) | $44.02 | $1.45M | **46% below** |
| Size-band median (base) | $97.55 | $3.22M | **20% above** |
| Size-band p75 (upside) | $262.40 | $8.66M | **224% above** |
| Size-band p90 (stretch) | $469.89 | $15.51M | 480% above |

**Honest reading:** the *base* and *upside* cases clear the current ZOZO Marine deal comfortably — that's the convergence upside. The *conservative* case does not, and shouldn't be forced to: it represents the bottom quartile of a global size-matched set, which genuinely includes lower-fee markets a 33,000-seat ballpark could land in if Japan's convergence doesn't play out favorably. Presenting a conservative case that's artificially floored at today's Japan level would hide that real downside scenario — so it isn't done here.

### Current Japan market — reference only, not part of the estimate

Both classifications, side by side, purely to make the gap visible (never mixed into the global tiers above):

| Venue | Class. | Capacity | $/seat | Implied @ 33k |
|---|---|---|---|---|
| Nissan Stadium | OBSERVED | 72,327 | $12.01 | $0.40M |
| Fukuda Denshi Arena / Soga Sports Park | OBSERVED | 19,781 | $16.89 | $0.56M |
| Noevir Stadium Kobe | ESTIMATE | 30,132 | $13.75 | $0.45M |
| EDION Peace Wing Hiroshima | OBSERVED | 28,520 | $23.16 | $0.76M |
| Ajinomoto Stadium | OBSERVED | 49,970 | $27.76 | $0.92M |
| Panasonic Stadium Suita | OBSERVED | 39,694 | $36.92 | $1.22M |
| **Rakuten Mobile Saikyo Park Miyagi** | OBSERVED | 30,508 | $44.02 | $1.45M |
| Yodoko Sakura Stadium | OBSERVED | 24,481 | $54.59 | $1.80M |
| Mizuho PayPay Dome Fukuoka | ESTIMATE | 40,062 | $98.94 | $3.27M |
| **ZOZO Marine Stadium** (Chiba Lotte's current home) | OBSERVED | 29,645 | $90.16 | $2.98M |
| GMO Arena Saitama | OBSERVED | 36,500 | $100.69 | $3.32M |
| ES CON Field Hokkaido | ESTIMATE | 35,000 | $162.16 | $5.35M |
| IG Arena | ESTIMATE | 17,000 | $196.53 | $6.49M |
| MUFG Stadium | ESTIMATE | 68,000 | $196.53 | $6.49M |
| Daiwa House Premist Dome | ESTIMATE | 41,484 | n/a | n/a — 2028 start, outside ref coverage |

Today's Japan market spans roughly $12–$197/seat across both classes; among the *actually disclosed* (OBSERVED) deals, ZOZO Marine ($90.16) and GMO Arena ($100.69) sit at the top — right around the global size-matched median ($97.55), but well below the global p75 ($262.40). (The two highest Japan figures, ES CON Field and IG Arena/MUFG Stadium at ~$162–$197/seat, are unverified media/analyst ESTIMATEs, not consummated contracts, so they carry less weight than the OBSERVED comparison above.) That gap between "what Japan's disclosed deals pay now" and "what similarly-sized ballparks earn globally at the upper end" is the convergence opportunity this v2 valuation targets.

---

## Key uncertainties (stated plainly)

1. **Size-band n = 19** is workable for p25/median but the p75 (and especially the p90 "stretch" figure) are driven by a handful of very high-fee US ballparks (Truist Park, Globe Life Field, Oracle Park, Citi Field) — a small change in which parks fall in the 25k–45k window would move the upper end of the range noticeably. Treat the upside figure as directionally right, not precise to the dollar.
2. **No market-size adjustment in this version, by design.** Tokyo metro's market size relative to the US metros in this comparable set isn't accounted for at all here — this version deliberately asks "what does a ballpark this size get, globally" rather than "what would Tokyo's market specifically support." A later pass may still want a market-size-adjusted variant alongside this one.
3. **Carried-forward FX/CPI for 2026.** Both Japan ballparks in the size-band (ZOZO Marine, Rakuten Park) are 2026-start contracts using the 2025 actual JPY rate (¥149.66/$1) carried forward, since 2026 isn't published yet (`value_basis = 'carried_forward'` in `ref.fx_rates`). If the actual 2026 yen moves materially, the JPY figures throughout this document shift with it — the USD figures do not, since both the Japan comparables and the target's own fee are computed in the same real-2024-USD base.
4. **No regression cross-check yet.** Still ratio-only, per CLAUDE.md's method — the cross-check comes next.
5. **The conservative case sits below today's ZOZO Marine deal, honestly.** This isn't smoothed over: a 33,000-seat ballpark's naming rights could plausibly land in the lower quartile of the global comparable set if convergence is partial or slow. The base/upside cases are where the convergence thesis actually pays off.
6. **This is a global-standard estimate, not a market forecast.** It answers "what does a ballpark like this earn, worldwide" — it does not model *when* or *whether* Japan's market actually converges to that level, or over what time horizon. That's a judgment call for whoever uses this range, not something the data can answer.

---

## What's next

- **Regression cross-check**: regress real-2024-USD fee on capacity (and, if useful, league tier), report out-of-sample error, and confirm it doesn't wildly disagree with this global ratio-based range.
- Decide whether a market-size-adjusted variant should sit alongside this global-standard estimate, or whether the global-standard framing stands on its own for the final deliverable.
