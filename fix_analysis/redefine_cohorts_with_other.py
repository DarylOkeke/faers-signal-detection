#!/usr/bin/env python3
"""
Redefine Cohorts with Full OTHER Background

This script updates the cohort view to include ALL PS cases from FAERS 2023,
with proper assignment to target cohorts or OTHER background.

Author: FAERS Signal Detection Team
Date: August 2025
"""

import sqlite3
import pandas as pd
import os

# Database configuration
DB_PATH = "../data/faers+medicare.db"

def update_cohort_view(conn):
    """Update the cohort view to include comprehensive OTHER background."""
    
    print("Updating v_events_2023_cohorts with full OTHER background...")
    
    # Drop existing view
    conn.execute("DROP VIEW IF EXISTS v_events_2023_cohorts")
    
    # Create the updated cohort view
    create_view_sql = """
    CREATE VIEW v_events_2023_cohorts AS
    SELECT
        year,
        quarter,
        primaryid,
        caseid,
        ingredient_std,
        reaction_pt,
        role_cod,
        route_norm,
        is_oral,
        is_topical,
        is_unknown,
        CASE
          WHEN ingredient_std = 'MINOXIDIL'
               AND (is_oral = 1 OR is_unknown = 1) AND is_topical = 0
            THEN 'MINOXIDIL_SYSTEMIC'
          WHEN ingredient_std = 'MINOXIDIL'
               AND is_topical = 1
            THEN 'MINOXIDIL_TOPICAL'
          WHEN ingredient_std = 'HYDRALAZINE'
            THEN 'HYDRALAZINE'
          ELSE 'OTHER'
        END AS cohort
    FROM v_events_2023_route_flags
    WHERE role_cod = 'PS'  -- primary analysis set
      AND year = 2023
    """
    
    conn.execute(create_view_sql)
    print("✓ Updated v_events_2023_cohorts view created successfully")

def run_cohort_validation(conn):
    """Validate the updated cohort assignments."""
    
    print("\n" + "="*80)
    print("COHORT VALIDATION: COMPREHENSIVE BACKGROUND")
    print("="*80)
    
    # 1) Cohort size distribution
    print("\n1. Cohort size distribution:")
    cohort_query = """
    SELECT cohort, COUNT(DISTINCT primaryid) AS n_cases
    FROM v_events_2023_cohorts
    GROUP BY cohort
    ORDER BY n_cases DESC
    """
    
    cohort_result = pd.read_sql_query(cohort_query, conn)
    print(cohort_result.to_string(index=False))
    
    # Calculate percentages
    total_cases = cohort_result['n_cases'].sum()
    print(f"\nTotal PS cases: {total_cases:,}")
    for _, row in cohort_result.iterrows():
        pct = (row['n_cases'] / total_cases) * 100
        print(f"  {row['cohort']}: {row['n_cases']:,} ({pct:.1f}%)")
    
    # 2) Check for NULL cohorts (should be 0)
    print("\n2. NULL cohort check:")
    null_query = """
    SELECT SUM(CASE WHEN cohort IS NULL THEN 1 ELSE 0 END) AS null_cohort_rows 
    FROM v_events_2023_cohorts
    """
    
    null_result = pd.read_sql_query(null_query, conn)
    null_count = null_result.iloc[0, 0]
    if null_count == 0:
        print(f"✓ No NULL cohorts found ({null_count})")
    else:
        print(f"⚠ WARNING: {null_count} rows have NULL cohort")
    
    # 3) MINOXIDIL route breakdown
    print("\n3. MINOXIDIL route breakdown:")
    minox_query = """
    SELECT 
        cohort,
        route_norm,
        is_oral,
        is_topical,
        is_unknown,
        COUNT(DISTINCT primaryid) AS n_cases
    FROM v_events_2023_cohorts
    WHERE ingredient_std = 'MINOXIDIL'
    GROUP BY cohort, route_norm, is_oral, is_topical, is_unknown
    ORDER BY cohort, n_cases DESC
    """
    
    minox_result = pd.read_sql_query(minox_query, conn)
    print(minox_result.to_string(index=False))
    
    # 4) HYDRALAZINE verification  
    print("\n4. HYDRALAZINE verification:")
    hydral_query = """
    SELECT 
        ingredient_std,
        cohort,
        COUNT(DISTINCT primaryid) AS n_cases
    FROM v_events_2023_cohorts
    WHERE ingredient_std LIKE '%HYDRALAZINE%'
    GROUP BY ingredient_std, cohort
    ORDER BY n_cases DESC
    """
    
    hydral_result = pd.read_sql_query(hydral_query, conn)
    if not hydral_result.empty:
        print(hydral_result.to_string(index=False))
    else:
        print("No HYDRALAZINE cases found")
    
    # 5) Sample OTHER cohort drugs
    print("\n5. Sample OTHER cohort drugs (top 10):")
    other_query = """
    SELECT 
        ingredient_std,
        COUNT(DISTINCT primaryid) AS n_cases
    FROM v_events_2023_cohorts
    WHERE cohort = 'OTHER'
    GROUP BY ingredient_std
    ORDER BY n_cases DESC
    LIMIT 10
    """
    
    other_result = pd.read_sql_query(other_query, conn)
    print(other_result.to_string(index=False))
    
    # 6) Target reactions across cohorts
    print("\n6. Target cardiac reactions across cohorts:")
    target_reactions = ['PERICARDIAL EFFUSION', 'PERICARDITIS', 'CARDIAC TAMPONADE', 'PLEURAL EFFUSION']
    
    for reaction in target_reactions:
        print(f"\n   {reaction}:")
        reaction_query = f"""
        SELECT 
            cohort,
            COUNT(DISTINCT primaryid) AS n_cases
        FROM v_events_2023_cohorts
        WHERE reaction_pt = '{reaction}'
        GROUP BY cohort
        ORDER BY n_cases DESC
        """
        
        reaction_result = pd.read_sql_query(reaction_query, conn)
        if not reaction_result.empty:
            print(reaction_result.to_string(index=False))
        else:
            print("     No cases found")

def main():
    """Execute the cohort redefinition and validation."""
    
    print("="*80)
    print("COHORT REDEFINITION: COMPREHENSIVE OTHER BACKGROUND")
    print("="*80)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return 1
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Update the cohort view
            update_cohort_view(conn)
            
            # Run validation checks
            run_cohort_validation(conn)
            
        print("\n" + "="*80)
        print("COHORT REDEFINITION COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Failed to redefine cohorts: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
