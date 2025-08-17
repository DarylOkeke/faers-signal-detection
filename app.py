# app.py
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from io import StringIO

# ====== CONFIG ======
DB_PATH = "data/faers+medicare.db"
SIGNAL_VIEW = "v_signal_2x2_2023"
COHORT_VIEW = "v_events_2023_cohorts"

# ====== CACHE HELPERS ======
@st.cache_data(show_spinner=False)
def get_connection_info():
    return DB_PATH, SIGNAL_VIEW, COHORT_VIEW

@st.cache_data(show_spinner=True)
def get_cohorts_pts_counts(db_path: str):
    """Return (all_cohorts, all_pts, cohort_counts_df)"""
    with sqlite3.connect(db_path) as conn:
        pts = pd.read_sql_query(
            f"SELECT DISTINCT reaction_pt FROM {COHORT_VIEW} "
            f"WHERE reaction_pt <> '' ORDER BY reaction_pt", conn
        )["reaction_pt"].tolist()

        counts = pd.read_sql_query(
            f"SELECT cohort, COUNT(DISTINCT primaryid) AS n_cases "
            f"FROM {COHORT_VIEW} GROUP BY cohort ORDER BY n_cases DESC", conn
        )

    # Put cardiac endpoints on top if present
    cardiac = ['CARDIAC TAMPONADE', 'PERICARDIAL EFFUSION', 'PERICARDITIS', 'PLEURAL EFFUSION']
    pts = sorted(set(pts), key=lambda x: (x not in cardiac, x))
    cohorts = counts["cohort"].tolist()
    return cohorts, pts, counts

@st.cache_data(show_spinner=True)
def fetch_signal_rows(db_path: str, cohorts: list, pts: list):
    """Pull a,b,c,d for selected cohorts/PTs from view."""
    if not cohorts or not pts:
        return pd.DataFrame(columns=["cohort","reaction_pt","a","b","c","d"])
    placeholders_c = ",".join("?"*len(cohorts))
    placeholders_p = ",".join("?"*len(pts))
    q = f"""
        SELECT cohort, reaction_pt, a, b, c, d
        FROM {SIGNAL_VIEW}
        WHERE cohort IN ({placeholders_c})
          AND reaction_pt IN ({placeholders_p})
        ORDER BY reaction_pt, cohort
    """
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(q, conn, params=cohorts+pts)
    return df

@st.cache_data(show_spinner=True)
def fetch_top_signals(db_path: str, prr_min=2.0, chi2_min=4.0, n_min=3, limit=25):
    """Overview page: top flagged signals overall."""
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            f"SELECT cohort, reaction_pt, a, b, c, d FROM {SIGNAL_VIEW}", conn
        )
    df = add_stats(df, prr_min, chi2_min, n_min)
    flagged = df[df["flagged"]].copy()
    return (flagged
            .sort_values(["PRR","chi2"], ascending=[False, False])
            .head(limit)
            .reset_index(drop=True))

# ====== STATS ======
def _wald_ci_prr(a,b,c,d, eps=0.5):
    a_=a+eps; b_=b+eps; c_=c+eps; d_=d+eps
    prr = (a_/(a_+b_)) / (c_/(c_+d_))
    se  = np.sqrt((1/a_) - (1/(a_+b_)) + (1/c_) - (1/(c_+d_)))
    lcl = np.exp(np.log(prr) - 1.96*se)
    ucl = np.exp(np.log(prr) + 1.96*se)
    return prr, lcl, ucl

def _wald_ci_ror(a,b,c,d, eps=0.5):
    a_=a+eps; b_=b+eps; c_=c+eps; d_=d+eps
    ror = (a_*d_)/(b_*c_)
    se  = np.sqrt(1/a_ + 1/b_ + 1/c_ + 1/d_)
    lcl = np.exp(np.log(ror) - 1.96*se)
    ucl = np.exp(np.log(ror) + 1.96*se)
    return ror, lcl, ucl

def chi_square(a,b,c,d, eps=0.5):
    a_=a+eps; b_=b+eps; c_=c+eps; d_=d+eps
    num = (a_*d_ - b_*c_)**2 * (a_+b_+c_+d_)
    den = (a_+b_)*(c_+d_)*(a_+c_)*(b_+d_)
    return num/den

