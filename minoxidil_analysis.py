#!/usr/bin/env python3
"""
FAERS Signal Detection Analysis: Minoxidil Pericardial Effusion Hypothesis Testing

This script performs a pharmacovigilance analysis comparing:
- Oral vs Topical Minoxidil for pericardial effusion and related cardiovascular events
- Minoxidil vs Hydralazine (comparator drug)

Uses proportional reporting ratios (PRR) and reporting odds ratios (ROR) 
with chi-square statistics for signal detection.

Author: FAERS Signal Detection Team
Date: August 2025
"""

import sqlite3
import pandas as pd
import numpy as np
from math import log, sqrt, exp
import os
import sys

# ============================================================================
# CONFIGURATION
# ============================================================================

# Database configuration
DB_PATH = "data/faers+medicare.db"

# Analysis parameters
YEAR_WINDOW = (2023, 2023)
ROLE = "PS"  # Primary Suspect drugs only
TARGET_ING = "MINOXIDIL"
COMPARATOR_ING = "HYDRALAZINE"  # Fixed: use actual name in database (not HYDROCHLORIDE)

# Endpoints of interest
PRIMARY_PTS = ["PERICARDIAL EFFUSION"]
SECONDARY_PTS = ["PERICARDITIS", "CARDIAC TAMPONADE", "PLEURAL EFFUSION"]
ALL_PTS = PRIMARY_PTS + SECONDARY_PTS

# Signal detection thresholds
FLAG_RULE = {
    "prr_min": 2.0,     # PRR >= 2.0
    "chi2_min": 4.0,    # Chi-square >= 4.0
    "n_min": 3          # At least 3 cases
}

# Route classification keywords (case-insensitive contains)
ORAL_KEYS = ["ORAL", "PO"]
TOPICAL_KEYS = ["TOPICAL", "CUTANEOUS", "SCALP"]
UNKNOWN_KEYS = ["UNKNOWN", "UNK"]  # Handle unknown routes separately

# ============================================================================
# STATISTICAL FUNCTIONS
# ============================================================================

def prr_ror_chi2(a, b, c, d, yates=True):
    """
    Calculate PRR, ROR, and Chi-square statistics with confidence intervals.
    
    2x2 contingency table:
                Drug    Not Drug
    Event        a         c
    Not Event    b         d
    
    Args:
        a, b, c, d: Cell counts (integers)
        yates: Apply Yates continuity correction for chi-square
        
    Returns:
        dict: Statistical measures with confidence intervals
    """
    # Convert to integers and check for problematic cases
    a, b, c, d = map(int, (a, b, c, d))
    
    # Check for completely empty drug or event groups
    if (a + b) == 0:  # No drug cases at all
        return {
            "PRR": float('nan'), "PRR_LCL": float('nan'), "PRR_UCL": float('nan'),
            "ROR": float('nan'), "ROR_LCL": float('nan'), "ROR_UCL": float('nan'),
            "chi2": float('nan')
        }
    
    if (a + c) == 0:  # No event cases at all
        return {
            "PRR": 0.0, "PRR_LCL": 0.0, "PRR_UCL": 0.0,
            "ROR": 0.0, "ROR_LCL": 0.0, "ROR_UCL": 0.0,
            "chi2": 0.0
        }
    
    # Apply Haldane-Anscombe correction only if any cell is zero
    if min(a, b, c, d) == 0:
        a += 0.5; b += 0.5; c += 0.5; d += 0.5

    # Proportional Reporting Ratio (PRR) and 95% CI
    prr = (a / (a + b)) / (c / (c + d))
    var_ln_prr = (1/a) - (1/(a+b)) + (1/c) - (1/(c+d))
    se_ln_prr = sqrt(max(var_ln_prr, 0))
    prr_lcl = exp(log(prr) - 1.96 * se_ln_prr)
    prr_ucl = exp(log(prr) + 1.96 * se_ln_prr)

    # Reporting Odds Ratio (ROR) and 95% CI
    ror = (a / b) / (c / d)
    var_ln_ror = (1/a) + (1/b) + (1/c) + (1/d)
    se_ln_ror = sqrt(max(var_ln_ror, 0))
    ror_lcl = exp(log(ror) - 1.96 * se_ln_ror)
    ror_ucl = exp(log(ror) + 1.96 * se_ln_ror)

    # Chi-square test (with optional Yates correction)
    n = a + b + c + d
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    exp_a = row1 * col1 / n
    exp_b = row1 * col2 / n
    exp_c = row2 * col1 / n
    exp_d = row2 * col2 / n

    def chi2_cell(observed, expected):
        if yates and n > 1:
            return (abs(observed - expected) - 0.5)**2 / expected
        return (observed - expected)**2 / expected

    chi2 = (chi2_cell(a, exp_a) + chi2_cell(b, exp_b) + 
            chi2_cell(c, exp_c) + chi2_cell(d, exp_d))

    return {
        "PRR": prr, "PRR_LCL": prr_lcl, "PRR_UCL": prr_ucl,
        "ROR": ror, "ROR_LCL": ror_lcl, "ROR_UCL": ror_ucl,
        "chi2": chi2
    }

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def build_route_sets(drug_ps_df, ingredient_std, route_keys):
    """
    Build sets of case IDs where drug matches ingredient and route contains keywords.
    
    Args:
        drug_ps_df: DataFrame with PS drug data
        ingredient_std: Target ingredient name
        route_keys: List of route keywords to match
        
    Returns:
        set: Case IDs matching criteria
    """
    mask_ing = (drug_ps_df["ingredient_std"] == ingredient_std)
    
    # Handle null routes and make case-insensitive
    route_col = drug_ps_df["route"].fillna("").str.upper()
    route_hit = pd.Series(False, index=drug_ps_df.index)
    
    for keyword in route_keys:
        route_hit = route_hit | route_col.str.contains(keyword.upper(), na=False)
    
    matching_cases = drug_ps_df.loc[mask_ing & route_hit, "caseid"].unique()
    return set(matching_cases)

