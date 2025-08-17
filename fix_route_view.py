#!/usr/bin/env python3
"""
Check and fix the route view
"""

import sqlite3
import pandas as pd

with sqlite3.connect('data/faers+medicare.db') as conn:
    
    # Get the view definition
    view_def_query = """
    SELECT sql FROM sqlite_master 
    WHERE type='view' AND name='v_events_2023_route_flags'
    """
    
    view_def = pd.read_sql_query(view_def_query, conn)
    if len(view_def) > 0:
        print("Current view definition:")
        print(view_def['sql'].iloc[0])
    
    print("\nDropping and recreating view...")
    
    # Drop the problematic view
    conn.execute("DROP VIEW IF EXISTS v_events_2023_route_flags;")
    
    # Create a simpler, more efficient view
    create_sql = """
    CREATE VIEW v_events_2023_route_flags AS
    SELECT
        year,
        quarter,
        primaryid,
        caseid,
        ingredient_std,
        reaction_pt,
        role_cod,
        route,
        
        -- Simplified route normalization
        CASE 
            WHEN route IS NULL THEN ''
            ELSE UPPER(TRIM(route))
        END AS route_norm,
        
        -- Route flags with simpler logic
        CASE 
            WHEN UPPER(TRIM(COALESCE(route,''))) IN ('ORAL','PO') THEN 1 
            ELSE 0 
        END AS is_oral,
        
        CASE 
            WHEN UPPER(TRIM(COALESCE(route,''))) IN ('TOPICAL','CUTANEOUS','SCALP') THEN 1 
            ELSE 0 
        END AS is_topical,
        
        CASE 
            WHEN route IS NULL OR TRIM(route) = '' OR UPPER(TRIM(route)) = 'UNKNOWN' THEN 1 
            ELSE 0 
        END AS is_unknown,
        
        age_yrs,
        sex,
        serious_any
    FROM faers_events_2023_unique
    WHERE year = 2023;
    """
    
    conn.execute(create_sql)
    conn.commit()
    print("✓ View recreated with simpler logic")
    
    # Test the new view
    print("\nTesting new view...")
    
    count_query = "SELECT COUNT(*) as total_rows FROM v_events_2023_route_flags"
    count_result = pd.read_sql_query(count_query, conn)
    print(f"Total rows: {count_result['total_rows'].iloc[0]:,}")
    
    # Quick MINOXIDIL test
    minox_test = """
    SELECT COUNT(*) as minoxidil_count
    FROM v_events_2023_route_flags 
    WHERE ingredient_std = 'MINOXIDIL'
    """
    
    minox_result = pd.read_sql_query(minox_test, conn)
    print(f"MINOXIDIL rows: {minox_result['minoxidil_count'].iloc[0]:,}")
    
    # Route distribution for MINOXIDIL
    route_dist = """
    SELECT 
        route_norm,
        SUM(is_oral) as oral,
        SUM(is_topical) as topical,
        SUM(is_unknown) as unknown,
        COUNT(*) as total
    FROM v_events_2023_route_flags 
    WHERE ingredient_std = 'MINOXIDIL'
    GROUP BY route_norm
    ORDER BY total DESC
    LIMIT 10
    """
    
    route_result = pd.read_sql_query(route_dist, conn)
    print("\nMINOXIDIL route distribution:")
    print(route_result.to_string(index=False))

print("View check complete!")