def add_stats(df, prr_min=2.0, chi2_min=4.0, n_min=3):
    out = df.copy()
    if out.empty:
        return out.assign(N=[], PRR=[], PRR_LCL=[], PRR_UCL=[],
                          ROR=[], ROR_LCL=[], ROR_UCL=[], chi2=[], flagged=[])
    out["N"] = out["a"].astype(int)
    out[["PRR","PRR_LCL","PRR_UCL"]] = out.apply(
        lambda r: _wald_ci_prr(r.a, r.b, r.c, r.d), axis=1, result_type="expand"
    )
    out[["ROR","ROR_LCL","ROR_UCL"]] = out.apply(
        lambda r: _wald_ci_ror(r.a, r.b, r.c, r.d), axis=1, result_type="expand"
    )
    out["chi2"] = out.apply(lambda r: chi_square(r.a, r.b, r.c, r.d), axis=1)
    out["flagged"] = (out["PRR"]>=prr_min) & (out["chi2"]>=chi2_min) & (out["N"]>=n_min)
    return out

# ====== UI UTILS ======
def df_download_button(df: pd.DataFrame, filename: str, label="Download CSV"):
    buf = StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, data=buf.getvalue(), file_name=filename, mime="text/csv")

def make_palette(labels):
    """Return dict {label: hexcolor} for any set of cohorts."""
    cmap = plt.get_cmap('tab20')
    return {lab: mcolors.to_hex(cmap(i % cmap.N)) for i, lab in enumerate(sorted(set(labels)))}

def prr_forest(show: pd.DataFrame, prr_min: float):
    """Render PRR forest with 95% CI; one color per row (fixes list-of-colors bug)."""
    if show.empty:
        st.info("No rows to plot.")
        return
    fig, ax = plt.subplots(figsize=(8, max(3, 0.5*len(show))))
    palette = make_palette(show["cohort"])

    ylabels = []
    for i, row in show.iterrows():
        prr = max(row["PRR"], 0.01)
        lcl = max(row["PRR_LCL"], 0.01)
        ucl = max(row["PRR_UCL"], 0.01)
        color = palette.get(row["cohort"], "#000000")

        ax.errorbar(
            prr, i,
            xerr=[[prr - lcl], [ucl - prr]],
            fmt='s', color=color, ecolor=color, capsize=3
        )
        ylabels.append(f"{row['reaction_pt']} — {row['cohort']}")

    ax.set_xscale("log")
    ax.axvline(1.0, ls='--', color='k', alpha=0.5, label='No effect (PRR=1)')
    ax.axvline(prr_min, ls=':', color='r', alpha=0.6, label='Signal threshold')
    ax.set_xlabel("Proportional Reporting Ratio (PRR)")
    ax.set_yticks(range(len(ylabels)))
    ax.set_yticklabels(ylabels)
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.2)

    # Legend (dedup)
    handles, labels = ax.get_legend_handles_labels()
    by = {}
    for h, lab in zip(handles, labels):
        if lab and lab not in by:
            by[lab] = h
    # Add cohort swatches
    for c, col in palette.items():
        by[c] = plt.Line2D([0],[0], marker='s', color=col, linestyle='None')
    ax.legend(by.values(), by.keys(), loc="upper right", frameon=True)
    st.pyplot(fig, use_container_width=True)

def count_bars(show_counts: pd.DataFrame):
    """Horizontal bar chart for N by cohort/PT (matching forest order)."""
    if show_counts.empty:
        return
    fig, ax = plt.subplots(figsize=(8, max(3, 0.5*len(show_counts))))
    palette = make_palette(show_counts["cohort"])
    ylabels = []
    for i, row in show_counts.iterrows():
        n = int(row["N"])
        color = palette.get(row["cohort"], "#000000")
        ax.barh(i, n, height=0.35, color=color, edgecolor="white")
        ax.text(n + 0.2, i, str(n), va='center', ha='left', fontsize=9, fontweight='bold')
        ylabels.append(f"{row['reaction_pt']} — {row['cohort']}")

    ax.set_xlabel("Number of Cases (N)")
    ax.set_yticks(range(len(ylabels)))
    ax.set_yticklabels(ylabels)
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.2)
    st.pyplot(fig, use_container_width=True)

# ====== APP ======
st.set_page_config(page_title="FAERS Signal Detection", layout="wide")
st.title("FAERS Signal Detection Explorer (2023)")

