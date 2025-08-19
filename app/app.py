# app.py — FAERS Single-Drug Signal Explorer (2023, DuckDB+Parquet, optimized & polished)
import duckdb
from io import StringIO
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ==============================
# CONFIG
# ==============================
ANYDRUG_SOURCE = "data/anydrug_2023.parquet"  # Parquet snapshot created by export_to_parquet.py
PRR_CAP = 1000.0

# Guardrails (fixed; non-tunable to keep scope tight)
EXP_MIN = 5         # all four expected counts must be >= 5
BG_MIN = 2000       # c+d must be large enough to avoid denominator spikes
TABLE_MIN = 10000   # a+b+c+d must be sizable
MIN_ELIGIBLE_PTS = 15  # a drug must have at least this many PT rows passing guardrails to appear
SAFE_N_MIN = 5         # a must be >= 5 when we pre-validate
MAX_DISPLAY_ROWS = 60  # cap rows shown/plotted for speed & legibility

st.set_page_config(page_title="FAERS Signal Detection (2023)", layout="wide")

# ==============================
# DB HELPERS (DuckDB + Parquet)
# ==============================
@st.cache_resource
def get_ddb():
    # In-memory DuckDB; Parquet scans are parallelized by DuckDB
    return duckdb.connect(database=":memory:")

@st.cache_data(show_spinner=True, ttl=1200)
def fetch_df(sql: str, params=None) -> pd.DataFrame:
    return get_ddb().execute(sql, params or {}).df()

# ==============================
# VALIDATED DRUG PICKER (SQL over Parquet)
# ==============================
@st.cache_data(show_spinner=False, ttl=3600)
def get_validated_drugs() -> list[str]:
    q = f"""
    WITH base AS (
      SELECT
        ingredient_std,
        reaction_pt,
        CAST(a AS DOUBLE) AS a,
        CAST(b AS DOUBLE) AS b,
        CAST(c AS DOUBLE) AS c,
        CAST(d AS DOUBLE) AS d
      FROM read_parquet('{ANYDRUG_SOURCE}')
      WHERE ingredient_std IS NOT NULL AND LENGTH(TRIM(ingredient_std)) > 0
        AND reaction_pt   IS NOT NULL AND LENGTH(TRIM(reaction_pt))   > 0
    ),
    feats AS (
      SELECT
        ingredient_std,
        reaction_pt,
        a, b, c, d,
        (a+b+c+d) AS total,
        (c+d)     AS bg,
        (a+b)     AS row1,
        (c+d)     AS row2,
        (a+c)     AS col1,
        (b+d)     AS col2
      FROM base
    ),
    eligible AS (
      SELECT ingredient_std, reaction_pt
      FROM feats
      WHERE total >= {TABLE_MIN}
        AND bg    >= {BG_MIN}
        AND a     >= {SAFE_N_MIN}
        AND (row1*col1)/NULLIF(total,0) >= {EXP_MIN}
        AND (row1*col2)/NULLIF(total,0) >= {EXP_MIN}
        AND (row2*col1)/NULLIF(total,0) >= {EXP_MIN}
        AND (row2*col2)/NULLIF(total,0) >= {EXP_MIN}
    )
    SELECT ingredient_std
    FROM eligible
    WHERE strpos(ingredient_std, '\\\\') = 0
    GROUP BY ingredient_std
    HAVING COUNT(*) >= {MIN_ELIGIBLE_PTS}
    ORDER BY ingredient_std;
    """
    df = fetch_df(q)
    if df.empty:
        return []
    return df["ingredient_std"].astype(str).str.strip().tolist()

# ==============================
# STATS HELPERS
# ==============================
def prr_display(val: float, cap: float = PRR_CAP) -> str:
    if np.isinf(val) or (val is not None and val > cap):
        return f">{int(cap)}"
    return f"{val:.2f}"

