# CLAUDE.md — Naming Rights Valuation Data Product

> This file is the project's memory. Claude Code reads it at the start of every
> session. It records every decision **with a reason**. Decisions not written
> here are the ones the agent will make silently. Keep it up to date.

---

## 0. Project in one line

Build a **naming-rights benchmark database + valuation engine**: load global
disclosed naming-rights contracts, normalize them to one currency and price
level, and estimate a defensible **annual naming-rights fee** for a target venue.
The headline application (the showcase) is the **Chiba Lotte Marines new stadium**
(planned ~2034, Makuhari, NPB, ~33,000-seat outdoor ballpark). The engine is
**generalizable**: swap the target's inputs (capacity, league tier, venue type,
market) and it prices any venue.

- **Central question (kept sharp, we commit to an answer):** What is a defensible
  annual naming-rights fee (range) for the Chiba Lotte Marines new stadium?
- **Audience of the artifact:** the club's business office / a candidate sponsor's
  decision-maker (non-technical). Picture someone deciding what to bid/ask.
- **What a credible answer looks like (decided BEFORE computing):** a
  conservative / base / upside fee range, expressed per year, with the comparable
  set shown, a floor argument (should not fall below the current ZOZO Marine deal),
  and stated uncertainty. A model cross-check confirms the ratio result is not
  wildly off.

---

## 1. Data sources (raw layer)

### Internal (the naming-rights workbook)
One CSV per source, loaded **as-is** into raw tables (values untouched):

| Source ID prefix | What it is | ~Rows | Notes / quirks |
|---|---|---|---|
| SRC-SBJ   | Sports Business Journal directory extract | 589 | Bulk directory; ~half lack disclosed fees |
| SRC-KROLL | Kroll report extract (football club estimates) | 36 | **Estimates** — reference only, flag separately |
| SRC-ASIA  | Asia individual-venue extracts | 16 | Local-language names; per-row sources |
| SRC-TARGET| Chiba Lotte target case | 1 | **NOT an observation — exclude from benchmark** |

### External (public macro data — must be joined; this is the real ETL friction)
| Purpose | Source | Series / dataset | Granularity |
|---|---|---|---|
| FX (contract-year average) | World Bank | `PA.NUS.FCRF` (LCU per US$, period average, 1960–2024) | annual, by country/currency |
| Inflation to base year | FRED | `CPIAUCSL` (US CPI, all urban, all items) — annual mean | annual, US |
| Market size (baseline) | World Bank | `SP.POP.TOTL`, `NY.GDP.MKTP.CD`, income indicators | annual, by country |
| Market size (finer, optional) | US Census (MSA) + manual for key JP cities | Metropolitan Statistical Area population | metro area |

All external sources are free and key-less (FRED CSV gateway / World Bank REST).

---

## 2. Schema & grain

