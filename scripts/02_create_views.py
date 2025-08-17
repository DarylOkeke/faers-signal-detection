#!/usr/bin/env python3
"""
FAERS Database Setup for Signal Detection

This script sets up the complete database views needed for FAERS signal detection analysis.
It creates the route normalization, cohort definition, and 2x2 contingency table views.

Author: FAERS Signal Detection Team
Date: August 2025
"""

import sqlite3
import pandas as pd
import os
import sys

# Database configuration
DB_PATH = "data/faers+medicare.db"

def create_route_flags_view(conn):
    """Create route normalization view with boolean flags."""
    print("Creating v_events_2023_route_flags view...")
    
    conn.execute("DROP VIEW IF EXISTS v_events_2023_route_flags")
    
    route_view_sql = """
    CREATE VIEW v_events_2023_route_flags AS
    SELECT
        -- Keep identifiers that exist in faers_events_2023_unique
        year,
        quarter,
        primaryid,
        caseid,
        UPPER(TRIM(COALESCE(ingredient_std,'')))     AS ingredient_std,
        UPPER(TRIM(COALESCE(reaction_pt,'')))        AS reaction_pt,
        UPPER(TRIM(COALESCE(role_cod,'')))           AS role_cod,

        -- Normalize route text
        UPPER(TRIM(COALESCE(route,'')))              AS route_norm,

        -- Route flags (SQLite CASE)
        CASE
          WHEN UPPER(TRIM(COALESCE(route,''))) IN ('ORAL','PO','BY MOUTH')
               OR UPPER(TRIM(COALESCE(route,''))) LIKE 'ORAL %'
          THEN 1 ELSE 0 END                          AS is_oral,

        CASE
          WHEN UPPER(TRIM(COALESCE(route,''))) IN ('TOPICAL','CUTANEOUS','SCALP','TRANSDERMAL')
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%TOPICAL%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%CUTANEOUS%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%SCALP%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%LOTION%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%FOAM%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%SOLUTION%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%SOLN%'
          THEN 1 ELSE 0 END                          AS is_topical,

        CASE
          WHEN route IS NULL
               OR TRIM(route) = ''
               OR UPPER(TRIM(route)) IN ('UNKNOWN','UNSPECIFIED','NONE')
          THEN 1 ELSE 0 END                          AS is_unknown
    FROM faers_events_2023_unique
    WHERE year = 2023
    """
    
    conn.execute(route_view_sql)
    print("✓ v_events_2023_route_flags view created")

def create_cohorts_view(conn):
    """Create cohort definition view with comprehensive OTHER background."""
    print("Creating v_events_2023_cohorts view...")
    
    conn.execute("DROP VIEW IF EXISTS v_events_2023_cohorts")
    
    cohorts_view_sql = """
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
          WHEN ingredient_std LIKE '%HYDRALAZINE%'
            THEN 'HYDRALAZINE'
          ELSE 'OTHER'
        END AS cohort
    FROM v_events_2023_route_flags
    WHERE role_cod = 'PS'  -- primary analysis set
      AND year = 2023
    """
    
    conn.execute(cohorts_view_sql)
    print("✓ v_events_2023_cohorts view created")

def create_2x2_view(conn):
    """Create 2x2 contingency table view for signal detection."""
    print("Creating v_signal_2x2_2023 view...")
    
    conn.execute("DROP VIEW IF EXISTS v_signal_2x2_2023")
    
    # Get grand total for calculations
    grand_total_result = conn.execute("""
    SELECT COUNT(DISTINCT primaryid) AS grand_total
    FROM v_events_2023_cohorts
    """).fetchone()
    grand_total = grand_total_result[0]
    
    signal_view_sql = f"""
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
    
    conn.execute(signal_view_sql)
    print(f"✓ v_signal_2x2_2023 view created (grand total: {grand_total:,} cases)")

def validate_views(conn):
    """Validate that all views were created successfully."""
    print("\nValidating database views...")
    
    # Check view existence
    views_query = """
    SELECT name FROM sqlite_master 
    WHERE type='view' AND name LIKE 'v_%2023%'
    ORDER BY name
    """
    views_df = pd.read_sql_query(views_query, conn)
    print(f"✓ Created {len(views_df)} views: {list(views_df['name'])}")
    
    # Quick validation queries
    validations = [
        ("Route flags", "SELECT COUNT(*) as count FROM v_events_2023_route_flags"),
        ("Cohorts", "SELECT COUNT(*) as count FROM v_events_2023_cohorts"),
        ("2x2 tables", "SELECT COUNT(*) as count FROM v_signal_2x2_2023"),
    ]
    
    for desc, query in validations:
        result = pd.read_sql_query(query, conn)
        count = result.iloc[0, 0]
        print(f"✓ {desc}: {count:,} rows")
    
    # Check target endpoints
    pe_query = """
    SELECT cohort, a, b, c, d
    FROM v_signal_2x2_2023
    WHERE reaction_pt = 'PERICARDIAL EFFUSION'
    ORDER BY cohort
    """
    pe_result = pd.read_sql_query(pe_query, conn)
    if not pe_result.empty:
        print(f"\n✓ PERICARDIAL EFFUSION 2x2 tables:")
        print(pe_result.to_string(index=False))
    else:
        print(f"\n⚠ No PERICARDIAL EFFUSION data found")

def main():
    """Set up all database views for FAERS signal detection."""
    
    print("="*80)
    print("FAERS SIGNAL DETECTION DATABASE SETUP")
    print("="*80)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("Please run scripts/load_faers+medicare_to_db.py first to create the database.")
        return 1
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Create views in order (dependencies matter)
            create_route_flags_view(conn)
            create_cohorts_view(conn)
            create_2x2_view(conn)
            
            # Validate everything worked
            validate_views(conn)
            
        print("\n" + "="*80)
        print("DATABASE SETUP COMPLETE")
        print("="*80)
        print("Ready for signal detection analysis!")
        print("\nNext steps:")
        print("1. python -m src.compute_summary --db data/faers+medicare.db --out results/tables/summary_2023_ps.csv")
        print("2. python -m src.make_trimmed_tables --in results/tables/summary_2023_ps.csv --out results/tables/minoxidil_cardiac_2023_ps.csv")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
