# Chiba Lotte Marines New Stadium — Naming-Rights Valuation (v1)

**Method:** simple comparables (ratio) — fee-per-seat from real comparable deals, applied to the new stadium's capacity. **No market-size adjustment and no regression cross-check yet** — those come in the next pass. This is the first complete answer, built to be checked and improved, not the final number.

**Target:** Chiba Lotte Marines New Stadium (planned, Makuhari, Chiba — Greater Tokyo), NPB Pacific League, **33,000-seat outdoor ballpark**, opening targeted ~2034.

---

## Headline range (first pass)

| | Annual naming-rights fee |
|---|---|
| **Conservative** | **¥400M (~$2.67M)** — floor: today's ZOZO Marine deal |
| **Base** | **¥445M (~$2.98M)** — ZOZO Marine's own $/seat rate, scaled to the bigger stadium |
| **Upside** | **¥710M (~$4.75M)** — North American ballpark upper-quartile $/seat, scaled to 33,000 seats |

(JPY at the latest available FX rate: ¥149.66/$1, the 2025 actual rate, carried forward to 2026 — see "Key uncertainties" below.)

**Why the range looks the way it does:** this reflects a real finding, not a rounding choice — see "The floor problem" section below. A plain average of Japanese comparables would have put the low end of this range *below* what Chiba Lotte's current stadium already earns, which doesn't hold up: a bigger, newer venue for the same team shouldn't rent its name for less than the old one does. The range above corrects for that; the raw, uncorrected tier math is shown in full so nothing is hidden.

---

## How this was built: three comparable tiers

Every comparable below is a real, disclosed (`OBSERVED`) naming-rights deal, normalized to real-2024-USD (see `clean.naming_rights_normalized` / `analysis.naming_rights_analysis_ready`) — no estimates, no the target row, and the $3/year data-entry-error row is already excluded. `fee_per_seat_real2024 = annual_fee_usd_real2024 / capacity`.

### Tier 1 — Japan OBSERVED ballparks (tightest anchor, n=2)

