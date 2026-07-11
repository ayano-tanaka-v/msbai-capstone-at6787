"""Chiba Lotte Marines naming-rights valuation dashboard (Part 3).

Primary audience: the Chiba Lotte business office, deciding what annual fee
to ask a sponsor for the new stadium's naming rights. Secondary: a candidate
sponsor checking whether an asking price is fair (noted in the UI, not the
primary design target). See dashboard/spec.md for the full spec and Verify
targets this app is built against.

Every number on this page is read from BigQuery (analysis-ready + valuation
tables), cached once per session via st.cache_data -- widget interactions
(currency toggle, capacity/venue-type inputs) recompute in pandas from the
cached data, they never re-query BigQuery.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery

PROJECT = "msbai-capstone-at6787"
CACHE_TTL_SECONDS = 3600

# dataviz skill's validated categorical palette (references/palette.md),
# used by hex value directly since this is a Python/Plotly context, not the
# skill's HTML/CSS-custom-property target.
BLUE = "#2a78d6"
AQUA = "#1baf7a"
RED = "#e34948"
VIOLET = "#4a3aa7"
MUTED_INK = "#898781"
GRIDLINE = "#e1e0d9"

CHIBA_LOTTE_TARGET_ID = "TARGET-CHIBA-LOTTE-2034"
SIZE_BAND_TIER_MATCH = "25k-45k"


@st.cache_resource
def get_client():
    return bigquery.Client(project=PROJECT)


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_valuation_summary():
    return get_client().query(
        f"SELECT * FROM `{PROJECT}.analysis.chiba_lotte_valuation_v2_summary`"
    ).to_dataframe()


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_regression_prediction():
    return get_client().query(
        f"SELECT * FROM `{PROJECT}.analysis.chiba_lotte_regression_prediction`"
    ).to_dataframe()


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_analysis_ready():
    return get_client().query(
        f"SELECT * FROM `{PROJECT}.analysis.naming_rights_analysis_ready`"
    ).to_dataframe()


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_japan_reference():
    return get_client().query(
        f"SELECT * FROM `{PROJECT}.analysis.chiba_lotte_japan_reference_v2`"
    ).to_dataframe()


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_target_venue():
    df = get_client().query(
        f"""SELECT * FROM `{PROJECT}.analysis.target_venues`
            WHERE record_id = '{CHIBA_LOTTE_TARGET_ID}'"""
    ).to_dataframe()
    return df.iloc[0]


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_latest_fx_jpy_per_usd():
    df = get_client().query(
        f"""SELECT lcu_per_usd, year, value_basis FROM `{PROJECT}.ref.fx_rates`
            WHERE currency = 'JPY' ORDER BY year DESC LIMIT 1"""
    ).to_dataframe()
    return float(df["lcu_per_usd"].iloc[0]), int(df["year"].iloc[0]), df["value_basis"].iloc[0]


def venue_type_group(venue_type):
    """Same collapsing rule as scripts/regression_cross_check.py, kept as a
    small standalone copy here rather than importing scripts/ into the
    deployed container (the Docker image only ships dashboard/)."""
    v = str(venue_type).lower()
    if "ballpark" in v:
        return "Ballpark"
    if "stadium" in v:
        return "Stadium"
    if "arena" in v:
        return "Arena"
    return "Other"


def fmt_money(usd_value, currency, fx_rate):
    if currency == "JPY":
        return f"¥{usd_value * fx_rate:,.0f}"
    return f"${usd_value:,.0f}"


def fmt_compact(value, symbol):
    """Compact figure for on-bar labels / hover text, e.g. '¥400M'."""
    if value >= 1e9:
        return f"{symbol}{value / 1e9:,.1f}B"
    if value >= 1e6:
        return f"{symbol}{value / 1e6:,.0f}M"
    return f"{symbol}{value:,.0f}"


def fmt_compact_original(value, currency):
    """Compact original-currency figure, e.g. '¥400M'."""
    symbol = "¥" if currency == "JPY" else f"{currency} "
    return fmt_compact(value, symbol)


def main():
    st.set_page_config(
        page_title="Chiba Lotte Naming-Rights Valuation",
        layout="wide",
    )

    valuation = load_valuation_summary()
    regression = load_regression_prediction()
    comps = load_analysis_ready()
    japan_ref = load_japan_reference()
    target = load_target_venue()
    fx_rate, fx_year, fx_basis = load_latest_fx_jpy_per_usd()

    st.title("Chiba Lotte Marines New Stadium — Naming-Rights Valuation")
    st.markdown(
        "**Built for:** the Chiba Lotte Marines business office, deciding what annual fee to ask "
        "a sponsor for the new stadium's naming rights. *A candidate sponsor can use the same "
        "numbers to judge whether an asking price is fair.*"
    )

    currency = st.radio("Currency", ["JPY", "USD"], horizontal=True, index=0)

    def fmt(usd_value):
        return fmt_money(usd_value, currency, fx_rate)

    def fmt_md(usd_value):
        # Escape "$" for markdown-parsed contexts (st.caption/st.markdown) --
        # otherwise Streamlit's markdown renderer treats "$3,115,912)" as the
        # start of a LaTeX math span and mangles the whole sentence.
        return fmt(usd_value).replace("$", r"\$")

    # ---------- Headline range ----------
    size_band_row = valuation[valuation["valuation_tier"].str.contains(SIZE_BAND_TIER_MATCH)].iloc[0]
    conservative_usd = size_band_row["implied_fee_p25_usd"]
    base_ratio_usd = size_band_row["implied_fee_median_usd"]
    upside_usd = size_band_row["implied_fee_p75_usd"]
    base_regression_usd = regression["point_estimate_usd"].iloc[0]
    base_lo_usd = min(base_ratio_usd, base_regression_usd)
    base_hi_usd = max(base_ratio_usd, base_regression_usd)

    st.header("Recommended annual naming-rights fee")

    def stat_tile(label, value_html):
        st.markdown(
            f"<div style='font-size:0.95rem;color:{MUTED_INK};margin-bottom:2px'>{label}</div>"
            f"<div style='font-size:1.6rem;font-weight:600;line-height:1.25;overflow-wrap:break-word'>{value_html}</div>",
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        stat_tile("Conservative", fmt(conservative_usd))
    with col2:
        stat_tile("Base", f"{fmt(base_lo_usd)} &ndash;<br>{fmt(base_hi_usd)}")
    with col3:
        stat_tile("Upside", fmt(upside_usd))
    st.caption(
        "Base is a range because two independent methods agree closely: the ratio method's "
        f"median ({fmt_md(base_ratio_usd)}) and a regression cross-check's point estimate "
        f"({fmt_md(base_regression_usd)}), fit on the same {int(regression['n_training_rows'].iloc[0])} "
        "global comparable deals. See analysis/VALUATION.md for the full methodology."
    )

    st.divider()

    # ---------- Benchmark distribution ----------
    st.header("Is this grounded in real comparables?")
    size_band_comps = comps[
        (comps["venue_type"].str.contains("Ballpark", case=False, na=False))
        & (comps["capacity"].between(25000, 45000))
    ].copy()

    currency_symbol = "¥" if currency == "JPY" else "$"
    per_seat_multiplier = fx_rate if currency == "JPY" else 1.0
    fee_per_seat_display = size_band_comps["fee_per_seat_real2024"] * per_seat_multiplier

    fig1 = go.Figure()
    fig1.add_trace(
        go.Histogram(
            x=fee_per_seat_display,
            marker_color=BLUE,
            name=f"Global ballparks, 25k–45k capacity",
            hovertemplate=f"{currency_symbol}%{{x:,.0f}}/seat<extra></extra>",
        )
    )
    base_fee_per_seat_display = (base_ratio_usd / target["capacity"]) * per_seat_multiplier
    fig1.add_vline(
        x=base_fee_per_seat_display,
        line_width=3,
        line_color=RED,
        annotation_text=f"Chiba Lotte base estimate: {currency_symbol}{base_fee_per_seat_display:,.0f}/seat",
        annotation_position="top",
    )
    fig1.update_layout(
        title=(
            "Chiba Lotte's estimate sits inside the real range of what similarly-sized "
            f"ballparks worldwide actually charge (n={len(size_band_comps)} comparables)"
        ),
        xaxis_title=f"Naming-rights fee per seat, real-2024-{currency}",
        yaxis_title="Number of comparable deals",
        plot_bgcolor="#fcfcfb",
        paper_bgcolor="#fcfcfb",
        showlegend=False,
        bargap=0.05,
    )
    fig1.update_xaxes(gridcolor=GRIDLINE)
    fig1.update_yaxes(gridcolor=GRIDLINE)
    st.plotly_chart(fig1, width='stretch')
    st.caption(
        f"n={len(size_band_comps)} global ballparks with capacity 25,000–45,000, from "
        "analysis.naming_rights_analysis_ready — every point is a real, disclosed naming-rights deal."
    )

    size_band_sorted = size_band_comps.sort_values("fee_per_seat_real2024", ascending=False)
    comp_table = pd.DataFrame(
        {
            "Venue": size_band_sorted["venue_name"].values,
            "Country": size_band_sorted["country"].values,
            "Capacity": [f"{int(c):,}" for c in size_band_sorted["capacity"]],
            "Contract start": [str(int(y)) for y in size_band_sorted["contract_start_year"]],
            "Annual fee": [fmt(v) for v in size_band_sorted["annual_fee_usd_real2024"]],
            "Fee/seat": [fmt(v) for v in size_band_sorted["fee_per_seat_real2024"]],
        }
    )
    with st.expander(f"See the {len(comp_table)} comparable venues behind this distribution"):
        st.dataframe(comp_table, use_container_width=True, hide_index=True)
        st.caption(
            "Sorted high to low by fee per seat, real-2024-USD converted to the selected currency. "
            "Same rows and figures as analysis.naming_rights_analysis_ready, filtered to the 25k–45k ballpark band."
        )

    st.divider()

    # ---------- Japan vs global ----------
    st.header("Why not just match what Japan pays today?")
    money_multiplier = fx_rate if currency == "JPY" else 1.0
    japan_plot = japan_ref.dropna(subset=["fee_per_seat_real2024"]).copy()
    japan_plot["implied_fee_33k_display"] = (
        japan_plot["fee_per_seat_real2024"] * target["capacity"] * money_multiplier
    )
    japan_plot = japan_plot.sort_values("implied_fee_33k_display")

    fig2 = go.Figure()
    for classification, color in [("OBSERVED", BLUE), ("ESTIMATE", AQUA)]:
        subset = japan_plot[japan_plot["row_classification"] == classification]
        raw_value_str = [
            fmt_compact_original(v, c) for v, c in zip(subset["annual_fee_original"], subset["currency"])
        ]
        capacity_str = [f"{int(c):,}" for c in subset["capacity"]]
        normalized_str = [fmt_compact(v, currency_symbol) for v in subset["implied_fee_33k_display"]]
        bar_text = [f"{rv} @ {cap} seats" for rv, cap in zip(raw_value_str, capacity_str)]
        fig2.add_trace(
            go.Bar(
                y=subset["venue_name"],
                x=subset["implied_fee_33k_display"],
                orientation="h",
                marker_color=color,
                marker_line_color="white",
                marker_line_width=1,
                name=f"Japan — {classification.title()}",
                text=bar_text,
                textposition="outside",
                textfont=dict(size=11, color=MUTED_INK),
                customdata=list(zip(raw_value_str, capacity_str, normalized_str)),
                hovertemplate=(
                    "<b>%{y}</b> — actual deal: %{customdata[0]}/year, %{customdata[1]} seats "
                    "(&#8594; %{customdata[2]} if scaled to 33,000 seats)"
                    "<extra></extra>"
                ),
            )
        )
    fig2.add_vrect(
        x0=conservative_usd * money_multiplier,
        x1=upside_usd * money_multiplier,
        fillcolor=RED,
        opacity=0.12,
        line_width=0,
        annotation_text="Global-standard range",
        annotation_position="top left",
    )
    fig2.add_vline(x=base_ratio_usd * money_multiplier, line_width=2, line_color=RED, line_dash="dash")
    fig2.update_layout(
        title=(
            "Today's Japan naming-rights deals sit well below what a similarly-sized ballpark "
            "commands globally — that gap is the convergence upside"
        ),
        xaxis_title=(
            f"Implied fee IF scaled to {int(target['capacity']):,} seats (size-normalized) — "
            "hover for each venue's actual fee & capacity"
        ),
        legend_title="Japan deal classification",
        plot_bgcolor="#fcfcfb",
        paper_bgcolor="#fcfcfb",
        height=550,
        margin=dict(r=160),
    )
    fig2.update_xaxes(gridcolor=GRIDLINE)
    fig2.update_yaxes(gridcolor=GRIDLINE)
    st.plotly_chart(fig2, width='stretch')
    st.caption(
        "Bars are size-normalized to 33,000 seats so every venue is comparable on one axis regardless of its "
        "real capacity — e.g. MUFG Stadium (¥2B, 68,000 seats) and IG Arena (¥500M, 17,000 seats) land at "
        "similar bar lengths only because both work out to a similar $/seat rate, not because their real "
        "contracts are alike. Hover or read the label on each bar for the real contract value and capacity. "
        "ESTIMATE rows (lighter) are unverified media/analyst figures, not consummated contracts — shown for "
        "triangulation only, never mixed into the global comparable set the range above is built from."
    )

    st.divider()

    # ---------- Generalizable engine ----------
    st.header("Price any venue")
    st.markdown("Chiba Lotte (33,000-seat ballpark) is the preset — change the inputs to price a different venue.")
    engine_col1, engine_col2 = st.columns(2)
    input_capacity = engine_col1.number_input(
        "Capacity", min_value=1000, max_value=120000, value=int(target["capacity"]), step=500
    )
    input_venue_type = engine_col2.selectbox(
        "Venue type", ["Ballpark", "Stadium", "Arena", "Other"], index=0
    )

    comps_local = comps.copy()
    comps_local["venue_type_group"] = comps_local["venue_type"].apply(venue_type_group)
    band_low = input_capacity * (25000 / 33000)
    band_high = input_capacity * (45000 / 33000)
    matched = comps_local[
        (comps_local["venue_type_group"] == input_venue_type)
        & (comps_local["capacity"].between(band_low, band_high))
    ]

    if len(matched) < 5:
        st.warning(
            f"Only {len(matched)} comparables of this venue type/size — falling back to all "
            f"{input_venue_type} venues globally, regardless of size, for a rougher estimate."
        )
        matched = comps_local[comps_local["venue_type_group"] == input_venue_type]

    if len(matched) == 0:
        st.error("No comparables of this venue type exist in the dataset — cannot estimate.")
    else:
        p25, median, p75 = matched["fee_per_seat_real2024"].quantile([0.25, 0.5, 0.75])
        e1, e2, e3 = st.columns(3)
        e1.metric("Conservative", fmt(p25 * input_capacity))
        e2.metric("Base", fmt(median * input_capacity))
        e3.metric("Upside", fmt(p75 * input_capacity))
        st.caption(
            f"Based on {len(matched)} global {input_venue_type.lower()} comparables "
            f"({int(band_low):,}–{int(band_high):,} seats). Recomputed live from cached data — "
            "no BigQuery query on this interaction."
        )

    st.divider()
    st.caption(
        f"FX: ¥{fx_rate:,.2f}/\\$1 ({fx_year} {fx_basis}). Data: BigQuery `{PROJECT}` — "
        "analysis.naming_rights_analysis_ready, analysis.chiba_lotte_valuation_v2_summary, "
        "analysis.chiba_lotte_regression_prediction. See analysis/VALUATION.md for the full write-up."
    )


if __name__ == "__main__":
    main()