# ==============================
# ROW-LEVEL COMPUTE & FETCH (SQL prefilters + vectorized stats)
# ==============================
@st.cache_data(show_spinner=True, ttl=900)
def get_drug_rows(drug: str, prr_min: float, chi2_min: float, n_min: int, flagged_only=True) -> pd.DataFrame:
    q = f"""
      SELECT ingredient_std AS drug, reaction_pt, a, b, c, d
      FROM read_parquet('{ANYDRUG_SOURCE}')
      WHERE ingredient_std = ?
        AND (a+b+c+d) >= {TABLE_MIN}
        AND (c+d)      >= {BG_MIN}
        AND a          >= {n_min}
    """
    out = fetch_df(q, [drug])
    if out.empty:
        return out

    # Ensure numeric
    for col in ["a", "b", "c", "d"]:
        out[col] = out[col].astype(float)

    # Expected counts (vectorized)
    n  = out[["a", "b", "c", "d"]].sum(axis=1)
    r1 = out["a"] + out["b"]
    r2 = out["c"] + out["d"]
    c1 = out["a"] + out["c"]
    c2 = out["b"] + out["d"]
    out["Ea"] = (r1 * c1) / n
    out["Eb"] = (r1 * c2) / n
    out["Ec"] = (r2 * c1) / n
    out["Ed"] = (r2 * c2) / n

    out["total"] = n
    out["bg"] = r2
    out["N"] = out["a"].astype(int)

    # --- PRR / ROR / chi2 (vectorized, conditional Haldane eps=0.5) ---
    zeros_mask = (out[["a", "b", "c", "d"]] == 0).any(axis=1).to_numpy()
    eps = np.where(zeros_mask, 0.5, 0.0)

    a = out["a"].to_numpy() + eps
    b = out["b"].to_numpy() + eps
    c = out["c"].to_numpy() + eps
    d = out["d"].to_numpy() + eps

    prr = (a / (a + b)) / (c / (c + d))
    se_prr = np.sqrt((1 / a) - (1 / (a + b)) + (1 / c) - (1 / (c + d)))
    log_prr = np.log(prr)
    out["PRR"] = prr
    out["PRR_LCL"] = np.exp(log_prr - 1.96 * se_prr)
    out["PRR_UCL"] = np.exp(log_prr + 1.96 * se_prr)

    ror = (a * d) / (b * c)
    se_ror = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    log_ror = np.log(ror)
    out["ROR"] = ror
    out["ROR_LCL"] = np.exp(log_ror - 1.96 * se_ror)
    out["ROR_UCL"] = np.exp(log_ror + 1.96 * se_ror)

    num = (a * d - b * c) ** 2 * (a + b + c + d)
    den = (a + b) * (c + d) * (a + c) * (b + d)
    out["chi2"] = num / den

    ok_expected = out[["Ea", "Eb", "Ec", "Ed"]].min(axis=1) >= EXP_MIN
    ok_lcl = out["PRR_LCL"] > 1.0
    ok_finite = np.isfinite(out["PRR"].to_numpy())

    out["flagged"] = (
        (out["PRR"] >= prr_min) &
        (out["chi2"] >= chi2_min) &
        (out["N"] >= n_min) &
        ok_expected & ok_lcl & ok_finite
    )

    if flagged_only:
        out = out[out["flagged"]]

    out = out.sort_values(["PRR", "chi2"], ascending=[False, False]).head(MAX_DISPLAY_ROWS).reset_index(drop=True)
    out["reaction_pt"] = out["reaction_pt"].astype("category")
    return out

# ==============================
# VISUAL HELPERS & PLOTS
# ==============================
def _wrap_labels(labels, width=28):
    out = []
    for s in labels:
        s = str(s)
        chunks, line = [], []
        for w in s.split():
            line.append(w)
            if len(" ".join(line)) > width:
                line.pop()
                chunks.append(" ".join(line))
                line = [w]
        if line:
            chunks.append(" ".join(line))
        out.append("<br>".join(chunks))
    return out

def _base_layout(title, height_rows: int, x_title=None, y_title=None):
    return dict(
        template="plotly_white",
        title=dict(text=title, x=0, xanchor="left", yanchor="top", font=dict(size=18, family="Inter, Arial, sans-serif")),
        margin=dict(l=10, r=10, t=48, b=10),
        height=max(360, 40 * max(1, height_rows)),
        font=dict(size=14, family="Inter, Arial, sans-serif"),
        xaxis=dict(title=x_title, showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False, tickfont=dict(size=12)),
        yaxis=dict(title=y_title, showgrid=False, tickfont=dict(size=12), automargin=True),
    )

