#!/usr/bin/env python3
"""
Rebuild 2x2 Contingency Tables with Full Background

This script rebuilds the 2x2 view to use the comprehensive OTHER background
for proper signal detection calculations.

Author: FAERS Signal Detection Team
Date: August 2025
"""

import sqlite3
import pandas as pd
import os

# Database configuration
DB_PATH = "../data/faers+medicare.db"

def rebuild_2x2_view(conn):
    """Rebuild the 2x2 view with full background calculations."""
    
    print("Rebuilding v_signal_2x2_2023 with comprehensive background...")
    
    # Drop existing view
    conn.execute("DROP VIEW IF EXISTS v_signal_2x2_2023")
    
    # Create the updated 2x2 view with proper background
    create_view_sql = """
    CREATE VIEW v_signal_2x2_2023 AS
    WITH cohort_reaction_counts AS (
        SELECT
            cohort,
            reaction_pt,
            COUNT(DISTINCT primaryid) AS a  -- cases with event in this cohort
        FROM v_events_2023_cohorts
        GROUP BY cohort, reaction_pt
    ),
    cohort_totals AS (
        SELECT
            cohort,
            COUNT(DISTINCT primaryid) AS total_cohort
        FROM v_events_2023_cohorts
        GROUP BY cohort
    ),
    reaction_totals AS (
        SELECT
            reaction_pt,
            COUNT(DISTINCT primaryid) AS total_with_event
        FROM v_events_2023_cohorts
        GROUP BY reaction_pt
    ),
    grand AS (
        SELECT COUNT(DISTINCT primaryid) AS grand_total
        FROM v_events_2023_cohorts
    )
    SELECT
        crc.cohort,
        crc.reaction_pt,
        crc.a,
        (ct.total_cohort - crc.a) AS b,
        (rt.total_with_event - crc.a) AS c,
        ( (g.grand_total - ct.total_cohort) - (rt.total_with_event - crc.a) ) AS d
    FROM cohort_reaction_counts crc
    JOIN cohort_totals ct   ON ct.cohort = crc.cohort
    JOIN reaction_totals rt ON rt.reaction_pt = crc.reaction_pt
    JOIN grand g
    """
    
    conn.execute(create_view_sql)
    print("✓ Rebuilt v_signal_2x2_2023 view with full background")

