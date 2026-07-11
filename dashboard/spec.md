# Dashboard spec (Part 3)

## Questions this dashboard answers

1. **What annual naming-rights fee should Chiba Lotte ask for the new stadium?** — a conservative / base / upside range, in JPY and USD.
2. **Is that range grounded in real comparables, or made up?** — shown against the actual global size-matched ballpark distribution the range comes from.
3. **Why isn't the answer just "what Japan pays today"?** — today's Japan level (ZOZO Marine + the Japan estimate rows) shown against the global-standard estimate, making the convergence-upside gap visible. This is the core business argument for the ask.
4. **What would the same engine recommend for a different venue?** — capacity and venue type are inputs, not hard-coded; Chiba Lotte (33,000, Ballpark) is the preset, not the only case the tool can answer.

## Audience

- **Primary: the Chiba Lotte Marines business office**, deciding what to ask a sponsor for the new stadium's naming rights. Naming rights are a core piece of financing the ¥65B stadium, so this is a price-justification tool for an internal/negotiation decision, not a research report.
- **Secondary (noted in-app, not the primary design target): a candidate sponsor**, using the same numbers to judge whether an asking price is fair. The UI carries one line making this explicit, but the tool is not restructured around it — every number the sponsor needs is already visible to the primary audience.

## Filters / slices

- **Currency toggle:** JPY (default) / USD, applied to every dollar figure on the page at once (one axis, one currency at a time — never both simultaneously on the same chart).
- **Capacity input:** number input, default 33,000 (Chiba Lotte preset).
- **Venue type input:** selectbox (Ballpark / Stadium / Arena / Other), default Ballpark.
- Changing capacity/venue type recomputes the "generalizable engine" section only — the headline Chiba Lotte numbers and the Japan-vs-global chart stay pinned to the actual Chiba Lotte case regardless of what the user types in the explorer.

## What's read from where (no hard-coded numbers)

| Section | Source |
|---|---|
| Headline range (conservative/base/upside) | `analysis.chiba_lotte_valuation_v2_summary` (ratio method) + `analysis.chiba_lotte_regression_prediction` (cross-check) |
| Benchmark distribution | `analysis.naming_rights_analysis_ready` (all rows, cached once) |
| Japan-vs-global | `analysis.chiba_lotte_japan_reference_v2` + the same v2 summary |
| Generalizable engine | recomputed in-app from the cached `naming_rights_analysis_ready` row-level data (no re-query per interaction — see "Verify: performance") |

All reads go through `st.cache_data`; BigQuery is hit once per cache period (default TTL 1 hour), not once per user interaction or widget change.

## Verify targets

1. **Load-time target:** first paint (data fetched, headline numbers rendered) in **under 3 seconds** on a warm cache, measured via `curl -w "%{time_total}"` against the deployed Cloud Run URL after the first request has warmed the container and Streamlit's cache.
2. **Correctness check:** the headline base figure shown in the app must match `analysis.chiba_lotte_valuation_v2_summary`'s `median_fee_per_seat * target_capacity` for the size-band tier, to the dollar (spot-checked by hand against a direct BigQuery query, not just "looks right").
3. **Public-reach test:** the deployed Cloud Run URL loads with **no authentication prompt**, from a plain unauthenticated `curl`/browser request (`--allow-unauthenticated`), confirming the "public, no-login" requirement actually holds, not just that it deploys.
4. **Clarity bar:** every chart carries a one-sentence plain-English claim rendered *in* the chart itself (title or annotation) — not only in surrounding prose — checked by reading each chart with the surrounding text hidden and confirming the claim still stands alone.

## Design notes (dataviz skill)

- Palette: the skill's validated default categorical set (`#2a78d6` blue, `#1baf7a` aqua, `#eda100` yellow, `#008300` green, `#4a3aa7` violet, `#e34948` red, `#e87ba4` magenta, `#eb6834` orange) — validated via `scripts/validate_palette.js` (all checks pass; contrast WARN on aqua/yellow/magenta means those slots always carry a visible direct label, never small text in a low-contrast fill).
- One axis per chart — no dual-axis JPY/USD overlay; the currency toggle re-renders the same chart in one currency at a time.
- Every chart's one-sentence claim is a title/annotation, not a caption below the figure.