PLOT_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "toImageButtonOptions": {"format": "png", "filename": "faers_chart", "height": 800, "width": 1200, "scale": 2},
}

def plot_counts_bar(df: pd.DataFrame, title: str):
    if df.empty:
        return None
    d = df[["reaction_pt", "N"]].copy()
    d["N"] = d["N"].astype(int)
    d = d.sort_values("N", ascending=True)
    y_wrapped = _wrap_labels(d["reaction_pt"].tolist(), width=26)

    fig = go.Figure()
    fig.add_bar(
        x=d["N"], y=y_wrapped, orientation="h",
        text=d["N"].astype(str), textposition="outside",
        hovertemplate="<b>%{y}</b><br>N=%{x}<extra></extra>",
        marker=dict(line=dict(width=0.5, color="rgba(0,0,0,0.25)")),
    )
    fig.update_layout(**_base_layout(title, height_rows=len(d), x_title="Number of cases (N)", y_title="Reaction PT"))
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(uniformtext_minsize=10, uniformtext_mode="hide", bargap=0.25)
    return fig

def plot_forest(df: pd.DataFrame, prr_min: float, title: str):
    if df.empty:
        return None

    have_N = "N" in df.columns
    cols = ["reaction_pt", "PRR", "PRR_LCL", "PRR_UCL"] + (["N"] if have_N else [])
    d = df[cols].copy()

    d["PRR"] = d["PRR"].clip(lower=0.01, upper=PRR_CAP)
    d["PRR_LCL"] = d["PRR_LCL"].clip(lower=0.01)
    d["PRR_UCL"] = d["PRR_UCL"].clip(upper=PRR_CAP)
    d = d.sort_values("PRR", ascending=True)

    y_wrapped = _wrap_labels(d["reaction_pt"].tolist(), width=26)
    prr = d["PRR"].to_numpy()
    lcl = d["PRR_LCL"].to_numpy()
    ucl = d["PRR_UCL"].to_numpy()
    err_low  = prr - lcl
    err_high = ucl - prr

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=prr, y=y_wrapped, mode="markers",
        marker=dict(symbol="square", size=10),
        error_x=dict(type="data", array=err_high, arrayminus=err_low, thickness=1.5, width=0),
        hovertemplate="%{text}<extra></extra>", showlegend=False,
    ))

    # Per-point hover text
    hover_text = [f"<b>{yy}</b><br>PRR={p:.2f}<br>95% CI: [{lo:.2f}, {hi:.2f}]"
                  for yy, p, lo, hi in zip(y_wrapped, prr, lcl, ucl)]
    fig.data[0].text = hover_text

    # Size markers by N if available
    if have_N:
        N = d["N"].to_numpy().astype(float)
        if np.isfinite(N).any() and N.max() > 0:
            sizes = np.clip(6 + (N / N.max()) * 10, 8, 16)
        else:
            sizes = np.full_like(N, 10, dtype=float)
        fig.data[0].marker.size = sizes

    # Reference lines (bold + labeled + legend-friendly)
    fig.add_vline(x=1.0, line_dash="dash", line_color="#444", line_width=3, opacity=0.95)
    fig.add_vline(x=float(prr_min), line_dash="dot", line_color="#D62728", line_width=3, opacity=0.95, layer="above")
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines",
                             line=dict(color="#444", width=3, dash="dash"), name="PRR = 1"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines",
                             line=dict(color="#D62728", width=3, dash="dot"), name=f"Threshold = {prr_min:.1f}"))
    fig.add_annotation(x=1.0, xref="x", y=1.02, yref="paper",
                       text="PRR = 1", showarrow=False,
                       font=dict(size=12, color="#444"),
                       bgcolor="rgba(255,255,255,0.8)", bordercolor="#444", borderwidth=0.5, borderpad=3)
    fig.add_annotation(x=float(prr_min), xref="x", y=1.02, yref="paper",
                       text=f"Threshold = {prr_min:.1f}", showarrow=False,
                       font=dict(size=12, color="#D62728"),
                       bgcolor="rgba(255,255,255,0.8)", bordercolor="#D62728", borderwidth=0.5, borderpad=3)

    # Log axis ticks + bounds
    tick_vals = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
    tick_text = ["0.1","0.2","0.5","1","2","5","10","20","50","100","200","500",">1k"]
    xmax = max(PRR_CAP, float(prr_min) * 1.1)
    fig.update_xaxes(
        type="log",
        tickvals=[v for v in tick_vals if v <= xmax],
        ticktext=[t for v,t in zip(tick_vals, tick_text) if v <= xmax],
        range=[-1, np.log10(xmax)],
        title="PRR (log scale)",
        showgrid=True, gridcolor="rgba(0,0,0,0.08)", zeroline=False
    )
    fig.update_layout(**_base_layout(title, height_rows=len(d), y_title="Reaction PT"))
    return fig

