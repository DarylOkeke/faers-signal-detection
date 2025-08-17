#!/usr/bin/env python3
"""
FAERS Signal Detection Summary Computation

This module computes PRR, ROR, and chi-square statistics from 2x2 contingency tables
with proper Haldane-Anscombe correction for confidence intervals.

Author: FAERS Signal Detection Team
Date: August 2025
"""

import argparse
import sqlite3
import pandas as pd
import numpy as np
import math
import os
import sys
from pathlib import Path

def apply_haldane_correction(a, b, c, d):
    """
    Apply Haldane-Anscombe correction only when any cell is zero.
    
    Args:
        a, b, c, d: Raw cell counts
        
    Returns:
        tuple: (a', b', c', d') corrected counts for statistics
    """
    if min(a, b, c, d) == 0:
        return a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return float(a), float(b), float(c), float(d)

def compute_prr_stats(a_prime, b_prime, c_prime, d_prime):
    """
    Compute PRR and 95% confidence interval.
    
    Args:
        a_prime, b_prime, c_prime, d_prime: Corrected cell counts
        
    Returns:
        tuple: (PRR, PRR_LCL, PRR_UCL)
    """
    # PRR = [a'/(a'+b')] / [c'/(c'+d')]
    p1 = a_prime / (a_prime + b_prime)
    p0 = c_prime / (c_prime + d_prime)
    
    if p0 == 0:
        return float('inf'), float('inf'), float('inf')
    
    prr = p1 / p0
    
    # Standard error of ln(PRR)
    ln_prr_se = math.sqrt(
        (1 / a_prime) - (1 / (a_prime + b_prime)) + 
        (1 / c_prime) - (1 / (c_prime + d_prime))
    )
    
    # 95% CI
    ln_prr = math.log(prr)
    prr_lcl = math.exp(ln_prr - 1.96 * ln_prr_se)
    prr_ucl = math.exp(ln_prr + 1.96 * ln_prr_se)
    
    return prr, prr_lcl, prr_ucl

def compute_ror_stats(a_prime, b_prime, c_prime, d_prime):
    """
    Compute ROR and 95% confidence interval.
    
    Args:
        a_prime, b_prime, c_prime, d_prime: Corrected cell counts
        
    Returns:
        tuple: (ROR, ROR_LCL, ROR_UCL)
    """
    # ROR = (a'/b') / (c'/d')
    if b_prime == 0 or d_prime == 0:
        return float('inf'), float('inf'), float('inf')
    
    ror = (a_prime / b_prime) / (c_prime / d_prime)
    
    # Standard error of ln(ROR)
    ln_ror_se = math.sqrt(1/a_prime + 1/b_prime + 1/c_prime + 1/d_prime)
    
    # 95% CI
    ln_ror = math.log(ror)
    ror_lcl = math.exp(ln_ror - 1.96 * ln_ror_se)
    ror_ucl = math.exp(ln_ror + 1.96 * ln_ror_se)
    
    return ror, ror_lcl, ror_ucl

def compute_chi2_pearson(a_prime, b_prime, c_prime, d_prime):
    """
    Compute Pearson chi-square statistic (no Yates correction).
    
    Args:
        a_prime, b_prime, c_prime, d_prime: Corrected cell counts
        
    Returns:
        float: Chi-square statistic
    """
    n = a_prime + b_prime + c_prime + d_prime
    
    if n == 0:
        return 0.0
    
    # Pearson chi-square without Yates correction
    numerator = (a_prime * d_prime - b_prime * c_prime) ** 2 * n
    denominator = (a_prime + b_prime) * (c_prime + d_prime) * (a_prime + c_prime) * (b_prime + d_prime)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

def compute_statistics_row(row):
    """
    Compute all statistics for a single 2x2 table row.
    
    Args:
        row: pandas Series with columns a, b, c, d
        
    Returns:
        dict: Statistics results
    """
    a, b, c, d = int(row['a']), int(row['b']), int(row['c']), int(row['d'])
    
    # Apply Haldane-Anscombe correction for statistics
    a_prime, b_prime, c_prime, d_prime = apply_haldane_correction(a, b, c, d)
    
    # Compute PRR
    prr, prr_lcl, prr_ucl = compute_prr_stats(a_prime, b_prime, c_prime, d_prime)
    
    # Compute ROR
    ror, ror_lcl, ror_ucl = compute_ror_stats(a_prime, b_prime, c_prime, d_prime)
    
    # Compute chi-square
    chi2 = compute_chi2_pearson(a_prime, b_prime, c_prime, d_prime)
    
    return {
        'PRR': prr,
        'PRR_LCL': prr_lcl,
        'PRR_UCL': prr_ucl,
        'ROR': ror,
        'ROR_LCL': ror_lcl,
        'ROR_UCL': ror_ucl,
        'chi2': chi2
    }