def counts_for_drug_pt(events_df, drug_ingredient, preferred_term, restrict_caseids=None):
    """
    Build 2x2 contingency table for drug-event combination at case level.
    
    Args:
        events_df: Events DataFrame (case-level unique)
        drug_ingredient: Target drug ingredient
        preferred_term: Target adverse event (PT)
        restrict_caseids: Optional set to restrict analysis to specific cases
        
    Returns:
        tuple: (a, b, c, d) cell counts for 2x2 table
    """
    # Find cases with drug and event
    cases_with_drug = set(events_df.loc[
        events_df["ingredient_std"] == drug_ingredient, "caseid"
    ].unique())
    
    cases_with_event = set(events_df.loc[
        events_df["reaction_pt"] == preferred_term, "caseid"
    ].unique())

    # Apply case restrictions if specified
    if restrict_caseids is not None:
        cases_with_drug = cases_with_drug & restrict_caseids

    # Get universe of cases (all or restricted)
    all_cases = set(events_df["caseid"].unique())
    if restrict_caseids is not None:
        all_cases = all_cases & restrict_caseids

    # Build 2x2 table
    a = len(cases_with_drug & cases_with_event)      # Drug + Event
    b = len(cases_with_drug - cases_with_event)      # Drug, No Event  
    c = len(cases_with_event - cases_with_drug)      # No Drug + Event
    d = len(all_cases - (cases_with_drug | cases_with_event))  # No Drug, No Event

    return a, b, c, d

def run_analysis_panel(events_df, drug_ingredient, preferred_terms, 
                      label, restrict_caseids=None):
    """
    Run complete analysis panel for one drug across multiple endpoints.
    
    Args:
        events_df: Events DataFrame
        drug_ingredient: Target drug
        preferred_terms: List of PTs to analyze
        label: Analysis set label
        restrict_caseids: Optional case restrictions
        
    Returns:
        DataFrame: Results with statistics and flags
    """
    results = []
    
    for pt in preferred_terms:
        a, b, c, d = counts_for_drug_pt(events_df, drug_ingredient, pt, restrict_caseids)
        stats = prr_ror_chi2(a, b, c, d)
        
        results.append({
            "analysis_set": label,
            "drug": drug_ingredient,
            "pt": pt,
            "a": a, "b": b, "c": c, "d": d,
            **stats
        })
    
    results_df = pd.DataFrame(results)
    
    # Apply flagging criteria
    results_df["flag"] = (
        (results_df["PRR"] >= FLAG_RULE["prr_min"]) & 
        (results_df["chi2"] >= FLAG_RULE["chi2_min"]) & 
        (results_df["a"] >= FLAG_RULE["n_min"])
    )
    
    return results_df.sort_values(["pt"])

# ============================================================================
# DATA LOADING
# ============================================================================

