#!/usr/bin/env python3
"""
Method validation for the FAERS disproportionality pipeline.

Pre-specified control checks run against the live DuckDB database:
  - Positive control: CIPROFLOXACIN → TENDON RUPTURE  (expect signal)
  - Negative control: METFORMIN     → ALOPECIA         (expect no signal)

Run via pytest (make test) or directly as a script.
Both tests must pass before trusting pipeline output on any drug-event pair.
"""

import argparse
import csv
import math
import os
from textwrap import dedent

import duckdb
import pytest

DEFAULT_DB   = "data/faers+medicare.duckdb"
DEFAULT_VIEW = "v_events_2023_cohorts"
DEFAULT_OUT  = "results/tables/method_controls.csv"

PRR_MIN  = 2.0
CHI2_MIN = 4.0
N_MIN    = 3


# ── Database helpers ─────────────────────────────────────────────────────────

def get_connection(db_path=DEFAULT_DB):
    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            "Run pipeline/01_create_views.py first."
        )
    return duckdb.connect(db_path, read_only=True)


def get_2x2(conn, ingredient, reaction_pt, view):
    ingredient  = ingredient.upper().strip()
    reaction_pt = reaction_pt.upper().strip()

    def fetch_int(sql, params=()):
        row = conn.execute(sql, list(params)).fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    a = fetch_int(
        f"SELECT COUNT(DISTINCT primaryid) FROM {view} "
        "WHERE UPPER(ingredient_std) = ? AND UPPER(reaction_pt) = ?",
        (ingredient, reaction_pt),
    )
    tot_ing = fetch_int(
        f"SELECT COUNT(DISTINCT primaryid) FROM {view} "
        "WHERE UPPER(ingredient_std) = ?",
        (ingredient,),
    )
    tot_evt = fetch_int(
        f"SELECT COUNT(DISTINCT primaryid) FROM {view} "
        "WHERE UPPER(reaction_pt) = ?",
        (reaction_pt,),
    )
    grand = fetch_int(f"SELECT COUNT(DISTINCT primaryid) FROM {view}")

    b = max(tot_ing - a, 0)
    c = max(tot_evt - a, 0)
    d = max(grand - (a + b + c), 0)
    return a, b, c, d, grand


def prr_stats(a, b, c, d):
    aa, bb, cc, dd = map(float, (a, b, c, d))
    if min(aa, bb, cc, dd) == 0.0:
        aa += 0.5; bb += 0.5; cc += 0.5; dd += 0.5

    num = aa / (aa + bb) if (aa + bb) > 0 else 0.0
    den = cc / (cc + dd) if (cc + dd) > 0 else 0.0
    prr = (num / den) if den > 0 else 0.0

    if prr > 0 and (aa + bb) > 0 and (cc + dd) > 0:
        se  = math.sqrt((1/aa) - (1/(aa+bb)) + (1/cc) - (1/(cc+dd)))
        lcl = math.exp(math.log(prr) - 1.96 * se)
        ucl = math.exp(math.log(prr) + 1.96 * se)
    else:
        lcl, ucl = 0.0, 0.0

    numerator = (aa*dd - bb*cc)**2 * (aa + bb + cc + dd)
    denom     = (aa + bb) * (cc + dd) * (aa + cc) * (bb + dd)
    chi2      = (numerator / denom) if denom > 0 else 0.0

    return prr, lcl, ucl, chi2


def run_check(conn, ingredient, reaction_pt, expect_signal, view=DEFAULT_VIEW):
    a, b, c, d, grand = get_2x2(conn, ingredient, reaction_pt, view)
    prr, lcl, ucl, chi2 = prr_stats(a, b, c, d)
    flagged = (a >= N_MIN) and (prr >= PRR_MIN) and (chi2 >= CHI2_MIN)
    passed  = flagged if expect_signal else not flagged
    return {
        "ingredient": ingredient,
        "reaction":   reaction_pt,
        "a": a, "b": b, "c": c, "d": d,
        "grand": grand,
        "PRR":     prr,
        "PRR_LCL": lcl,
        "PRR_UCL": ucl,
        "chi2":    chi2,
        "expected": "SIGNAL" if expect_signal else "NO SIGNAL",
        "result":   "PASS" if passed else "FAIL",
    }


# ── pytest test functions ────────────────────────────────────────────────────

def test_positive_control():
    """Ciprofloxacin → Tendon rupture must meet all three signal thresholds."""
    try:
        conn = get_connection()
    except FileNotFoundError as e:
        pytest.skip(str(e))

    r = run_check(conn, "CIPROFLOXACIN", "TENDON RUPTURE", expect_signal=True)
    conn.close()
    assert r["result"] == "PASS", (
        f"Positive control FAILED — CIPROFLOXACIN→TENDON RUPTURE: "
        f"PRR={r['PRR']:.2f}, χ²={r['chi2']:.2f}, N={r['a']}"
    )


def test_negative_control():
    """Metformin → Alopecia must NOT meet signal thresholds."""
    try:
        conn = get_connection()
    except FileNotFoundError as e:
        pytest.skip(str(e))

    r = run_check(conn, "METFORMIN", "ALOPECIA", expect_signal=False)
    conn.close()
    assert r["result"] == "PASS", (
        f"Negative control FAILED — METFORMIN→ALOPECIA: "
        f"PRR={r['PRR']:.2f}, χ²={r['chi2']:.2f}, N={r['a']}"
    )


# ── CLI entry point ──────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Method control checks for FAERS PRR pipeline"
    )
    ap.add_argument("--db",   default=DEFAULT_DB)
    ap.add_argument("--view", default=DEFAULT_VIEW)
    ap.add_argument("--out",  default=DEFAULT_OUT)
    args = ap.parse_args()

    conn = get_connection(args.db)
    results = [
        run_check(conn, "CIPROFLOXACIN", "TENDON RUPTURE", True,  args.view),
        run_check(conn, "METFORMIN",     "ALOPECIA",       False, args.view),
    ]
    conn.close()

    for r in results:
        print(dedent(f"""
        {r['ingredient']} → {r['reaction']}
          a={r['a']}, b={r['b']}, c={r['c']}, d={r['d']}, grand={r['grand']}
          PRR={r['PRR']:.3f} (95% CI {r['PRR_LCL']:.3f}–{r['PRR_UCL']:.3f}), χ²={r['chi2']:.3f}
          Expected: {r['expected']} → Result: {r['result']}
        """).strip())

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nResults saved to {args.out}")

    all_pass = all(r["result"] == "PASS" for r in results)
    return 0 if all_pass else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