def load_2x2_data(db_path, view_name):
    """
    Load 2x2 contingency table data from database view.
    
    Args:
        db_path: Path to SQLite database
        view_name: Name of the 2x2 view
        
    Returns:
        pandas.DataFrame: 2x2 table data
    """
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
    """
    Compute summary statistics for all 2x2 tables.
    
    Args:
        df: DataFrame with 2x2 table data
        prr_min: Minimum PRR for flagging
        chi2_min: Minimum chi-square for flagging
        n_min: Minimum case count for flagging
        
    Returns:
        pandas.DataFrame: Summary with all statistics
    """
    print(f"Computing statistics for {len(df):,} cohort-reaction pairs...")
    
    # Compute statistics for each row
    stats_list = []
    for idx, row in df.iterrows():
        stats = compute_statistics_row(row)
        stats_list.append(stats)
        
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1:,} rows...")
    
    # Convert to DataFrame and merge with original data
    stats_df = pd.DataFrame(stats_list)
    result_df = pd.concat([df, stats_df], axis=1)
    
    # Add N column (raw case count)
    result_df['N'] = result_df['a']
    
    # Apply flagging criteria
    result_df['flagged'] = (
        (result_df['PRR'] >= prr_min) & 
        (result_df['chi2'] >= chi2_min) & 
        (result_df['N'] >= n_min)
    )
    
    # Reorder columns as specified
    column_order = [
        'cohort', 'reaction_pt', 'a', 'b', 'c', 'd', 'N',
        'PRR', 'PRR_LCL', 'PRR_UCL', 'ROR', 'ROR_LCL', 'ROR_UCL', 
        'chi2', 'flagged'
    ]
    
    result_df = result_df[column_order]
    
    return result_df

def save_summary(df, output_path):
    """
    Save summary results to CSV file.
    
    Args:
        df: Summary DataFrame
        output_path: Output CSV file path
    """
    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Round numeric columns for cleaner output
    numeric_cols = ['PRR', 'PRR_LCL', 'PRR_UCL', 'ROR', 'ROR_LCL', 'ROR_UCL', 'chi2']
    for col in numeric_cols:
        df[col] = df[col].round(6)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"✓ Saved summary to: {output_path}")

def print_summary_stats(df):
    """Print summary statistics about the results."""
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    # Overall stats
    total_pairs = len(df)
    flagged_count = df['flagged'].sum()
    
    print(f"Total cohort-reaction pairs: {total_pairs:,}")
    print(f"Flagged signals: {flagged_count:,} ({flagged_count/total_pairs*100:.1f}%)")
    
    # Cohort breakdown
    print(f"\nCohort breakdown:")
    cohort_stats = df.groupby('cohort').agg({
        'a': ['count', 'sum', 'mean'],
        'flagged': 'sum'
    }).round(2)
    cohort_stats.columns = ['n_reactions', 'total_events', 'avg_events', 'n_flagged']
    print(cohort_stats)
    
    # Top flagged signals
    if flagged_count > 0:
        print(f"\nTop 10 flagged signals (by PRR):")
        top_signals = df[df['flagged']].nlargest(10, 'PRR')[
            ['cohort', 'reaction_pt', 'N', 'PRR', 'chi2']
        ]
        print(top_signals.to_string(index=False))
    
    # Target endpoint check
    target_reactions = ['PERICARDIAL EFFUSION', 'PERICARDITIS', 'CARDIAC TAMPONADE', 'PLEURAL EFFUSION']
    target_df = df[df['reaction_pt'].isin(target_reactions)]
    
    if len(target_df) > 0:
        print(f"\nTarget cardiac endpoints:")
        target_summary = target_df[['cohort', 'reaction_pt', 'N', 'PRR', 'chi2', 'flagged']]
        print(target_summary.to_string(index=False))
        
        # Specific check for MINOXIDIL_SYSTEMIC + PERICARDIAL EFFUSION
        minox_pe = df[
            (df['cohort'] == 'MINOXIDIL_SYSTEMIC') & 
            (df['reaction_pt'] == 'PERICARDIAL EFFUSION')
        ]
        
        if len(minox_pe) > 0:
            row = minox_pe.iloc[0]
            print(f"\n✓ MINOXIDIL_SYSTEMIC + PERICARDIAL EFFUSION found:")
            print(f"   N={row['N']}, PRR={row['PRR']:.3f}, chi2={row['chi2']:.3f}, flagged={row['flagged']}")
        else:
            print(f"\n⚠ MINOXIDIL_SYSTEMIC + PERICARDIAL EFFUSION not found")

def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Compute FAERS signal detection summary statistics"
    )
    parser.add_argument('--db', required=True, help='Path to SQLite database')
    parser.add_argument('--view', default='v_signal_2x2_2023', help='Name of 2x2 view')
    parser.add_argument('--out', required=True, help='Output CSV file path')
    parser.add_argument('--prr-min', type=float, default=2.0, help='Minimum PRR for flagging')
    parser.add_argument('--chi2-min', type=float, default=4.0, help='Minimum chi-square for flagging')
    parser.add_argument('--n-min', type=int, default=3, help='Minimum case count for flagging')
    
    args = parser.parse_args()
    
    print("="*80)
    print("FAERS SIGNAL DETECTION SUMMARY COMPUTATION")
    print("="*80)
    print(f"Database: {args.db}")
    print(f"View: {args.view}")
    print(f"Output: {args.out}")
    print(f"Flagging criteria: PRR≥{args.prr_min}, χ²≥{args.chi2_min}, N≥{args.n_min}")
    
    try:
        # Load 2x2 data
        df = load_2x2_data(args.db, args.view)
        print(f"✓ Loaded {len(df):,} cohort-reaction pairs from {args.view}")
        
        # Compute statistics
        summary_df = compute_summary(df, args.prr_min, args.chi2_min, args.n_min)
        
        # Save results
        save_summary(summary_df, args.out)
        
        # Print summary statistics
        print_summary_stats(summary_df)
        
        print("\n" + "="*80)
        print("COMPUTATION COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