def load_faers_data(db_path, year_window):
    """Load and validate FAERS data from SQLite database."""
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    print(f"Loading FAERS data from: {db_path}")
    print(f"Year window: {year_window[0]}-{year_window[1]}")
    
    with sqlite3.connect(db_path) as conn:
        # Load unique events (case × ingredient × PT level)
        events_query = """
            SELECT caseid, primaryid, ingredient_std, reaction_pt, 
                   year, quarter, sex, age_yrs, serious_any
            FROM faers_events_2023_unique
            WHERE year BETWEEN ? AND ?
        """
        
        events_df = pd.read_sql_query(events_query, conn, params=year_window)
        print(f"✓ Loaded events: {len(events_df):,} rows")
        
        # Load PS drug data with route information
        drug_query = """
            SELECT d.primaryid, d.drug_seq, d.role_cod, d.ingredient_std,
                   UPPER(TRIM(d.route)) AS route, x.caseid
            FROM faers_drug_2023_ps d
            JOIN faers_demo_2023_latest_us x USING (primaryid)
            WHERE UPPER(TRIM(COALESCE(d.role_cod,''))) = 'PS'
              AND x.year BETWEEN ? AND ?
        """
        
        drug_df = pd.read_sql_query(drug_query, conn, params=year_window)
        print(f"✓ Loaded PS drugs: {len(drug_df):,} rows")
        
        # Try to load Medicare denominators (optional)
        try:
            denom_query = """
                SELECT ingredient_std, tot_30day_fills, tot_benes
                FROM medicare_denoms_2023
            """
            denoms_df = pd.read_sql_query(denom_query, conn)
            print(f"✓ Loaded Medicare denominators: {len(denoms_df):,} drugs")
        except:
            # Create dummy denominators if Medicare data unavailable
            denoms_df = pd.DataFrame({
                'ingredient_std': [TARGET_ING, COMPARATOR_ING],
                'tot_30day_fills': [100000, 100000],
                'tot_benes': [50000, 50000]
            })
            print("⚠ Medicare data unavailable, using dummy denominators")
    
    return events_df, drug_df, denoms_df

def validate_data(events_df, drug_df, target_ing, comparator_ing):
    """Validate that target drugs exist in the datasets."""
    
    print("\n" + "="*60)
    print("DATA VALIDATION")
    print("="*60)
    
    # Check target drug presence
    target_events = events_df['ingredient_std'].str.contains(target_ing, na=False).sum()
    target_drugs = drug_df['ingredient_std'].str.contains(target_ing, na=False).sum()
    comp_events = events_df['ingredient_std'].str.contains(comparator_ing, na=False).sum()
    comp_drugs = drug_df['ingredient_std'].str.contains(comparator_ing, na=False).sum()
    
    print(f"Target drug '{target_ing}':")
    print(f"  - Events: {target_events:,} rows")
    print(f"  - PS drugs: {target_drugs:,} rows")
    
    print(f"\nComparator '{comparator_ing}':")
    print(f"  - Events: {comp_events:,} rows")
    print(f"  - PS drugs: {comp_drugs:,} rows")
    
    if target_events == 0 or target_drugs == 0:
        print(f"\n⚠ WARNING: {target_ing} has limited data")
    if comp_events == 0 or comp_drugs == 0:
        print(f"\n⚠ WARNING: {comparator_ing} has limited data")
    
    # Show top ingredients for context
    print(f"\nTop 10 ingredients in events:")
    print(events_df['ingredient_std'].value_counts().head(10))

# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def main():
    """Execute the complete signal detection analysis."""
    
    print("="*80)
    print("FAERS SIGNAL DETECTION: MINOXIDIL PERICARDIAL EFFUSION ANALYSIS")
    print("="*80)
    
    try:
        # Load data
        events_df, drug_df, denoms_df = load_faers_data(DB_PATH, YEAR_WINDOW)
        validate_data(events_df, drug_df, TARGET_ING, COMPARATOR_ING)
        
        print("\n" + "="*60)
        print("BUILDING ROUTE-BASED COHORTS")
        print("="*60)
        
        # Build route-specific case sets
        oral_cases = build_route_sets(drug_df, TARGET_ING, ORAL_KEYS)
        topical_cases = build_route_sets(drug_df, TARGET_ING, TOPICAL_KEYS)
        unknown_cases = build_route_sets(drug_df, TARGET_ING, UNKNOWN_KEYS)
        
        # Also get cases with None/null routes
        mask_ing = (drug_df["ingredient_std"] == TARGET_ING)
        null_route_cases = set(drug_df.loc[
            mask_ing & (drug_df["route"].isna() | (drug_df["route"] == "")), 
            "caseid"
        ].unique())
        
        # Combine unknown and null routes
        unknown_all_cases = unknown_cases | null_route_cases
        
        print(f"Route cohorts:")
        print(f"  - Oral {TARGET_ING}: {len(oral_cases):,} cases")
        print(f"  - Topical {TARGET_ING}: {len(topical_cases):,} cases")
        print(f"  - Unknown/Unspecified {TARGET_ING}: {len(unknown_all_cases):,} cases")
        print(f"  - {COMPARATOR_ING}: No route filter (all PS cases)")
        
        print("\n" + "="*60)
        print("RUNNING STATISTICAL ANALYSIS")
        print("="*60)
        
        # Run analysis panels
        panel_oral = run_analysis_panel(
            events_df, TARGET_ING, ALL_PTS, 
            label="MINOXIDIL_ORAL_PS_2023", 
            restrict_caseids=oral_cases
        )
        
        panel_topical = run_analysis_panel(
            events_df, TARGET_ING, ALL_PTS,
            label="MINOXIDIL_TOPICAL_PS_2023", 
            restrict_caseids=topical_cases
        )
        
        panel_unknown = run_analysis_panel(
            events_df, TARGET_ING, ALL_PTS,
            label="MINOXIDIL_UNKNOWN_ROUTE_PS_2023", 
            restrict_caseids=unknown_all_cases
        )
        
        panel_comparator = run_analysis_panel(
            events_df, COMPARATOR_ING, ALL_PTS,
            label=f"{COMPARATOR_ING}_PS_2023", 
            restrict_caseids=None
        )
        
        # Combine results
        all_results = pd.concat([panel_oral, panel_topical, panel_unknown, panel_comparator], 
                               ignore_index=True)
        
        # Add Medicare rates if available
        all_results = all_results.merge(
            denoms_df, how="left", 
            left_on="drug", right_on="ingredient_std", 
            suffixes=("", "_den")
        )
        
        all_results["rate_per_100k_fills"] = np.where(
            all_results["tot_30day_fills"] > 0,
            all_results["a"] / all_results["tot_30day_fills"] * 1e5,
            np.nan
        )
        
        # Clean up columns
        all_results = all_results.drop(columns=["ingredient_std_den"], errors='ignore')
        
        # Display results
        primary_results = all_results[
            all_results["pt"].isin(PRIMARY_PTS)
        ].sort_values(["analysis_set", "pt"])
        
        secondary_results = all_results[
            all_results["pt"].isin(SECONDARY_PTS)
        ].sort_values(["analysis_set", "pt"])
        
        print("\n" + "="*80)
        print("RESULTS: PRIMARY ENDPOINTS")
        print("="*80)
        display_results(primary_results)
        
        print("\n" + "="*80)
        print("RESULTS: SECONDARY ENDPOINTS")
        print("="*80)
        display_results(secondary_results)
        
        # Summary of signals
        print("\n" + "="*80)
        print("SIGNAL SUMMARY")
        print("="*80)
        
        flagged = all_results[all_results["flag"] == True]
        if len(flagged) > 0:
            print(f"🚨 {len(flagged)} potential signals detected:")
            for _, row in flagged.iterrows():
                print(f"  - {row['analysis_set']}: {row['pt']}")
                print(f"    PRR={row['PRR']:.2f} (CI: {row['PRR_LCL']:.2f}-{row['PRR_UCL']:.2f})")
                print(f"    Cases={row['a']}, Chi2={row['chi2']:.2f}")
        else:
            print("No signals detected based on flagging criteria.")
        
        # Save results
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"minoxidil_analysis_{timestamp}.csv"
        all_results.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def display_results(df):
    """Display results in a formatted table."""
    if len(df) == 0:
        print("No results to display.")
        return
    
    # Format key columns for display
    display_cols = ['analysis_set', 'pt', 'a', 'b', 'c', 'd', 
                   'PRR', 'PRR_LCL', 'PRR_UCL', 'ROR', 'ROR_LCL', 'ROR_UCL', 
                   'chi2', 'flag']
    
    display_df = df[display_cols].copy()
    
    # Round numeric columns
    numeric_cols = ['PRR', 'PRR_LCL', 'PRR_UCL', 'ROR', 'ROR_LCL', 'ROR_UCL', 'chi2']
    for col in numeric_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(3)
    
    # Print formatted output
    print(display_df.to_string(index=False))

# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