| Venue | Capacity | Contract start | $/seat (real-2024-USD) |
|---|---|---|---|
| Rakuten Mobile Saikyo Park Miyagi | 30,508 | 2026 | $44.02 |
| ZOZO Marine Stadium (Chiba Lotte's **current** home) | 29,645 | 2026 | $90.16 |

With only 2 comparables, "median/p25/p75" imply more precision than the data supports (BigQuery's approximate-quantile math on 2 points literally returns the *minimum* as both the 25th percentile and the median) — so the honest summary is the plain average and the two endpoints, not manufactured percentiles:

| Stat | $/seat | Implied fee @ 33,000 seats |
|---|---|---|
| Low (Rakuten Park) | $44.02 | $1.45M (¥217M) |
| **Average** | **$67.09** | **$2.21M (¥331M)** |
| High (ZOZO Marine) | $90.16 | $2.98M (¥445M) |

### Tier 2 — all Japan OBSERVED comparables (n=9)

Adds large stadiums and soccer venues to Tier 1:

| Venue | Type | Capacity | Contract start | $/seat |
|---|---|---|---|---|
| Nissan Stadium | Stadium | 72,327 | 2026 | $12.01 |
| Fukuda Denshi Arena / Soga Sports Park | Soccer stadium | 19,781 | 2026 | $16.89 |
| EDION Peace Wing Hiroshima | Soccer stadium | 28,520 | 2024 | $23.16 |
| Ajinomoto Stadium | Stadium | 49,970 | 2024 | $27.76 |
| Panasonic Stadium Suita | Soccer stadium | 39,694 | 2023 | $36.92 |
| Rakuten Mobile Saikyo Park Miyagi | Ballpark | 30,508 | 2026 | $44.02 |
| Yodoko Sakura Stadium | Soccer stadium | 24,481 | 2026 | $54.59 |
| ZOZO Marine Stadium | Ballpark | 29,645 | 2026 | $90.16 |
| GMO Arena Saitama | Arena | 36,500 | 2026 | $100.69 |

| Stat | $/seat | Implied fee @ 33,000 seats |
|---|---|---|
| p25 | $23.16 | $0.76M (¥114M) |
| Median | $36.92 | $1.22M (¥182M) |
| p75 | $54.59 | $1.80M (¥270M) |
| Max (GMO Arena) | $100.69 | $3.32M (¥497M) |

### Tier 3 — North American OBSERVED ballparks (statistical base, n=61)

The largest sample, used here **without** any market-size adjustment (Tokyo metro vs. the mix of US/Canada markets these deals come from) — that adjustment is next pass's job, so treat this tier as an unadjusted upper reference for now, not a like-for-like comp.

| Stat | $/seat | Implied fee @ 33,000 seats |
|---|---|---|
| Min (Bank of Sun Prairie Stadium) | $3.62 | $0.12M |
| p25 | $35.78 | $1.18M (¥177M) |
| Median | $75.26 | $2.48M (¥372M) |
| p75 | $143.84 | $4.75M (¥710M) |
| Max (Citi Field — outlier) | $697.57 | $23.02M |

---

## The floor problem — a real finding, flagged not hidden

CLAUDE.md's guardrail: the new stadium's fee **should not fall below** the current ZOZO Marine deal (¥400M / **$2,672,762 real-2024-USD**, per the corrected raw data), since the new venue is larger (33,000 vs. 29,645 seats) and newer.

**Checking the raw tier math against that floor:**

| Estimate | Value | Clears the $2.67M floor? |
|---|---|---|
| Tier 2 p25 | $0.76M | ❌ No — 71% below floor |
| Tier 2 median | $1.22M | ❌ No — 54% below floor |
| Tier 1 average | $2.21M | ❌ No — 17% below floor |
| Tier 2 p75 | $1.80M | ❌ No — 33% below floor |
| Tier 3 p25 | $1.18M | ❌ No — 56% below floor |
| Tier 1 high (ZOZO's own rate, scaled) | $2.98M | ✅ Yes |
| Tier 3 median | $2.48M | ❌ No — 7% below floor (barely) |
| Tier 3 p75 | $4.75M | ✅ Yes |

**Flag:** most of the raw, unadjusted tier percentiles — including the Tier 1 average and every Tier 2 statistic — sit *below* today's ZOZO Marine deal. This is because ZOZO Marine's own newly-corrected rate ($90.16/seat) is actually the *high* end of the Japan comparable set, not its middle: Rakuten Park and the stadium/soccer comparables in Tier 2 all rent for less per seat. A straight "Japan-anchored median" would imply Chiba Lotte's brand-new, bigger stadium should earn *less* than their current one already does — which doesn't hold up economically and contradicts CLAUDE.md's explicit floor guardrail.

**Resolution used for the headline range above:** the conservative bound is pinned to the floor itself (not a raw percentile that undershoots it), and the base case uses ZOZO Marine's *own* $/seat rate scaled to the new stadium's larger capacity — the cleanest "same team, same market, bigger building" logic available from a single comparable. The upside uses Tier 3's p75, which comfortably clears the floor. This is a judgment call, stated plainly here rather than buried in a spreadsheet: **the next pass's market-size adjustment and regression cross-check should either confirm this resolution or give a better-grounded reason to move it.**

---

## Japan ESTIMATE rows — sanity reference only (NOT comparables)

These are `ESTIMATE`-classified rows (media estimates / Kroll-style figures, not consummated disclosed contracts) — shown side-by-side purely for triangulation, never mixed into the tiers above.

| Venue | Type | Own $/seat | Implied @ 33,000 seats |
|---|---|---|---|
| ES CON Field Hokkaido | Ballpark | $162.16 | $5.35M (¥801M) |
| Mizuho PayPay Dome Fukuoka | Ballpark | $98.94 | $3.27M (¥489M) |
| IG Arena | Arena | $196.53 | $6.49M (¥971M) |
| MUFG Stadium | Stadium | $196.53 | $6.49M (¥971M) |
| Noevir Stadium Kobe | Soccer stadium | $13.75 | $0.45M (¥68M) |
| Daiwa House Premist Dome | Stadium | n/a | n/a — 2028 contract start falls outside `ref.fx_rates`/`ref.us_cpi` coverage (2000–2026) |

**Read on triangulation:** the two ballpark-type estimates (ES CON Field, Mizuho PayPay Dome) bracket the headline range's upside comfortably above it ($5.35M and $3.27M vs. our $4.75M upside) — consistent with the base/upside range being reasonable rather than inflated, since even unverified estimate-grade figures for comparable Japanese ballparks land in the same neighborhood or higher.

---

## Key uncertainties (stated plainly)

1. **Very small Japan sample.** Tier 1 has only 2 comparables; Tier 2 has 9. Both ZOZO Marine and Rakuten Park (Tier 1) are themselves 2026-start contracts recovered by extending the reference tables — remove either one and the "Japan-anchored" numbers move a lot. This is the single biggest source of imprecision in this pass.
2. **Carried-forward FX/CPI for 2026.** 6 of the 9 Tier 2 rows (including both Tier 1 rows, ZOZO Marine and Rakuten Park) have a 2026 contract start year. World Bank hasn't published 2026 FX or CPI yet, so those rows use the latest **actual** 2025 value carried forward (flagged via `value_basis = 'carried_forward'` in `ref.fx_rates`/`ref.us_cpi` and `clean.naming_rights_normalized`). If the actual 2026 yen weakens or strengthens materially from 2025, every 2026-start figure in this document shifts with it.
3. **No market-size adjustment yet.** Tier 3 (North American ballparks) is shown completely unadjusted for market size — Tokyo metro is one of the largest media markets these teams play in, which this pass does not yet account for. Tier 3's numbers should be read as a rough upper reference, not a like-for-like comparable, until the next pass.
4. **No regression cross-check yet.** This entire pass is ratio-only. CLAUDE.md's method calls for a regression cross-check with reported out-of-sample error before the number is considered defensible — not done here.
5. **The floor resolution above is a judgment call**, clearly flagged, not a statistical output — see "The floor problem."
6. **ZOZO Marine's own rate is doing a lot of work.** Because the "base" case is anchored on a single comparable (ZOZO Marine's own newly-corrected deal), any future correction to that one row's fee or year would directly move the base case.

---

## What's next

- **Market-size adjustment**: bring in `SP.POP.TOTL` / `NY.GDP.MKTP.CD` (already scoped in CLAUDE.md section 1) to make the North American ballpark tier genuinely comparable to Tokyo metro, rather than an unadjusted reference.
- **Regression cross-check**: regress real-2024-USD fee on capacity, market size, and league tier; report out-of-sample error; confirm it doesn't wildly disagree with this ratio-based range.
- Revisit the floor resolution once both of the above are in, and confirm the same conclusion holds on firmer ground.