# ==============================
# UI ROUTING + SIDEBAR (single source of truth)
# ==============================
st.title("FAERS Signal Detection — 2023 (Validated Scope, DuckDB)")

# Keep the nav itself in the sidebar
page = st.sidebar.radio("Navigation", ["Overview", "Analysis"], index=1, key="nav")

if page == "Overview":
    st.header("What this app does")
    st.markdown("""
This tool screens **FAERS 2023** for **disproportionate reporting** of adverse events for a **single ingredient** (PRR/ROR/χ² on 2×2 tables).
We intentionally keep a **small, conservative scope** so results are **fast** and **hard to misread**.
""")
    st.subheader("Important limitations (read me)")
    st.markdown("""
- **Screening, not causality**: Disproportionality highlights **signals** worth follow-up; it does **not** prove risk or incidence.
- **Reporting bias & confounding**: FAERS is spontaneous; counts reflect **reports**, not exposure.
- **Conservative defaults**: We may miss rare-but-real signals; that’s intentional for a precise demo.
""")
    st.caption(f"Source: `{ANYDRUG_SOURCE}` (Parquet snapshot of `v_anydrug_signal_2x2_2023`)")
    st.stop()  # Don’t render analysis below on Overview

# ---------- Analysis page ----------
# Sidebar controls (ONLY here)
with st.sidebar:
    st.header("Controls")

    drugs = get_validated_drugs()
    if not drugs:
        st.error("No validated ingredients found. Rebuild snapshot or loosen guardrails.")
        st.stop()

    # Initialize session state once (no widget defaults)
    if "picked_drug" not in st.session_state or st.session_state.picked_drug not in drugs:
        st.session_state.picked_drug = drugs[0]
    if "prr_min" not in st.session_state:  st.session_state.prr_min  = 2.0
    if "chi2_min" not in st.session_state: st.session_state.chi2_min = 4.0
    if "n_min" not in st.session_state:    st.session_state.n_min    = 5

    # Widgets driven by state (no value=)
    picked = st.selectbox("Validated single ingredient", options=drugs, key="picked_drug")
    st.subheader("Flagging thresholds")
    st.number_input("PRR ≥",  min_value=0.0, step=0.5, key="prr_min")
    st.number_input("χ² ≥",   min_value=0.0, step=0.5, key="chi2_min")
    st.number_input("N ≥",    min_value=0,   step=1,   key="n_min")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("↻ Clear cache", use_container_width=True, key="btn_clear_cache"):
            st.cache_data.clear(); st.cache_resource.clear()
            st.success("Cache cleared.")
    with col_b:
        if st.button("Reset thresholds", use_container_width=True, key="btn_reset_thresholds"):
            st.session_state.prr_min  = 2.0
            st.session_state.chi2_min = 4.0
            st.session_state.n_min    = 5

# ---------- Main results ----------
st.header("Adverse event analysis")

prr_min  = float(st.session_state.prr_min)
chi2_min = float(st.session_state.chi2_min)
n_min    = int(st.session_state.n_min)

with st.spinner("Building report..."):
    df = get_drug_rows(picked, prr_min, chi2_min, n_min, flagged_only=True)

