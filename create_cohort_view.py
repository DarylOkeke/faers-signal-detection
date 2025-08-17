#!/usr/bin/env python3
"""
Create FAERS Cohort Definition View

This script creates a view that defines drug cohorts for analysis:
- MINOXIDIL_SYSTEMIC (oral + unknown routes)
- MINOXIDIL_TOPICAL (topical routes only)
- HYDRALAZINE (all routes - systemic drug)

Author: FAERS Signal Detection Team
Date: August 2025
"""

import sqlite3
import pandas as pd
import os

# Database configuration
DB_PATH = "data/faers+medicare.db"

def create_cohort_view(conn):
    """Create the cohort definition view."""
    print("Creating v_events_2023_cohorts view...")
    
    # Drop existing view if it exists
    drop_sql = "DROP VIEW IF EXISTS v_events_2023_cohorts;"
    conn.execute(drop_sql)
    
    # Create cohort view
    create_sql = """
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
          WHEN ingredient_std = 'MINOXIDIL' AND (is_oral = 1 OR is_unknown = 1)
            THEN 'MINOXIDIL_SYSTEMIC'
          WHEN ingredient_std = 'MINOXIDIL' AND is_topical = 1
            THEN 'MINOXIDIL_TOPICAL'
          WHEN ingredient_std = 'HYDRALAZINE'
            THEN 'HYDRALAZINE'
          ELSE NULL
        END AS cohort
    FROM v_events_2023_route_flags
    WHERE role_cod = 'PS'  -- keep primary suspects only
      AND (
           (ingredient_std = 'MINOXIDIL')
           OR (ingredient_std = 'HYDRALAZINE')
      );
    """
    
    conn.execute(create_sql)
    conn.commit()
    print("✓ View created successfully")

def run_sanity_checks(conn):
    """Run sanity checks on the cohort view."""
    print("\n" + "="*60)
    print("COHORT VIEW SANITY CHECKS")
    print("="*60)
    
    # 1. Count by cohort
    print("\n1. Count by cohort:")
    cohort_counts_sql = """
    SELECT cohort, COUNT(*) AS n
    FROM v_events_2023_cohorts
    GROUP BY cohort
    ORDER BY n DESC;
    """
    
    cohort_counts = pd.read_sql_query(cohort_counts_sql, conn)
    print(cohort_counts.to_string(index=False))
    
    # 2. Reaction diversity per cohort
    print("\n2. Reaction diversity per cohort:")
    reaction_diversity_sql = """
    SELECT cohort, COUNT(DISTINCT reaction_pt) AS n_reactions
    FROM v_events_2023_cohorts
    GROUP BY cohort
    ORDER BY n_reactions DESC;
    """
    
    reaction_diversity = pd.read_sql_query(reaction_diversity_sql, conn)
    print(reaction_diversity.to_string(index=False))
    
    # 3. Sample rows
    print("\n3. Sample rows from cohort view:")
    sample_sql = """
    SELECT cohort, ingredient_std, route_norm, reaction_pt
    FROM v_events_2023_cohorts
    ORDER BY cohort, reaction_pt
    LIMIT 20;
    """
    
    sample_data = pd.read_sql_query(sample_sql, conn)
    print(sample_data.to_string(index=False))
    
    # 4. Route distribution within MINOXIDIL cohorts
    print("\n4. Route distribution within MINOXIDIL cohorts:")
    route_dist_sql = """
    SELECT 
        cohort,
        route_norm,
        SUM(is_oral) as oral_count,
        SUM(is_topical) as topical_count,
        SUM(is_unknown) as unknown_count,
        COUNT(*) AS total_count
    FROM v_events_2023_cohorts
    WHERE cohort LIKE 'MINOXIDIL%'
    GROUP BY cohort, route_norm
    ORDER BY cohort, total_count DESC;
    """
    
    route_dist = pd.read_sql_query(route_dist_sql, conn)
    print(route_dist.to_string(index=False))
    
    # 5. Check for NULL cohorts (should be none)
    print("\n5. Check for NULL cohorts:")
    null_check_sql = """
    SELECT COUNT(*) as null_cohorts
    FROM v_events_2023_cohorts
    WHERE cohort IS NULL;
    """
    
    null_check = pd.read_sql_query(null_check_sql, conn)
    null_count = null_check['null_cohorts'].iloc[0]
    if null_count == 0:
        print("✓ No NULL cohorts found (good)")
    else:
        print(f"⚠ Warning: {null_count} rows have NULL cohort")

def check_target_reactions(conn):
    """Check if target reactions are present in cohorts."""
    print("\n" + "="*60)
    print("TARGET REACTION ANALYSIS")
    print("="*60)
    
    target_pts = [
        'PERICARDIAL EFFUSION',
        'PERICARDITIS', 
        'CARDIAC TAMPONADE',
        'PLEURAL EFFUSION'
    ]
    
    for pt in target_pts:
        print(f"\n--- {pt} ---")
        pt_sql = f"""
        SELECT cohort, COUNT(*) as cases
        FROM v_events_2023_cohorts
        WHERE reaction_pt = '{pt}'
        GROUP BY cohort
        ORDER BY cases DESC;
        """
        
        try:
            pt_results = pd.read_sql_query(pt_sql, conn)
            if not pt_results.empty:
                print(pt_results.to_string(index=False))
            else:
                print("No cases found")
        except Exception as e:
            print(f"Error querying {pt}: {e}")

def main():
    """Execute the cohort view creation and testing."""
    
    print("="*80)
    print("FAERS COHORT DEFINITION VIEW CREATION")
    print("="*80)
    
    try:
        # Check database existence
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database not found: {DB_PATH}")
        
        print(f"✓ Database found: {DB_PATH}")
        
        # Connect to database
        with sqlite3.connect(DB_PATH) as conn:
            
            # Create cohort view
            create_cohort_view(conn)
            
            # Run sanity checks
            run_sanity_checks(conn)
            
            # Check target reactions
            check_target_reactions(conn)
            
        print("\n" + "="*80)
        print("COHORT VIEW CREATION COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
