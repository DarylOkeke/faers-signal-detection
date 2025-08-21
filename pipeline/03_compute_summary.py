#!/usr/bin/env python3
"""
FAERS Signal Detection Summary
Compute PRR, ROR, chi2, apply thresholds, and export CSV.
"""

import argparse
import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path

from stats import add_stats


def load_2x2_data(db_path, view_name):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    query = f"""
    SELECT cohort, reaction_pt, a, b, c, d
    FROM {view_name}
    ORDER BY cohort, reaction_pt
    """

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(query, conn)
    return df


def compute_summary(df, prr_min=2.0, chi2_min=4.0, n_min=3):
    print(f"Computing statistics for {len(df):,} cohort-reaction pairs...")
    result_df = add_stats(df, prr_min=prr_min, chi2_min=chi2_min, n_min=n_min)

    cols = [
        "cohort", "reaction_pt", "a", "b", "c", "d", "N",
        "PRR", "PRR_LCL", "PRR_UCL",
        "ROR", "ROR_LCL", "ROR_UCL",
        "chi2", "flagged", "unstable_den", "sparse_bg"
    ]
    return result_df[cols]


def save_summary(df, output_path):
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    numeric_cols = ["PRR", "PRR_LCL", "PRR_UCL", "ROR", "ROR_LCL", "ROR_UCL", "chi2"]
    for col in numeric_cols:
        df[col] = df[col].round(6)

    df.to_csv(output_path, index=False)
    print(f"✓ Saved summary to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Compute FAERS signal detection summary statistics")
    parser.add_argument("--db", required=True, help="Path to SQLite database")
    parser.add_argument("--view", default="v_signal_2x2_2023", help="Name of 2x2 view")
    parser.add_argument("--out", required=True, help="Output CSV file path")
    parser.add_argument("--prr-min", type=float, default=2.0)
    parser.add_argument("--chi2-min", type=float, default=4.0)
    parser.add_argument("--n-min", type=int, default=3)

    args = parser.parse_args()

    df = load_2x2_data(args.db, args.view)
    summary_df = compute_summary(df, args.prr_min, args.chi2_min, args.n_min)
    save_summary(summary_df, args.out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
