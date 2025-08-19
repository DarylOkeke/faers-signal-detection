# faers_core/stats.py
"""
FAERS Signal Detection Statistics Core
Shared by both CLI summary and Streamlit app.
"""

import math
import numpy as np
import pandas as pd


def apply_haldane_if_zero(a, b, c, d):
    """Apply 0.5 continuity correction only if any cell is zero."""
    if min(a, b, c, d) == 0:
        return a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return float(a), float(b), float(c), float(d)


def prr_ci(a, b, c, d):
    """PRR and 95% CI using Wald on ln(PRR), with conditional Haldane."""
    a_, b_, c_, d_ = apply_haldane_if_zero(a, b, c, d)
    p1 = a_ / (a_ + b_)
    p0 = c_ / (c_ + d_)
    if p0 == 0:
        return float("inf"), float("inf"), float("inf")
    prr = p1 / p0
    se = math.sqrt((1 / a_) - (1 / (a_ + b_)) + (1 / c_) - (1 / (c_ + d_)))
    ln = math.log(prr)
    return prr, math.exp(ln - 1.96 * se), math.exp(ln + 1.96 * se)


def ror_ci(a, b, c, d):
    """ROR and 95% CI using Wald on ln(ROR), with conditional Haldane."""
    a_, b_, c_, d_ = apply_haldane_if_zero(a, b, c, d)
    if b_ == 0 or d_ == 0:
        return float("inf"), float("inf"), float("inf")
    ror = (a_ / b_) / (c_ / d_)
    se = math.sqrt(1 / a_ + 1 / b_ + 1 / c_ + 1 / d_)
    ln = math.log(ror)
    return ror, math.exp(ln - 1.96 * se), math.exp(ln + 1.96 * se)


def chi2_pearson(a, b, c, d):
    """Pearson chi-square on the (possibly corrected) table."""
    a_, b_, c_, d_ = apply_haldane_if_zero(a, b, c, d)
    n = a_ + b_ + c_ + d_
    if n == 0:
        return 0.0
    num = (a_ * d_ - b_ * c_) ** 2 * n
    den = (a_ + b_) * (c_ + d_) * (a_ + c_) * (b_ + d_)
    return 0.0 if den == 0 else num / den


def add_stats(df, prr_min=2.0, chi2_min=4.0, n_min=3):
    """
    Attach N, PRR, ROR, chi2, and flags to a 2x2 dataframe.
    Adds stability flags for denominator issues.
    """
    out = df.copy()
    if out.empty:
        return out.assign(
            N=[], PRR=[], PRR_LCL=[], PRR_UCL=[], ROR=[], ROR_LCL=[], ROR_UCL=[], chi2=[], flagged=[], unstable_den=[], sparse_bg=[]
        )

    out["N"] = out["a"].astype(int)

    prr_vals = out.apply(lambda r: prr_ci(r.a, r.b, r.c, r.d), axis=1, result_type="expand")
    out[["PRR", "PRR_LCL", "PRR_UCL"]] = prr_vals

    ror_vals = out.apply(lambda r: ror_ci(r.a, r.b, r.c, r.d), axis=1, result_type="expand")
    out[["ROR", "ROR_LCL", "ROR_UCL"]] = ror_vals

    out["chi2"] = out.apply(lambda r: chi2_pearson(r.a, r.b, r.c, r.d), axis=1)

    # Stability flags
    out["unstable_den"] = (out["c"] < 3) | (out["d"] < 3)
    out["sparse_bg"] = (out["c"] + out["d"]) < 50

    out["flagged"] = (out["PRR"] >= prr_min) & (out["chi2"] >= chi2_min) & (out["N"] >= n_min)
    return out