top_l, top_r = st.columns([1, 1.2])
with top_l:
    st.subheader(f"Results for **{picked}**")
    st.metric("Flagged signals", len(df))
    if len(df) == 0:
        st.info("No flagged PTs at current thresholds and guardrails. Try lowering PRR/χ²/N or choose another ingredient.")
with top_r:
    st.markdown("**Decision rule:** Flag if PRR ≥ **{:.1f}**, χ² ≥ **{:.1f}**, N ≥ **{}**".format(prr_min, chi2_min, n_min))
    st.caption(f"Generated {datetime.now():%Y-%m-%d %H:%M:%S}")

if not df.empty:
    # Main table (collapsed to essentials)
    show = df[["reaction_pt","N","PRR","PRR_LCL","PRR_UCL","chi2"]].copy()
    show["PRR_display"] = show["PRR"].apply(prr_display)

    st.markdown("### Flagged PTs (top {} shown)".format(MAX_DISPLAY_ROWS))
    st.dataframe(show[["reaction_pt","N","PRR_display","PRR_LCL","PRR_UCL","chi2"]].round(3), use_container_width=True)

    # Download (full detail), with a unique key
    buf = StringIO(); df.round(5).to_csv(buf, index=False)
    st.download_button(
        "Download CSV",
        data=buf.getvalue(),
        file_name=f"{picked}_signals.csv",
        mime="text/csv",
        key=f"dl_main_{picked}_{prr_min}_{chi2_min}_{n_min}",
    )

    # Plots (unique keys to avoid duplicate-ID errors)
    st.markdown("### Case counts")
    fig_counts = plot_counts_bar(df[["reaction_pt","N"]], title=f"{picked}: flagged PT counts")
    if fig_counts:
        st.plotly_chart(fig_counts, use_container_width=True, theme=None, config=PLOT_CONFIG,
                        key=f"plt_counts_{picked}_{prr_min}_{chi2_min}_{n_min}")

    st.markdown("### PRR forest (95% CI)")
    fig_forest = plot_forest(df[["reaction_pt","PRR","PRR_LCL","PRR_UCL","N"]], prr_min, title=f"{picked}: PRR with 95% CI")
    if fig_forest:
        st.plotly_chart(fig_forest, use_container_width=True, theme=None, config=PLOT_CONFIG,
                        key=f"plt_forest_{picked}_{prr_min}_{chi2_min}_{n_min}")

    # Debug / Transparency (2×2 + expected counts only)
    with st.expander("🔍 Debug / Transparency (2×2 + expected counts)"):
        st.caption(
            f"Raw 2×2 cells (a,b,c,d) and expected counts (Ea–Ed). "
            f"Verify guardrails: Ea–Ed ≥ {EXP_MIN}, bg ≥ {BG_MIN}, total ≥ {TABLE_MIN}, PRR_LCL>1."
        )
        qa = df[["reaction_pt","a","b","c","d","Ea","Eb","Ec","Ed"]].copy().round(3)
        st.dataframe(qa, use_container_width=True)
else:
    st.caption("No rows to show.")

with st.expander("What do these metrics mean?"):
    st.markdown("""
- **N**: number of unique cases reporting this reaction with this drug (2×2 cell **a**).
- **PRR**: (a/(a+b)) / (c/(c+d)). PRR≈1 → no disproportionality.
- **95% CI**: Wald CI with conditional Haldane–Anscombe correction (ε=0.5 only when a zero exists).
- **χ²**: Pearson chi-square on the 2×2.

**2×2 layout**
|          | Reaction=Yes | Reaction=No |
|----------|--------------|-------------|
| Drug=Yes | a            | b           |
| Drug=No  | c            | d           |
""")

with st.expander("Method notes & limitations"):
    st.markdown("""
- **Screening only**: Signals ≠ causation; FAERS counts are not exposure-adjusted incidence.
- **Biases**: Under/over-reporting, stimulated reporting, indication confounding, miscoding.
- **Conservative defaults**: We may miss rare-but-real signals; that’s intentional for a precise demo.
""")
