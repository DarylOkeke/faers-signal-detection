#!/usr/bin/env python3
"""
Create Efficient 2x2 Contingency Tables for Signal Detection

This script creates optimized 2x2 contingency tables using materialized
calculations instead of complex subqueries.

Author: FAERS Signal Detection Team
Date: August 2025
"""

import sqlite3
import pandas as pd
import os

# Database configuration
DB_PATH = "../data/faers+medicare.db"

def create_efficient_2x2_view(conn):
    """Create an efficient 2x2 contingency table view with materialized calculations."""
    
    print("Creating efficient v_signal_2x2_2023 view...")
    
    # Drop existing view
    conn.execute("DROP VIEW IF EXISTS v_signal_2x2_2023")
    
    # Get grand total first
    print("  Step 1: Getting grand total...")
    grand_total_result = conn.execute("""
    SELECT COUNT(DISTINCT primaryid) AS grand_total
    FROM v_events_2023_cohorts
    WHERE cohort IS NOT NULL
    """).fetchone()
    grand_total = grand_total_result[0]
    print(f"    Grand total cases: {grand_total:,}")
    
    # Create the view with all calculations inline using CTEs
    print("  Step 2: Creating optimized 2x2 view with CTEs...")
    
    final_view_sql = f"""
    CREATE VIEW v_signal_2x2_2023 AS
    WITH cohort_reaction_counts AS (
        SELECT 
            cohort,
            reaction_pt,
            COUNT(DISTINCT primaryid) AS a
        FROM v_events_2023_cohorts
        WHERE cohort IS NOT NULL
        GROUP BY cohort, reaction_pt
    ),
    cohort_totals AS (
        SELECT 
            cohort,
            COUNT(DISTINCT primaryid) AS total_cases
        FROM v_events_2023_cohorts
        WHERE cohort IS NOT NULL
        GROUP BY cohort
    ),
    reaction_totals AS (
        SELECT 
            reaction_pt,
            COUNT(DISTINCT primaryid) AS total_with_reaction
        FROM v_events_2023_cohorts
        WHERE cohort IS NOT NULL
        GROUP BY reaction_pt
    )
    SELECT
        cr.cohort,
        cr.reaction_pt,
        cr.a,
        (ct.total_cases - cr.a) AS b,
        (rt.total_with_reaction - cr.a) AS c,
        ({grand_total} - ct.total_cases - rt.total_with_reaction + cr.a) AS d
    FROM cohort_reaction_counts cr
    JOIN cohort_totals ct ON cr.cohort = ct.cohort
    JOIN reaction_totals rt ON cr.reaction_pt = rt.reaction_pt
    """
    
    conn.execute(final_view_sql)
    print("✓ Efficient v_signal_2x2_2023 view created successfully")

def run_quick_checks(conn):
    """Run quick sanity checks on the 2x2 table view."""
    
    print("\n" + "="*60)
    print("QUICK VALIDATION CHECKS")
    print("="*60)
    
    # 1) Total rows in view
    print("\n1. View size:")
    count_query = "SELECT COUNT(*) AS total_rows FROM v_signal_2x2_2023"
    count_result = pd.read_sql_query(count_query, conn)
    print(f"   Total cohort-reaction pairs: {count_result.iloc[0,0]:,}")
    
    # 2) Cohort summary
    print("\n2. Cohort summary:")
    cohort_query = """
    SELECT 
        cohort, 
        COUNT(*) AS n_reactions,
        SUM(a) AS total_events,
        AVG(a) AS avg_events_per_reaction
    FROM v_signal_2x2_2023
    GROUP BY cohort
    ORDER BY total_events DESC
    """
    cohort_result = pd.read_sql_query(cohort_query, conn)
    print(cohort_result.to_string(index=False))
    
    # 3) PERICARDIAL EFFUSION specifically
    print("\n3. PERICARDIAL EFFUSION 2x2 tables:")
    pe_query = """
    SELECT cohort, reaction_pt, a, b, c, d
    FROM v_signal_2x2_2023
    WHERE reaction_pt = 'PERICARDIAL EFFUSION'
    ORDER BY cohort
    """
    pe_result = pd.read_sql_query(pe_query, conn)
    if not pe_result.empty:
        print(pe_result.to_string(index=False))
    else:
        print("   No PERICARDIAL EFFUSION cases found")
    
    # 4) Top reactions for MINOXIDIL_SYSTEMIC
    print("\n4. Top reactions for MINOXIDIL_SYSTEMIC:")
    systemic_query = """
    SELECT cohort, reaction_pt, a, b, c, d
    FROM v_signal_2x2_2023
    WHERE cohort = 'MINOXIDIL_SYSTEMIC'
    ORDER BY a DESC
    LIMIT 5
    """
    systemic_result = pd.read_sql_query(systemic_query, conn)
    if not systemic_result.empty:
        print(systemic_result.to_string(index=False))
    else:
        print("   No MINOXIDIL_SYSTEMIC data found")

def main():
    """Execute the efficient 2x2 table creation."""
    
    print("="*80)
    print("EFFICIENT FAERS 2x2 CONTINGENCY TABLE CREATION")
    print("="*80)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return 1
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Create the efficient 2x2 view
            create_efficient_2x2_view(conn)
            
            # Run quick checks
            run_quick_checks(conn)
            
        print("\n" + "="*80)
        print("EFFICIENT 2x2 TABLE CREATION COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Failed to create 2x2 tables: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