- **Grain:** one row = one venue naming-rights record (observed contract OR target).
- **Field definitions:** `reference/data_dictionary.csv` (100 fields).
- **Controlled vocabularies:** `reference/code_lists.csv`.
- **Row classification (never mix these):** `Data Type / Value Basis` +
  `Row Source Type` separate *actual disclosed* vs *estimate* vs *target*.
  - **Decision (recorded here since the source data doesn't fully pin it
    down):** `Data Type / Value Basis` is only populated for SRC-ASIA and
    SRC-TARGET (~3% of rows) — SRC-SBJ and SRC-KROLL leave it blank. The
    `clean.naming_rights_clean` view (`sql/clean/naming_rights_clean.sql`)
    therefore classifies every row as OBSERVED / ESTIMATE / TARGET using
    `Data Type / Value Basis` where populated, falling back to the Source
    ID prefix otherwise:
    - `Data Type / Value Basis` = 'Target valuation case', or prefix
      `SRC-TARGET` → **TARGET**
    - 'Actual disclosed' / 'Actual reported but partially disclosed' →
      **OBSERVED**
    - 'Media estimate' / 'Minimum asking price' → **ESTIMATE** (an asking
      price is not a consummated disclosed fee, so it's kept out of the
      disclosed-only benchmark)
    - Blank + prefix `SRC-KROLL` → **ESTIMATE** (per section 1: "football
      club estimates ... reference only")
    - Blank + prefix `SRC-SBJ` → **OBSERVED** (directory of disclosed
      contracts, not labeled an estimate)
    - Result: 599 OBSERVED, 42 ESTIMATE, 1 TARGET (642 total, 0 unclassified).

---

## 3. Normalization decisions (clean unified view)

Pipeline for every monetary value:
**raw original value (kept)** → **USD at contract-year average FX** → **real USD at
2026 price level (US CPI)** → *(display only)* **convert to selected currency**.

- **Base currency = USD.** All comparison and modeling done in real-2026 USD.
- **FX = contract START YEAR annual average** (World Bank `PA.NUS.FCRF`).
  - Currency→country mapping for the FX join: USD→USA, JPY→JPN, EUR→Euro area (XC),
    GBP→GBR, CAD→CAN, SGD→SGP. **(decision: record any additions here)**
- **Inflation:** rebase to **2026** using US CPI (`CPIAUCSL`).
- **Display currency is switchable** (USD default; JPY/EUR/…): apply the chosen
  currency's latest rate at the *presentation* step only — never recompute the base.
- **Raw original values are always preserved** for auditability and re-derivation.
- **Missing contract start year (~31 disclosed rows):** decision — fall back to
  Contract Announcement Date if present, else flag `year_basis = unverified` and
  exclude from year-sensitive normalization. **(confirm rule)**

---

## 4. Analysis-ready table & method

- **Analysis-ready grain:** one row per observed contract with: real-2026-USD
  annual fee, capacity, league tier, venue type, sport, country, market-size
  fields, and observed/estimate flag.
- **Method: comparables (ratio) as the spine; a simple regression as a cross-check.**
  - **Segmentation, not one global ratio** (the data shows fee-per-seat is highly
    dispersed): segment by **capacity band × league tier × venue type**, with a
    market-size adjustment.
  - **Comparable priority for Chiba Lotte:** (1) Japan/NPB ballparks & large
    stadiums — anchored on ZOZO Marine (current home), ES CON Field, Rakuten Park,
    Mizuho PayPay Dome; (2) North American ballparks, market-adjusted; (3) European
    football = reference only (do not mix estimates with disclosed).
  - **Cross-check model:** regress real-2026-USD annual fee on capacity, market
    size, league tier (log where sensible). Report **out-of-sample** error
    (hold out disclosed rows); never report only in-sample fit.

---

## 5. Verification strategy (checks committed to repo)

- Row counts per source reconcile with `DATA_PROFILE.md`.
- Spot-check ~10 disclosed-fee rows back to `Source URL` by hand.
- Invariants: unique Record IDs; `Contract End Year > Start Year`; fees > 0;
  annualized ≈ total / length within tolerance; every FX/CPI join found a match
  (no silent nulls dropping rows).
- Triangulate the Chiba Lotte estimate against the ZOZO Marine floor and ES CON.
- Label any unverifiable figure **unverified**; keep estimates out of the
  disclosed-only benchmark.

---

## 6. Presentation (Part 3)

- **Deployed public Streamlit dashboard on Cloud Run** (course default; reuses
  Assignment 1 setup).
- Features: **currency selector** (USD/JPY/EUR…), **venue-input panel** (capacity,
  league tier, venue type, market) so the engine prices any venue, with
  **Chiba Lotte as the preset**. Benchmark distribution + the target's estimated
  range, every claim visible in a chart.

---

## 7. Guardrails

- Predictive/benchmark valuation — **not causal.** No "capacity causes fee" claims.
- Keep the central answer sharp (commit to a Chiba Lotte range); the generalizable
  engine is a stated strength in DECISIONS.md, not an excuse for a vague answer.
- Accountable for the outcome, not the agent. A green pipeline can still be wrong.

---

## 8. Cloud Credentials

Managed by the [cloud-bootstrap](https://github.com/ipeirotis/cloud-bootstrap)
skill (`.claude/skills/cloud-bootstrap/`). Encrypted credentials live in the
repo; a SessionStart hook decrypts and authenticates automatically at the
start of every Claude Code session — no manual token pasting after initial
setup.

- **Provider / project:** GCP, project `msbai-capstone-at6787`.
- **Service account:** `claude-agent@msbai-capstone-at6787.iam.gserviceaccount.com`.
- **Roles granted (least privilege, requested per-need):**
  - `roles/bigquery.dataEditor` — create/write the `raw` dataset and later
    clean/analysis-ready datasets and tables.
  - `roles/bigquery.jobUser` — run BigQuery load and query jobs.
  - Cloud Run roles (`roles/run.developer`, `roles/artifactregistry.writer`,
    `roles/iam.serviceAccountUser`) are **not yet granted** — to be requested
    via the same skill when the Part 3 Streamlit/Cloud Run deploy actually
    starts, not before.
- **Multi-user:** each team member gets their own
  `.cloud-credentials.<email>.enc`, encrypted with their own passphrase
  (`CLOUD_CREDENTIALS_KEY` or `GCP_CREDENTIALS_KEY` env var, never stored in
  the repo). This repo's identity key uses `CLAUDE_CODE_USER_EMAIL`
  (`at6787@stern.nyu.edu`) rather than `git config user.email`, because this
  harness sets the git commit author to `noreply@anthropic.com` for GitHub
  commit verification — that value does not identify the human user, so the
  cloud-bootstrap hook and workflows here resolve identity via
  `CLAUDE_CODE_USER_EMAIL` first, falling back to `git config user.email`.
- **Authentication:** automatic via `.claude/hooks/cloud-auth.sh`
  (SessionStart hook). To re-run manually or add a team member, see the
  skill's `workflows/authenticate.md` / `workflows/add-team-member.md`.
- **To escalate permissions** (e.g. for the future Cloud Run deploy): ask
  Claude to add the specific role; it will tell you which one and why, then
  wait for your approval before requesting a new bootstrap token — see
  `workflows/permission-escalation.md`. The agent never modifies IAM policy
  without an explicit approved role list.
