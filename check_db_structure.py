#!/usr/bin/env python3
"""
FAERS Database Structure Discovery Script

This script analyzes the database to understand the schema and locate key FAERS tables.
It will identify tables, columns, and sample data for pharmacovigilance analysis.

Author: FAERS Signal Detection Team
Date: August 2025
"""

import sqlite3
import pandas as pd
import os

# Database configuration
DB_PATH = "data/faers+medicare.db"

def check_db_exists():
    """Check if database exists and is accessible."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    print(f"✓ Database found: {DB_PATH}")

def get_all_tables(conn):
    """List all user tables in the database."""
    print("\n" + "="*80)
    print("1. ALL TABLES IN DATABASE")
    print("="*80)
    
    # SQLite query to list all tables
    query = """
    SELECT name AS table_name, type
    FROM sqlite_master 
    WHERE type='table' 
    AND name NOT LIKE 'sqlite_%'
    ORDER BY name;
    """
    
    tables_df = pd.read_sql_query(query, conn)
    print(f"Found {len(tables_df)} tables:")
    print(tables_df.to_string(index=False))
    
    return tables_df['table_name'].tolist()

def get_table_columns(conn, table_name):
    """Get column information for a specific table."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Convert to DataFrame for easier handling
        columns_df = pd.DataFrame(columns, columns=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'])
        return columns_df[['name', 'type']].values.tolist()
    except Exception as e:
        print(f"Error getting columns for {table_name}: {e}")
        return []

def analyze_faers_tables(conn, all_tables):
    """Analyze tables that likely contain FAERS data."""
    print("\n" + "="*80)
    print("2. FAERS-RELATED TABLES AND COLUMNS")
    print("="*80)
    
    # Keywords to identify FAERS tables
    faers_keywords = ['demo', 'drug', 'prod', 'med', 'reac', 'event', 'ae']
    
    faers_tables = []
    for table in all_tables:
        table_lower = table.lower()
        if any(keyword in table_lower for keyword in faers_keywords):
            faers_tables.append(table)
    
    print(f"Found {len(faers_tables)} FAERS-related tables:")
    
    table_info = {}
    for table in faers_tables:
        print(f"\n--- {table} ---")
        columns = get_table_columns(conn, table)
        table_info[table] = columns
        
        if columns:
            columns_df = pd.DataFrame(columns, columns=['Column', 'Type'])
            print(columns_df.to_string(index=False))
        else:
            print("No columns found or error accessing table")
    
    return faers_tables, table_info

def get_sample_data(conn, table_name, limit=5):
    """Get sample rows from a table."""
    try:
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        sample_df = pd.read_sql_query(query, conn)
        return sample_df
    except Exception as e:
        print(f"Error sampling {table_name}: {e}")
        return pd.DataFrame()

def analyze_sample_data(conn, faers_tables):
    """Show sample data from key FAERS tables."""
    print("\n" + "="*80)
    print("3. SAMPLE DATA FROM KEY TABLES")
    print("="*80)
    
    for table in faers_tables[:6]:  # Limit to first 6 tables to avoid too much output
        print(f"\n--- SAMPLE DATA: {table} ---")
        sample_df = get_sample_data(conn, table, limit=3)
        
        if not sample_df.empty:
            # Focus on key columns if they exist
            key_columns = [
                'caseid', 'case_version', 'caseversion', 'primaryid',
                'ingredient_std', 'ingredient', 'prod_ai', 'brand_name', 
                'route', 'dosage_form', 'role_cod',
                'reaction_pt', 'pt_term', 'meddra_version',
                'age_yrs', 'sex', 'fda_dt', 'year', 'quarter'
            ]
            
            # Get columns that actually exist
            existing_cols = [col for col in key_columns if col in sample_df.columns]
            if existing_cols:
                display_df = sample_df[existing_cols]
            else:
                # If no key columns found, show first 10 columns
                display_df = sample_df.iloc[:, :10]
            
            print(display_df.to_string(index=False))
        else:
            print("No data or error accessing table")

def probe_target_drugs(conn, faers_tables):
    """Probe for minoxidil and hydralazine presence in drug tables."""
    print("\n" + "="*80)
    print("4. TARGET DRUG ANALYSIS: MINOXIDIL & HYDRALAZINE")
    print("="*80)
    
    drug_columns = ['ingredient_std', 'ingredient', 'prod_ai', 'brand_name']
    target_drugs = ['MINOXIDIL', 'HYDRALAZINE']
    
    results = []
    
    for table in faers_tables:
        # Get table columns
        columns = get_table_columns(conn, table)
        column_names = [col[0] for col in columns]
        
        # Check which drug columns exist in this table
        existing_drug_cols = [col for col in drug_columns if col in column_names]
        
        if not existing_drug_cols:
            continue
            
        print(f"\n--- DRUG SEARCH: {table} ---")
        
        for drug_col in existing_drug_cols:
            try:
                # Count rows for each target drug
                for drug in target_drugs:
                    query = f"""
                    SELECT COUNT(*) as count
                    FROM {table}
                    WHERE UPPER({drug_col}) LIKE '%{drug}%'
                    """
                    
                    count_df = pd.read_sql_query(query, conn)
                    count = count_df['count'].iloc[0]
                    
                    if count > 0:
                        results.append({
                            'Table': table,
                            'Column': drug_col,
                            'Drug': drug,
                            'Count': count
                        })
                        print(f"  {drug_col}: {drug} → {count} rows")
                
            except Exception as e:
                print(f"  Error searching {drug_col}: {e}")
    
    if results:
        print(f"\n--- SUMMARY: TARGET DRUG COUNTS ---")
        results_df = pd.DataFrame(results)
        print(results_df.to_string(index=False))
        return results_df
    else:
        print("No target drugs found in any table")
        return pd.DataFrame()

def analyze_routes_and_roles(conn, faers_tables, drug_results):
    """Analyze route and role_cod values for target drugs."""
    print("\n" + "="*80)
    print("5. ROUTE AND ROLE ANALYSIS FOR TARGET DRUGS")
    print("="*80)
    
    if drug_results.empty:
        print("No target drugs found - skipping route/role analysis")
        return
    
    # Get unique table-column combinations where drugs were found
    drug_locations = drug_results[['Table', 'Column']].drop_duplicates()
    
    for _, row in drug_locations.iterrows():
        table = row['Table']
        drug_col = row['Column']
        
        print(f"\n--- ROUTES & ROLES: {table}.{drug_col} ---")
        
        # Get table columns to check for route and role_cod
        columns = get_table_columns(conn, table)
        column_names = [col[0] for col in columns]
        
        # Check for route information
        if 'route' in column_names:
            try:
                route_query = f"""
                SELECT DISTINCT UPPER(TRIM(route)) as route, COUNT(*) as count
                FROM {table}
                WHERE UPPER({drug_col}) LIKE '%MINOXIDIL%' OR UPPER({drug_col}) LIKE '%HYDRALAZINE%'
                GROUP BY UPPER(TRIM(route))
                ORDER BY count DESC
                """
                
                route_df = pd.read_sql_query(route_query, conn)
                if not route_df.empty:
                    print("Routes found:")
                    print(route_df.to_string(index=False))
                else:
                    print("No route data found")
                    
            except Exception as e:
                print(f"Error analyzing routes: {e}")
        
        # Check for role_cod information
        if 'role_cod' in column_names:
            try:
                role_query = f"""
                SELECT DISTINCT UPPER(TRIM(role_cod)) as role_cod, COUNT(*) as count
                FROM {table}
                WHERE UPPER({drug_col}) LIKE '%MINOXIDIL%' OR UPPER({drug_col}) LIKE '%HYDRALAZINE%'
                GROUP BY UPPER(TRIM(role_cod))
                ORDER BY count DESC
                """
                
                role_df = pd.read_sql_query(role_query, conn)
                if not role_df.empty:
                    print("Role codes found:")
                    print(role_df.to_string(index=False))
                else:
                    print("No role_cod data found")
                    
            except Exception as e:
                print(f"Error analyzing role codes: {e}")

def get_table_row_counts(conn, tables):
    """Get row counts for all tables."""
    print("\n" + "="*80)
    print("6. TABLE ROW COUNTS")
    print("="*80)
    
    counts = []
    for table in tables:
        try:
            query = f"SELECT COUNT(*) as count FROM {table}"
            count_df = pd.read_sql_query(query, conn)
            count = count_df['count'].iloc[0]
            counts.append({'Table': table, 'Row_Count': count})
        except Exception as e:
            counts.append({'Table': table, 'Row_Count': f'Error: {e}'})
    
    counts_df = pd.DataFrame(counts)
    print(counts_df.to_string(index=False))

def main():
    """Execute the complete database structure analysis."""
    
    print("="*80)
    print("FAERS DATABASE STRUCTURE DISCOVERY")
    print("="*80)
    
    try:
        # Check database existence
        check_db_exists()
        
        # Connect to database
        with sqlite3.connect(DB_PATH) as conn:
            
            # 1. List all tables
            all_tables = get_all_tables(conn)
            
            # 2. Analyze FAERS-related tables and their columns
            faers_tables, table_info = analyze_faers_tables(conn, all_tables)
            
            # 3. Show sample data
            analyze_sample_data(conn, faers_tables)
            
            # 4. Probe for target drugs
            drug_results = probe_target_drugs(conn, faers_tables)
            
            # 5. Analyze routes and roles for target drugs
            analyze_routes_and_roles(conn, faers_tables, drug_results)
            
            # 6. Get table row counts
            get_table_row_counts(conn, all_tables)
            
        print("\n" + "="*80)
        print("DATABASE ANALYSIS COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