def run_sanity_checks(conn):
    """Run sanity checks on the rebuilt 2x2 view."""
    
    print("\n" + "="*80)
    print("SANITY CHECKS: REBUILT 2x2 TABLES")
    print("="*80)
    
    # 1) Target reactions for MINOXIDIL_SYSTEMIC
    print("\n1. Target cardiac reactions for MINOXIDIL_SYSTEMIC:")
    target_query = """
    SELECT cohort, reaction_pt, a, b, c, d, (a+b+c+d) as total_check
    FROM v_signal_2x2_2023
    WHERE cohort='MINOXIDIL_SYSTEMIC'
      AND reaction_pt IN ('PERICARDIAL EFFUSION','PERICARDITIS','CARDIAC TAMPONADE','PLEURAL EFFUSION')
    ORDER BY reaction_pt
    """
    
    target_result = pd.read_sql_query(target_query, conn)
    if not target_result.empty:
        print(target_result.to_string(index=False))
    else:
        print("   No target cardiac reactions found for MINOXIDIL_SYSTEMIC")
    
    # 2) Totals validation - check that a+b+c+d equals grand total
    print("\n2. Totals validation (a+b+c+d should equal grand total):")
    totals_query = """
    WITH g AS (SELECT COUNT(DISTINCT primaryid) AS N FROM v_events_2023_cohorts),
    sample AS (
        SELECT cohort, reaction_pt, a, b, c, d, (a+b+c+d) as sum_abcd
        FROM v_signal_2x2_2023
        LIMIT 5
    )
    SELECT 
        s.cohort,
        s.reaction_pt,
        s.a, s.b, s.c, s.d,
        s.sum_abcd,
        g.N as grand_total,
        (s.sum_abcd = g.N) as totals_match
    FROM sample s, g
    """
    
    totals_result = pd.read_sql_query(totals_query, conn)
    print(totals_result.to_string(index=False))
    
    # 3) Cohort representation in 2x2 view
    print("\n3. Cohort representation in 2x2 view:")
    cohort_query = """
    SELECT 
        cohort, 
        COUNT(*) AS n_reaction_pairs,
        SUM(a) AS total_events_in_cohort,
        AVG(a) AS avg_events_per_reaction,
        MAX(a) AS max_events_for_reaction
    FROM v_signal_2x2_2023
    GROUP BY cohort
    ORDER BY total_events_in_cohort DESC
    """
    
    cohort_result = pd.read_sql_query(cohort_query, conn)
    print(cohort_result.to_string(index=False))
    
    # 4) Verify OTHER cohort is large
    print("\n4. OTHER cohort validation:")
    other_query = """
    SELECT 
        'OTHER cohort' as description,
        COUNT(*) AS n_reaction_pairs,
        SUM(a) AS total_events,
        MIN(a) AS min_events,
        MAX(a) AS max_events
    FROM v_signal_2x2_2023
    WHERE cohort = 'OTHER'
    """
    
    other_result = pd.read_sql_query(other_query, conn)
    print(other_result.to_string(index=False))
    
    # 5) Sample high-frequency reactions in OTHER
    print("\n5. Top reactions in OTHER cohort:")
    other_top_query = """
    SELECT cohort, reaction_pt, a, b, c, d
    FROM v_signal_2x2_2023
    WHERE cohort = 'OTHER'
    ORDER BY a DESC
    LIMIT 10
    """
    
    other_top_result = pd.read_sql_query(other_top_query, conn)
    print(other_top_result.to_string(index=False))
    
    # 6) PERICARDIAL EFFUSION across all cohorts
    print("\n6. PERICARDIAL EFFUSION distribution across cohorts:")
    pe_query = """
    SELECT cohort, reaction_pt, a, b, c, d
    FROM v_signal_2x2_2023
    WHERE reaction_pt = 'PERICARDIAL EFFUSION'
    ORDER BY a DESC
    """
    
    pe_result = pd.read_sql_query(pe_query, conn)
    if not pe_result.empty:
        print(pe_result.to_string(index=False))
        
        # Calculate some basic signal metrics for PE
        print("\n   Basic PRR calculations for PERICARDIAL EFFUSION:")
        for _, row in pe_result.iterrows():
            if row['a'] > 0 and row['b'] > 0 and row['c'] > 0 and row['d'] > 0:
                prr = (row['a'] / (row['a'] + row['b'])) / (row['c'] / (row['c'] + row['d']))
                print(f"     {row['cohort']}: PRR = {prr:.3f} (a={row['a']}, b={row['b']}, c={row['c']}, d={row['d']})")
    else:
        print("   No PERICARDIAL EFFUSION cases found")
    
    # 7) View statistics
    print("\n7. Overall view statistics:")
    stats_query = """
    SELECT 
        COUNT(*) AS total_cohort_reaction_pairs,
        COUNT(DISTINCT cohort) AS n_cohorts,
        COUNT(DISTINCT reaction_pt) AS n_unique_reactions,
        SUM(a) AS total_events,
        AVG(a) AS avg_events_per_pair,
        MIN(CASE WHEN a > 0 THEN a END) AS min_nonzero_events,
        MAX(a) AS max_events
    FROM v_signal_2x2_2023
    """
    
    stats_result = pd.read_sql_query(stats_query, conn)
    print(stats_result.to_string(index=False))

def main():
    """Execute the 2x2 view rebuild and validation."""
    
    print("="*80)
    print("REBUILD 2x2 TABLES WITH COMPREHENSIVE BACKGROUND")
    print("="*80)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return 1
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Rebuild the 2x2 view
            rebuild_2x2_view(conn)
            
            # Run sanity checks
            run_sanity_checks(conn)
            
        print("\n" + "="*80)
        print("2x2 VIEW REBUILD COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Failed to rebuild 2x2 view: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
