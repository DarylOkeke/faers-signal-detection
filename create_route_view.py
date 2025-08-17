#!/usr/bin/env python3
"""
Route Normalization View Creator

This script creates a SQLite view that standardizes route information
and adds boolean flags for route classification in FAERS analysis.

Author: FAERS Signal Detection Team  
Date: August 2025
"""

import sqlite3
import pandas as pd
import os

# Database configuration
DB_PATH = "data/faers+medicare.db"

def create_route_view(conn):
    """Create the route normalization view."""
    
    print("Creating route normalization view...")
    
    # Drop existing view if it exists
    drop_sql = "DROP VIEW IF EXISTS v_events_2023_route_flags;"
    conn.execute(drop_sql)
    
    # Create the view with route flags
    create_sql = """
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
          THEN 1 ELSE 0 END                          AS is_unknown,
               
        -- Include other relevant fields
        age_yrs,
        sex,
        serious_any
    FROM faers_events_2023_unique
    WHERE year = 2023;
    """
    
    conn.execute(create_sql)
    conn.commit()
    print("✓ View v_events_2023_route_flags created successfully")

def run_acceptance_checks(conn):
    """Run acceptance checks on the created view."""
    
    print("\n" + "="*60)
    print("ACCEPTANCE CHECKS")
    print("="*60)
    
    # 1) Quick row count
    print("\n1. Row count check:")
    count_query = "SELECT COUNT(*) AS n_rows FROM v_events_2023_route_flags;"
    count_df = pd.read_sql_query(count_query, conn)
    print(f"Total rows in view: {count_df['n_rows'].iloc[0]:,}")
    
    # 2) Route buckets for MINOXIDIL
    print("\n2. MINOXIDIL route distribution:")
    minox_query = """
    SELECT route_norm, 
           SUM(is_oral) AS oral, 
           SUM(is_topical) AS topical, 
           SUM(is_unknown) AS unknown, 
           COUNT(*) AS n
    FROM v_events_2023_route_flags
    WHERE ingredient_std = 'MINOXIDIL'
    GROUP BY route_norm
    ORDER BY n DESC
    LIMIT 20;
    """
    minox_df = pd.read_sql_query(minox_query, conn)
    print(minox_df.to_string(index=False))
    
    # 3) Role codes distribution
    print("\n3. Role code distribution for target drugs:")
    role_query = """
    SELECT role_cod, COUNT(*) AS n
    FROM v_events_2023_route_flags
    WHERE ingredient_std IN ('MINOXIDIL','HYDRALAZINE')
    GROUP BY role_cod
    ORDER BY n DESC;
    """
    role_df = pd.read_sql_query(role_query, conn)
    print(role_df.to_string(index=False))
    
    # 4) Sample minoxidil rows with flags
    print("\n4. Sample MINOXIDIL rows with route flags:")
    sample_query = """
    SELECT ingredient_std, route_norm, is_oral, is_topical, is_unknown, reaction_pt
    FROM v_events_2023_route_flags
    WHERE ingredient_std = 'MINOXIDIL'
    LIMIT 10;
    """
    sample_df = pd.read_sql_query(sample_query, conn)
    print(sample_df.to_string(index=False))
    
    # 5) Additional check: HYDRALAZINE distribution
    print("\n5. HYDRALAZINE route distribution:")
    hydral_query = """
    SELECT route_norm, 
           SUM(is_oral) AS oral, 
           SUM(is_topical) AS topical, 
           SUM(is_unknown) AS unknown, 
           COUNT(*) AS n
    FROM v_events_2023_route_flags
    WHERE ingredient_std = 'HYDRALAZINE'
    GROUP BY route_norm
    ORDER BY n DESC
    LIMIT 10;
    """
    hydral_df = pd.read_sql_query(hydral_query, conn)
    print(hydral_df.to_string(index=False))
    
    # 6) Flag overlap check (should be minimal)
    print("\n6. Route flag overlap check:")
    overlap_query = """
    SELECT 
        is_oral + is_topical + is_unknown AS flag_sum,
        COUNT(*) AS n
    FROM v_events_2023_route_flags
    WHERE ingredient_std IN ('MINOXIDIL','HYDRALAZINE')
    GROUP BY is_oral + is_topical + is_unknown
    ORDER BY flag_sum;
    """
    overlap_df = pd.read_sql_query(overlap_query, conn)
    print("Flag sum distribution (0=no flags, 1=one flag, 2+=overlap):")
    print(overlap_df.to_string(index=False))

def main():
    """Execute the route view creation and testing."""
    
    print("="*80)
    print("ROUTE NORMALIZATION VIEW CREATOR")
    print("="*80)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return 1
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Create the view
            create_route_view(conn)
            
            # Run acceptance checks
            run_acceptance_checks(conn)
            
        print("\n" + "="*80)
        print("ROUTE VIEW CREATION COMPLETE")
        print("="*80)
        print("✓ View v_events_2023_route_flags is ready for analysis")
        
    except Exception as e:
        print(f"\n❌ Failed to create route view: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
