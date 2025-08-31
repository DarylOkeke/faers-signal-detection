#!/usr/bin/env python3
"""
Create Trimmed Decision Tables for MINOXIDIL Cardiac Endpoints

Focus = Minoxidil cohorts only (systemic always; topical optional).
Hydralazine is excluded by default (positive-control comparator).
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
    
    # Create markdown table
    md.append("| " + " | ".join(headers) + " |")
    md.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for _, row in out.iterrows():
        row_str = "| " + " | ".join(str(row[col]) for col in headers) + " |"
        md.append(row_str)
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(md))
    print(f"✓ Saved markdown to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Create trimmed decision tables for MINOXIDIL cardiac endpoints")
    parser.add_argument("--input", required=True, help="Input summary CSV file path")
    parser.add_argument("--output", required=True, help="Output trimmed CSV file path")
    parser.add_argument("--include-topical", action="store_true", help="Include MINOXIDIL_TOPICAL cohort")
    parser.add_argument("--include-hydralazine", action="store_true", help="Include HYDRALAZINE cohort")
    parser.add_argument("--markdown", help="Optional: save markdown output to this path")
    
    args = parser.parse_args()
    
    try:
        # Load and process data
        df = load_summary_data(args.input)
        df = filter_to_targets(df, args.include_topical, args.include_hydralazine)
        df = ensure_complete_matrix(df, args.include_topical, args.include_hydralazine)
        df = add_decision_columns(df)
        df = sort_results(df)
        df = trim_columns(df)
        
        # Save outputs
        save_csv(df, args.output)
        if args.markdown:
            save_markdown(df, args.markdown)
        
        print(f"✓ Processing complete. {len(df)} rows in final output.")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
