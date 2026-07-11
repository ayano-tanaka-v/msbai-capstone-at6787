# DECISIONS.md

**What this document is:** a plain-language defense of the key choices behind this data product, for a non-technical reader — the Chiba Lotte Marines business office, and anyone else deciding what to do with this number. A decision you can't explain in plain terms is one you didn't really make. Every claim below is backed by a working artifact in this repo (the pipeline in `sql/`, the write-up in `analysis/VALUATION.md`, the live dashboard).

---

## 1. Why this data, and why this question

Chiba Lotte's new stadium costs roughly **¥65 billion** to build. Naming rights are one of the club's real ways to help pay for it — not a nice-to-have, a core revenue pillar. Before a club walks into a negotiation with a sponsor, it needs an answer to one question: **what should we ask for, and can we defend that number if a sponsor pushes back?**

That's the question this whole project answers. Everything here — the data collected, the comparisons built, the dashboard — exists to support that one real decision, not as an academic exercise.

- **Primary reader:** Chiba Lotte's business office, deciding what to ask.
- **Secondary reader:** a candidate sponsor, using the same public numbers to judge whether an asking price is fair. We designed for the first reader; the second gets the same transparency for free, because nothing here is hidden.

---

## 2. Why a global benchmark, not a Japan-discounted one

This is the single most consequential judgment call in the whole project, so it deserves to be stated plainly rather than buried in a spreadsheet.

**The choice:** we do **not** discount the estimate to match what Japanese naming-rights deals pay today. Instead, we price the stadium at **global-standard rates** — what a modern, similarly-sized ballpark commands anywhere in the world.

**Why:** Japan's naming-rights market is currently priced below the global market, but it is converging upward — recent Japanese deals (Rakuten Park, GMO Arena, ZOZO Marine's own renewed contract) are already climbing. A brand-new, larger, more modern stadium is exactly the kind of asset that should benchmark against where the market is heading, not where it's been. Pricing conservatively "because that's what Japan pays today" would leave real money on the table for a stadium literally being built to generate more of it.

This is a **deliberate stance, not a hidden assumption.** We don't ask the reader to just trust that Japan will catch up — the dashboard puts today's actual Japanese deals side-by-side with the global-standard estimate, so the size of that gap is visible, not asserted. We call it the **convergence upside**, and it's the central argument of this whole valuation.

---

## 3. What the headline number actually measures — and where it falls short

The headline metric is **fee per seat, in real-2024-USD** (i.e., inflation-adjusted so a 2010 contract and a 2025 contract are genuinely comparable), applied to Chiba Lotte's planned **33,000-seat** capacity.

**What it captures well:** it lets us compare a huge range of real, disclosed naming-rights deals — different countries, different currencies, different years — on one apples-to-apples basis, and scale that rate to Chiba Lotte's specific stadium size.

**What it does *not* capture, plainly:**
- **Capacity is only one driver of fee.** Our own regression shows capacity alone explains **under half** of why fees vary across venues (more on this in Section 5). A bigger stadium tends to command a bigger fee, but far from perfectly.
- **Per-seat rates vary enormously** even among similarly-sized ballparks — from a few dollars a seat to several hundred, depending on market, team prestige, and deal terms. The number we land on is a considered estimate from a wide, real range, not a precise formula output.
- **It doesn't yet account for market size** (Tokyo metro vs. a mid-size US market), media value, or the sport's local popularity. We tested adding market size and it didn't hold up (Section 5) — that's an honest gap, not a solved problem.

In short: this is a *grounded* estimate, built entirely from real comparable contracts — not a *precise* one. The range we give reflects that.

---

## 4. Why the answer is trustworthy

Four independent checks all point the same direction:

1. **Two different methods agree closely.** One method (a simple ratio, matching Chiba Lotte against similarly-sized ballparks worldwide) and a completely different method (a statistical regression, fit the same way but built on a fitted curve rather than direct comparison) land on **¥466M–¥482M (~$3.12M–$3.22M)** for the base case — within about **3% of each other**. Two unrelated approaches, built from the same real data but arriving independently, rarely land that close by accident.
2. **The estimate sits inside the real range**, not outside it. Every comparable behind this number is a real, disclosed naming-rights contract — not an estimate, not a projection. The base case isn't an extrapolation past what real deals show; it's squarely inside the distribution of what similarly-sized ballparks actually charge (visible directly on the dashboard).
3. **The ZOZO Marine floor sanity-checks it.** Chiba Lotte's own current home stadium deal (corrected figure: **¥400M**, ~$2.67M real-2024-USD — see Section 5) is a natural floor: a bigger, newer stadium for the same team shouldn't earn less than the current one. Our base and upside cases clear that floor comfortably.
4. **Every number is traceable, not asserted.** Every figure on the dashboard reads live from the same BigQuery tables backing this document — nothing is hand-typed or hardcoded. Anyone can check any number against the underlying data.

---

## 5. Where this is *not* trustworthy — stated honestly

A trustworthy analysis is one that tells you where it's weak, not just where it's strong.

- **The Japanese disclosed sample is very small: only 2 real NPB ballpark deals** (ZOZO Marine, Rakuten Park) meet our strict "actually disclosed, not an estimate" bar. Two data points move a lot if either one changes — this is the single biggest source of imprecision in the Japan-specific comparisons.
- **2026 exchange rates and US inflation figures are not yet real** — the actual 2026 numbers aren't published yet, so we carried forward the latest known values (2025 for currency, 2024 for inflation) and flagged every figure that relies on this explicitly in the underlying data. If those rates move meaningfully once published, the yen figures shift with them (the dollar figures do not, since everything is computed in dollars first).
- **The cross-check model's own accuracy is limited.** On data it's never seen before, its predictions are typically only accurate to within about **68%** in either direction, and it explains under half (~47%) of why fees vary venue to venue. That's a real, wide margin — useful for confirming our range isn't wildly off, not for pinpointing an exact number on its own.
- **We tried adjusting for market size (city GDP and population) and it didn't help — so we dropped it.** Adding it made the cross-check model's predictions *less* accurate on new data, not more, so we didn't keep a feature that looked good on paper but didn't actually improve the answer. (Likely reason: almost all our comparables are US venues, so a country-level economic figure barely varies from one to the next — it's too blunt an instrument. A city-level figure might do better in a future pass, but that's not built yet.)
- **We never mix real disclosed deals with estimates.** Some Japanese figures circulating publicly (like reported figures for ES CON Field or Mizuho PayPay Dome) are unverified media estimates, not confirmed contracts. We show them on the dashboard for context, but the actual valuation range is built only from consummated, disclosed deals — keeping a rumor from quietly becoming "data."
- **The source data itself has been corrected once already.** ZOZO Marine Stadium's own naming-rights figure was originally recorded as ¥310M (a 2016 deal) and was later corrected to ¥400M (a 2026 renewal) once better source data came in — every number derived from it was updated to match. Separately, one raw record (a "$3-per-year" contract that was obviously a data-entry error, not a real deal) was excluded from the comparable set entirely, and that exclusion is logged, not silently dropped.

None of this changes the recommended range — it's exactly why the range has a conservative and an upside end, rather than pretending to one precise number.

---

## 6. How this could be reused

The pricing engine behind this isn't hard-coded to Chiba Lotte. Enter any stadium's seat count and venue type, and it recomputes the same conservative/base/upside range from the same real global comparables — the dashboard's "price any venue" panel does exactly this, live. Chiba Lotte is the headline case this project was built to answer, but the same tool works for any club asking the same question about any venue.
