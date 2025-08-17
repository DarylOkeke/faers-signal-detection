#!/usr/bin/env python3
"""
Create Trimmed Decision Tables for MINOXIDIL Cardiac Endpoints

Focus = Minoxidil cohorts only (systemic always; topical optional).
Hydralazine is excluded by default (it’s a positive-control comparator and
should live in controls/validation, not the primary Minoxidil deliverable).

Author: FAERS Signal Detection Team
Date: August 2025
"""

import argparse
import pandas as pd
import os
import sys
from pathlib import Path

# Target cardiac endpoints in specified order
PT_ORDER = ['CARDIAC TAMPONADE', 'PERICARDIAL EFFUSION', 'PERICARDITIS', 'PLEURAL EFFUSION']

def load_summary_data(input_path):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Summary file not found: {input_path}")
    df = pd.read_csv(input_path)
    print(f"✓ Loaded {len(df):,} rows from {input_path}")
    return df

def filter_to_targets(df, include_topical=False, include_hydralazine=False):
    """
    Keep only the cohorts you want to show in the trimmed deliverable.
    By default: MINOXIDIL_SYSTEMIC (and optionally MINOXIDIL_TOPICAL).
    HYDRALAZINE is OFF by default.
    """
    target_cohorts = ['MINOXIDIL_SYSTEMIC']
    if include_topical:
        target_cohorts.append('MINOXIDIL_TOPICAL')
    if include_hydralazine:
        target_cohorts.append('HYDRALAZINE')

    filtered_df = df[
        (df['cohort'].isin(target_cohorts)) &
        (df['reaction_pt'].isin(PT_ORDER))
    ].copy()
    print(f"✓ Filtered to {len(filtered_df)} rows for target cohorts and cardiac endpoints")
    return filtered_df

def ensure_complete_matrix(df, include_topical=False, include_hydralazine=False):
    """
    Ensure all (cohort, reaction_pt) combos exist; fill missing with zeros.
    """
    cohorts = ['MINOXIDIL_SYSTEMIC']
    if include_topical:
        cohorts.append('MINOXIDIL_TOPICAL')
    if include_hydralazine:
        cohorts.append('HYDRALAZINE')

    complete_index = pd.MultiIndex.from_product([cohorts, PT_ORDER], names=['cohort','reaction_pt'])
    df_indexed = df.set_index(['cohort','reaction_pt'])
    complete_df = df_indexed.reindex(complete_index)

    fill_values = {
        'a': 0, 'b': 0, 'c': 0, 'd': 0, 'N': 0,
        'PRR': 0.0, 'PRR_LCL': 0.0, 'PRR_UCL': 0.0,
        'ROR': 0.0, 'ROR_LCL': 0.0, 'ROR_UCL': 0.0,
        'chi2': 0.0, 'flagged': False
    }
    for col, val in fill_values.items():
        if col in complete_df.columns:
            complete_df[col] = complete_df[col].fillna(val)

    complete_df = complete_df.reset_index()
    print(f"✓ Ensured complete matrix: {len(complete_df)} rows")
    return complete_df

def add_decision_columns(df):
    df['decision'] = df['flagged'].apply(lambda x: 'Reject H0 (signal)' if x else 'Fail to reject H0')
    interpretations = []
    for _, row in df.iterrows():
        cohort, pt = row['cohort'], row['reaction_pt']
        prr, lcl, ucl = row['PRR'], row['PRR_LCL'], row['PRR_UCL']
        n = int(row['N']) if 'N' in row and not pd.isna(row['N']) else 0
        if row['flagged']:
            txt = f"{cohort}: Disproportionate reporting for {pt} (PRR={prr:.1f}, 95% CI {lcl:.1f}-{ucl:.1f}, N={n})"
        else:
            txt = f"{cohort}: No disproportionate reporting for {pt} (PRR={prr:.1f}, N={n})"
        interpretations.append(txt)
    df['interpretation'] = interpretations
    return df

def sort_results(df):
    df['reaction_pt_cat'] = pd.Categorical(df['reaction_pt'], categories=PT_ORDER, ordered=True)
    out = df.sort_values(['cohort','reaction_pt_cat']).drop(columns=['reaction_pt_cat'])
    return out

def trim_columns(df):
    cols = ['cohort','reaction_pt','N','PRR','PRR_LCL','PRR_UCL','chi2','flagged','decision','interpretation']
    return df[cols]

