#!/usr/bin/env python3
"""
Method Controls for FAERS Disproportionality

Positive control: CIPROFLOXACIN → TENDON RUPTURE (expect SIGNAL)
Negative control: METFORMIN     → ALOPECIA       (expect NO SIGNAL)

Outputs results to both console and CSV.
"""

import argparse
import math
import sqlite3
import csv
import os
from textwrap import dedent

DEFAULT_DB = "data/faers+medicare.db"
DEFAULT_VIEW = "v_events_2023_cohorts"
DEFAULT_OUT = "results/tables/method_controls.csv"

def _fetch_one_int(conn, sql, params=()):
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else 0

def get_2x2(conn, ingredient, reaction_pt, view):
    ingredient = ingredient.upper().strip()
    reaction_pt = reaction_pt.upper().strip()

    a_sql = f"""
        SELECT COUNT(DISTINCT primaryid) FROM {view}
        WHERE UPPER(ingredient_std) = ? AND UPPER(reaction_pt) = ?
    """
    a = _fetch_one_int(conn, a_sql, (ingredient, reaction_pt))

    tot_ing_sql = f"""
        SELECT COUNT(DISTINCT primaryid) FROM {view}
        WHERE UPPER(ingredient_std) = ?
    """
    tot_ing = _fetch_one_int(conn, tot_ing_sql, (ingredient,))

    tot_evt_sql = f"""
        SELECT COUNT(DISTINCT primaryid) FROM {view}
        WHERE UPPER(reaction_pt) = ?
    """
    tot_evt = _fetch_one_int(conn, tot_evt_sql, (reaction_pt,))

    grand_sql = f"SELECT COUNT(DISTINCT primaryid) FROM {view}"
    grand = _fetch_one_int(conn, grand_sql)

    b = max(tot_ing - a, 0)
    c = max(tot_evt - a, 0)
    d = max(grand - (a + b + c), 0)

    return a, b, c, d, grand

def prr_stats(a, b, c, d, continuity=True):
    aa, bb, cc, dd = map(float, (a, b, c, d))
    if continuity and min(aa, bb, cc, dd) == 0.0:
        aa += 0.5; bb += 0.5; cc += 0.5; dd += 0.5

    num = aa / (aa + bb) if (aa + bb) > 0 else 0.0
    den = cc / (cc + dd) if (cc + dd) > 0 else 0.0
    prr = (num / den) if den > 0 else 0.0

    if prr > 0 and (aa + bb) > 0 and (cc + dd) > 0:
        se = math.sqrt((1/aa) - (1/(aa + bb)) + (1/cc) - (1/(cc + dd)))
        lcl = math.exp(math.log(prr) - 1.96 * se)
        ucl = math.exp(math.log(prr) + 1.96 * se)
    else:
        lcl, ucl = 0.0, 0.0

    numerator = (aa*dd - bb*cc)**2 * (aa + bb + cc + dd)
    denom = (aa + bb) * (cc + dd) * (aa + cc) * (bb + dd)
    chi2 = (numerator / denom) if denom > 0 else 0.0

    return prr, lcl, ucl, chi2

def run_check(conn, ingredient, reaction_pt, expect_signal, prr_min, chi2_min, n_min, view):
    a, b, c, d, grand = get_2x2(conn, ingredient, reaction_pt, view)
    prr, lcl, ucl, chi2 = prr_stats(a, b, c, d, continuity=True)

    if expect_signal:
        passed = (a >= n_min) and (prr >= prr_min) and (chi2 >= chi2_min)
        expectation = "SIGNAL"
    else:
        passed = not ((a >= n_min) and (prr >= prr_min) and (chi2 >= chi2_min))
        expectation = "NO SIGNAL"

    return {
        "ingredient": ingredient,
        "reaction": reaction_pt,
        "a": a, "b": b, "c": c, "d": d,
        "grand": grand,
        "PRR": prr, "PRR_LCL": lcl, "PRR_UCL": ucl,
        "chi2": chi2,
        "expected": expectation,
        "result": "PASS" if passed else "FAIL"
    }

def main():
    ap = argparse.ArgumentParser(description="Method control checks for FAERS PRR pipeline")
    ap.add_argument("--db", default=DEFAULT_DB, help="Path to SQLite DB")
    ap.add_argument("--view", default=DEFAULT_VIEW, help="Source view")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Output CSV path")
    ap.add_argument("--prr-min", type=float, default=2.0)
    ap.add_argument("--chi2-min", type=float, default=4.0)
    ap.add_argument("--n-min", type=int, default=3)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    with sqlite3.connect(args.db) as conn:
        results = []
        results.append(run_check(conn, "CIPROFLOXACIN", "TENDON RUPTURE", True, args.prr_min, args.chi2_min, args.n_min, args.view))
        results.append(run_check(conn, "METFORMIN", "ALOPECIA", False, args.prr_min, args.chi2_min, args.n_min, args.view))

    # Print to console
    for r in results:
        print(dedent(f"""
        {r['ingredient']} → {r['reaction']}
          a={r['a']}, b={r['b']}, c={r['c']}, d={r['d']}, grand={r['grand']}
          PRR={r['PRR']:.3f} (95% CI {r['PRR_LCL']:.3f}-{r['PRR_UCL']:.3f}), χ²={r['chi2']:.3f}
          Expect: {r['expected']} → Result: {r['result']}
        """).strip())

    # Save CSV
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Results saved to {args.out}")

if __name__ == "__main__":
    import sys
    sys.exit(main())
