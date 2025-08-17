#!/usr/bin/env python3
"""
Simple route view test
"""

import sqlite3
import pandas as pd

print("Connecting to database...")
with sqlite3.connect('data/faers+medicare.db') as conn:
    print("Connected. Checking view...")
    
    # Check if view exists
    view_check = pd.read_sql_query("""
    SELECT name FROM sqlite_master 
    WHERE type='view' AND name='v_events_2023_route_flags'
    """, conn)
    
    if len(view_check) > 0:
        print('✓ View v_events_2023_route_flags exists')
        
        print("Running count query...")
        # Simple count first
        count_query = "SELECT COUNT(*) as total_rows FROM v_events_2023_route_flags"
        count_result = pd.read_sql_query(count_query, conn)
        print(f"Total rows: {count_result['total_rows'].iloc[0]:,}")
        
        print("Running MINOXIDIL test...")
        # Test MINOXIDIL specifically
        minox_query = """
        SELECT COUNT(*) as minoxidil_rows
        FROM v_events_2023_route_flags
        WHERE ingredient_std = 'MINOXIDIL'
        LIMIT 1
        """
        
        minox_result = pd.read_sql_query(minox_query, conn)
        print(f"MINOXIDIL rows: {minox_result['minoxidil_rows'].iloc[0]:,}")
        
        print("All tests complete!")
        
    else:
        print('❌ View not found')

print("Script finished.")