def save_csv(df, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    for col in ['PRR','PRR_LCL','PRR_UCL','chi2']:
        if col in out.columns:
            out[col] = out[col].round(3)
    out.to_csv(output_path, index=False)
    print(f"✓ Saved trimmed CSV to: {output_path}")

def save_markdown(df, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    for col in ['PRR','PRR_LCL','PRR_UCL','chi2']:
        if col in out.columns:
            out[col] = out[col].round(3)

    md = ["# MINOXIDIL Cardiac Endpoints Signal Detection Results", ""]
    headers = out.columns.tolist()
    md.append("| " + " | ".join(headers) + " |")
    md.append("|" + "|".join([" --- "]*len(headers)) + "|")
    for _, row in out.iterrows():
        md.append("| " + " | ".join(str(v) for v in row.values) + " |")

    md += [
        "", "## Interpretation",
        "- **Reject H0 (signal)**: Statistically significant disproportionate reporting detected",
        "- **Fail to reject H0**: No significant disproportionate reporting detected",
        "", "**Flagging Criteria**: PRR ≥ 2.0, χ² ≥ 4.0, N ≥ 3", ""
    ]
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"✓ Saved Markdown table to: {output_path}")

def print_validation(df, include_topical=False, include_hydralazine=False):
    print("\n" + "="*80)
    print("TRIMMED TABLE VALIDATION")
    print("="*80)
    print("\nTable Preview:")
    print(df.to_string(index=False))

    # Expected rows
    expected = 4  # systemic always
    sys_rows = (df['cohort'] == 'MINOXIDIL_SYSTEMIC').sum()
    print(f"✓ MINOXIDIL_SYSTEMIC rows: {sys_rows} (expected: 4)")
    assert sys_rows == 4, f"Expected 4 MINOXIDIL_SYSTEMIC rows, got {sys_rows}"

    if include_topical:
        expected += 4
        top_rows = (df['cohort'] == 'MINOXIDIL_TOPICAL').sum()
        print(f"✓ MINOXIDIL_TOPICAL rows: {top_rows} (expected: 4)")
        assert top_rows == 4, f"Expected 4 MINOXIDIL_TOPICAL rows, got {top_rows}"

    if include_hydralazine:
        expected += 4
        hyd_rows = (df['cohort'] == 'HYDRALAZINE').sum()
        print(f"✓ HYDRALAZINE rows: {hyd_rows} (expected: 4)")
        assert hyd_rows == 4, f"Expected 4 HYDRALAZINE rows, got {hyd_rows}"

    print(f"✓ Total rows: {len(df)} (expected: {expected})")
    assert len(df) == expected, f"Expected {expected} total rows, got {len(df)}"

    flagged_df = df[df['flagged'] == True]
    if len(flagged_df) > 0:
        print(f"\n🚨 Flagged Signals ({len(flagged_df)}):")
        for _, r in flagged_df.iterrows():
            print(f"   {r['cohort']} + {r['reaction_pt']}: N={r['N']}, PRR={r['PRR']:.1f}")
    else:
        print("\n⚪ No flagged signals detected")
    print("\n✓ All validation checks passed!")

def main():
    parser = argparse.ArgumentParser(description="Create trimmed decision tables for MINOXIDIL cardiac endpoints")
    parser.add_argument('--in', dest='input_path', required=True, help='Input summary CSV path')
    parser.add_argument('--out', dest='output_path', required=True, help='Output CSV path')
    parser.add_argument('--include-topical', action='store_true', help='Include MINOXIDIL_TOPICAL as comparator')
    parser.add_argument('--include-hydralazine', action='store_true', default=False,
                        help='Include HYDRALAZINE comparator (default: False)')
    args = parser.parse_args()

    print("="*80)
    print("MINOXIDIL CARDIAC ENDPOINTS TRIMMED TABLE GENERATION")
    print("="*80)
    print(f"Input: {args.input_path}")
    print(f"Output: {args.output_path}")
    print(f"Include topical: {args.include_topical}")
    print(f"Include hydralazine: {args.include_hydralazine}")

    try:
        df = load_summary_data(args.input_path)
        filtered = filter_to_targets(df, args.include_topical, args.include_hydralazine)
        completed = ensure_complete_matrix(filtered, args.include_topical, args.include_hydralazine)
        decided = add_decision_columns(completed)
        sorted_df = sort_results(decided)
        final_df = trim_columns(sorted_df)

        save_csv(final_df, args.output_path)
        save_markdown(final_df, args.output_path.replace('.csv', '.md'))
        print_validation(final_df, args.include_topical, args.include_hydralazine)

        print("\n" + "="*80)
        print("TRIMMED TABLE GENERATION COMPLETE")
        print("="*80)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback; traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