db_path, signal_view, cohort_view = get_connection_info()
page = st.sidebar.radio("Page", ["Cohort / Endpoint Analysis", "All Cohorts Overview"])

# ---------- PAGE 1: Cohort / Endpoint Analysis ----------
if page == "Cohort / Endpoint Analysis":
    left, right = st.columns([1,2], gap="large")

    with left:
        st.subheader("Filters")
        cohorts_all, pts_all, cohort_counts = get_cohorts_pts_counts(db_path)

        # default to top 5 cohorts by size
        default_cohorts = cohort_counts["cohort"].head(5).tolist()
        selected_cohorts = st.multiselect(
            "Cohorts (from database)",
            options=cohorts_all,
            default=default_cohorts
        )

        cardiac = ['CARDIAC TAMPONADE', 'PERICARDIAL EFFUSION', 'PERICARDITIS', 'PLEURAL EFFUSION']
        default_pts = [pt for pt in cardiac if pt in pts_all] or pts_all[:10]
        selected_pts = st.multiselect(
            "Reaction PTs (MedDRA)",
            options=pts_all,
            default=default_pts
        )

        st.markdown("**Flagging thresholds**")
        prr_min = st.number_input("PRR ≥", min_value=0.0, value=2.0, step=0.5)
        chi2_min = st.number_input("χ² ≥", min_value=0.0, value=4.0, step=0.5)
        n_min = st.number_input("N ≥", min_value=0, value=3, step=1)

        run_btn = st.button("Analyze")

    with right:
        if not selected_cohorts or not selected_pts:
            st.info("Select at least one cohort and one reaction PT to begin.")
            st.stop()

        if run_btn:
            with st.spinner("Querying database and computing statistics..."):
                base = fetch_signal_rows(db_path, selected_cohorts, selected_pts)
                if base.empty:
                    st.warning("No rows found for your selections.")
                    st.stop()
                stats = add_stats(base, prr_min=prr_min, chi2_min=chi2_min, n_min=n_min)

            st.subheader("Results")
            show = stats[[
                "cohort","reaction_pt","N","a","b","c","d",
                "PRR","PRR_LCL","PRR_UCL","ROR","ROR_LCL","ROR_UCL","chi2","flagged"
            ]].sort_values(["reaction_pt","cohort"]).reset_index(drop=True)

            st.dataframe(show, use_container_width=True)
            df_download_button(show.round(4), "faers_signal_results.csv")

            flagged = show[show["flagged"]].copy()
            st.markdown(f"**Flagged signals:** {len(flagged)}")
            if len(flagged):
                st.table(flagged[["cohort","reaction_pt","N","PRR","PRR_LCL","PRR_UCL","chi2"]]
                         .sort_values(["reaction_pt","PRR"], ascending=[True,False]).round(3))

            # Visuals (counts + forest)
            st.markdown("### Case Counts")
            count_bars(show[["cohort","reaction_pt","N"]])

            st.markdown("### PRR Forest (95% CI)")
            prr_forest(show, prr_min)

# ---------- PAGE 2: All Cohorts Overview ----------
if page == "All Cohorts Overview":
    st.subheader("Cohort Sizes")
    _, _, cohort_counts = get_cohorts_pts_counts(db_path)
    st.dataframe(cohort_counts, use_container_width=True)
    df_download_button(cohort_counts, "cohort_sizes.csv", label="Download cohort sizes")

    st.subheader("Top Flagged Signals (global)")
    prr_min_o = st.number_input("PRR ≥ (overview)", min_value=0.0, value=2.0, step=0.5, key="o_prr")
    chi2_min_o = st.number_input("χ² ≥ (overview)", min_value=0.0, value=4.0, step=0.5, key="o_chi2")
    n_min_o = st.number_input("N ≥ (overview)", min_value=0, value=3, step=1, key="o_n")

    with st.spinner("Scanning all cohorts…"):
        top = fetch_top_signals(db_path, prr_min_o, chi2_min_o, n_min_o, limit=25)

    if top.empty:
        st.info("No flagged signals at current thresholds.")
    else:
        st.dataframe(top[["cohort","reaction_pt","N","PRR","PRR_LCL","PRR_UCL","chi2"]]
                     .round(3), use_container_width=True)
        df_download_button(top.round(4), "top_flagged_signals.csv", label="Download top signals")

st.caption("FAERS 2023 • Disproportionality analysis (PRR/ROR) • Haldane–Anscombe correction")
