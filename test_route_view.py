#!/usr/bin/env python3
"""
Quick test of the route view
"""

import sqlite3
import pandas as pd

with sqlite3.connect('data/faers+medicare.db') as conn:
    # Check if view exists
    view_check = pd.read_sql_query("""
    SELECT name FROM sqlite_master 
    WHERE type='view' AND name='v_events_2023_route_flags'
    """, conn)
    
    if len(view_check) > 0:
        print('✓ View v_events_2023_route_flags exists')
        
        # Quick test query
        test_query = """
        SELECT COUNT(*) as total_rows,
               SUM(CASE WHEN ingredient_std='MINOXIDIL' THEN 1 ELSE 0 END) as minoxidil_rows,
               SUM(CASE WHEN ingredient_std='HYDRALAZINE' THEN 1 ELSE 0 END) as hydralazine_rows
        FROM v_events_2023_route_flags
        """
        
        result = pd.read_sql_query(test_query, conn)
        print('View summary:')
        print(result.to_string(index=False))
        
        # MINOXIDIL route flags
        minox_query = """
        SELECT 
            SUM(is_oral) as oral_cases,
            SUM(is_topical) as topical_cases, 
            SUM(is_unknown) as unknown_cases,
            COUNT(*) as total_cases
        FROM v_events_2023_route_flags
        WHERE ingredient_std = 'MINOXIDIL'
        """
        
        minox_result = pd.read_sql_query(minox_query, conn)
        print('\nMINOXIDIL route flags summary:')
        print(minox_result.to_string(index=False))
        
        # HYDRALAZINE route flags
        hydral_query = """
        SELECT 
            SUM(is_oral) as oral_cases,
            SUM(is_topical) as topical_cases, 
            SUM(is_unknown) as unknown_cases,
            COUNT(*) as total_cases
        FROM v_events_2023_route_flags
        WHERE ingredient_std = 'HYDRALAZINE'
        """
        
        hydral_result = pd.read_sql_query(hydral_query, conn)
        print('\nHYDRALAZINE route flags summary:')
        print(hydral_result.to_string(index=False))
        
    else:
        print('❌ View not found')
