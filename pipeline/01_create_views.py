#!/usr/bin/env python3
"""
FAERS Database Setup for Signal Detection (DuckDB)

Creates the views used by the analysis & Streamlit app:
- v_events_2023_route_flags  (route normalization + flags)
- v_events_2023_cohorts      (cohort assignment incl. OTHER)
- v_signal_2x2_2023          (cohort × PT 2x2s)
- v_anydrug_signal_2x2_2023  (ingredient × PT 2x2s, PS only)
- v_all_drugs_2023           (helper: list of all ingredients)
- v_all_pts_2023             (helper: list of all PTs)

Author: FAERS Signal Detection Team
Date: August 2025
"""

import os
import sys
import duckdb
import pandas as pd

DB_PATH = "data/faers+medicare.duckdb"

def create_faers_events_2023_unique(conn):
    """Create unified FAERS events table from Q1 2023 raw tables."""
    print("Creating faers_events_2023_unique...")
    conn.execute("DROP TABLE IF EXISTS faers_events_2023_unique")
    sql = """
    CREATE TABLE faers_events_2023_unique AS
    SELECT
        demo.primaryid,
        demo.caseid,
        '2023' AS year,
        'Q1' AS quarter,
        UPPER(TRIM(drug.drugname)) AS ingredient_std,
        drug.role_cod,
        drug.route,
        reac.pt AS reaction_pt
    FROM faers_demo_2023q1 demo
    LEFT JOIN faers_drug_2023q1 drug ON demo.primaryid = drug.primaryid
    LEFT JOIN faers_reac_2023q1 reac ON demo.primaryid = reac.primaryid
    WHERE drug.role_cod IS NOT NULL AND reac.pt IS NOT NULL;
    """
    conn.execute(sql)
    print("✓ faers_events_2023_unique created")

def create_route_flags_view(conn):
    """Create route normalization view with boolean flags."""
    print("Creating v_events_2023_route_flags view...")
    conn.execute("DROP VIEW IF EXISTS v_events_2023_route_flags")
    sql = """
    CREATE VIEW v_events_2023_route_flags AS
    SELECT
        year,
        quarter,
        primaryid,
        caseid,
        UPPER(TRIM(COALESCE(ingredient_std,''))) AS ingredient_std,
        UPPER(TRIM(COALESCE(reaction_pt,'')))    AS reaction_pt,
        UPPER(TRIM(COALESCE(role_cod,'')))       AS role_cod,
        UPPER(TRIM(COALESCE(route,'')))          AS route_norm,
        CASE
          WHEN UPPER(TRIM(COALESCE(route,''))) IN ('ORAL','PO','BY MOUTH')
               OR UPPER(TRIM(COALESCE(route,''))) LIKE 'ORAL %'
          THEN 1 ELSE 0 END AS is_oral,
        CASE
          WHEN UPPER(TRIM(COALESCE(route,''))) IN ('TOPICAL','CUTANEOUS','SCALP','TRANSDERMAL')
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%TOPICAL%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%CUTANEOUS%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%SCALP%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%LOTION%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%FOAM%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%SOLUTION%'
               OR UPPER(TRIM(COALESCE(route,''))) LIKE '%SOLN%'
          THEN 1 ELSE 0 END AS is_topical,
        CASE
          WHEN route IS NULL OR TRIM(route) = ''
               OR UPPER(TRIM(route)) IN ('UNKNOWN','UNSPECIFIED','NONE')
          THEN 1 ELSE 0 END AS is_unknown
    FROM faers_events_2023_unique
    WHERE year = 2023;
    """
    conn.execute(sql)
    print("✓ v_events_2023_route_flags created")


def create_cohorts_view(conn):
    """Create cohort definition view with comprehensive OTHER background."""
    print("Creating v_events_2023_cohorts view...")
    conn.execute("DROP VIEW IF EXISTS v_events_2023_cohorts")
    sql = """
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
          WHEN ingredient_std = 'MINOXIDIL' AND is_topical = 1
            THEN 'MINOXIDIL_TOPICAL'
          WHEN ingredient_std LIKE '%HYDRALAZINE%'
            THEN 'HYDRALAZINE'
          ELSE 'OTHER'
        END AS cohort
    FROM v_events_2023_route_flags
    WHERE role_cod = 'PS' AND year = 2023;
    """
    conn.execute(sql)
    print("✓ v_events_2023_cohorts created")


def create_2x2_view(conn):
    """Create 2x2 contingency table view (cohort × reaction)."""
    print("Creating v_signal_2x2_2023 view...")
    conn.execute("DROP VIEW IF EXISTS v_signal_2x2_2023")
    
    sql = """
    CREATE VIEW v_signal_2x2_2023 AS
    WITH cohort_reaction_counts AS (
        SELECT cohort, reaction_pt, COUNT(DISTINCT primaryid) AS a
        FROM v_events_2023_cohorts
        GROUP BY cohort, reaction_pt
    ),
    cohort_totals AS (
        SELECT cohort, COUNT(DISTINCT primaryid) AS total_cohort
        FROM v_events_2023_cohorts
        GROUP BY cohort
    ),
    reaction_totals AS (
        SELECT reaction_pt, COUNT(DISTINCT primaryid) AS total_with_event
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
        ((g.grand_total - ct.total_cohort) - (rt.total_with_event - crc.a)) AS d
    FROM cohort_reaction_counts crc
    JOIN cohort_totals ct   ON ct.cohort = crc.cohort
    JOIN reaction_totals rt ON rt.reaction_pt = crc.reaction_pt
    CROSS JOIN grand g
    """
    
    conn.execute(sql)
    print("✓ v_signal_2x2_2023 created")



def create_anydrug_2x2_view(conn):
    """Create 2x2 view at ingredient (drug) × reaction granularity (PS only)."""
    print("Creating v_anydrug_signal_2x2_2023 view...")
    conn.execute("DROP VIEW IF EXISTS v_anydrug_signal_2x2_2023")
    sql = """
    CREATE VIEW v_anydrug_signal_2x2_2023 AS
    WITH base AS (
      SELECT year, primaryid,
             UPPER(TRIM(ingredient_std)) AS ingredient_std,
             UPPER(TRIM(reaction_pt))    AS reaction_pt
      FROM v_events_2023_route_flags
      WHERE year = 2023
        AND role_cod = 'PS'
        AND TRIM(ingredient_std) <> ''
        AND TRIM(reaction_pt) <> ''
    ),
    drug_event AS (
      SELECT ingredient_std, reaction_pt, COUNT(DISTINCT primaryid) AS a
      FROM base GROUP BY ingredient_std, reaction_pt
    ),
    drug_totals AS (
      SELECT ingredient_std, COUNT(DISTINCT primaryid) AS total_drug
      FROM base GROUP BY ingredient_std
    ),
    event_totals AS (
      SELECT reaction_pt, COUNT(DISTINCT primaryid) AS total_event
      FROM base GROUP BY reaction_pt
    ),
    grand AS ( SELECT COUNT(DISTINCT primaryid) AS grand_total FROM base )
    SELECT
      de.ingredient_std,
      de.reaction_pt,
      de.a,
      (dt.total_drug - de.a)             AS b,
      (et.total_event - de.a)            AS c,
      ((g.grand_total - dt.total_drug)
        - (et.total_event - de.a))       AS d
    FROM drug_event   de
    JOIN drug_totals  dt ON dt.ingredient_std = de.ingredient_std
    JOIN event_totals et ON et.reaction_pt    = de.reaction_pt
    CROSS JOIN grand  g
    """
    conn.execute(sql)
    print("✓ v_anydrug_signal_2x2_2023 created")


def create_lists_for_app(conn):
    """Helper views for fast dropdowns in Streamlit."""
    print("Creating helper views v_all_drugs_2023, v_all_pts_2023 ...")
    conn.execute("DROP VIEW IF EXISTS v_all_drugs_2023")
    conn.execute("DROP VIEW IF EXISTS v_all_pts_2023")

    conn.execute("""
      CREATE VIEW v_all_drugs_2023 AS
      SELECT DISTINCT ingredient_std
      FROM v_anydrug_signal_2x2_2023
      WHERE ingredient_std <> ''
      ORDER BY ingredient_std;
    """)
    conn.execute("""
      CREATE VIEW v_all_pts_2023 AS
      SELECT DISTINCT reaction_pt
      FROM v_anydrug_signal_2x2_2023
      WHERE reaction_pt <> ''
      ORDER BY reaction_pt;
    """)
    print("✓ helper views created")


def validate_views(conn):
    """Basic validation prints."""
    print("\nValidating views...")
    df = pd.read_sql_query(
        "SELECT table_name AS name FROM information_schema.tables WHERE table_type='VIEW' AND table_name LIKE 'v_%2023%' ORDER BY table_name;",
        conn
    )
    print(f"✓ Created {len(df)} views: {list(df['name'])}")

    checks = [
        ("Route flags",      "SELECT COUNT(*) AS n FROM v_events_2023_route_flags"),
        ("Cohorts",          "SELECT COUNT(*) AS n FROM v_events_2023_cohorts"),
        ("2x2 (cohorts)",    "SELECT COUNT(*) AS n FROM v_signal_2x2_2023"),
        ("2x2 (any drug)",   "SELECT COUNT(*) AS n FROM v_anydrug_signal_2x2_2023"),
        ("All drugs helper", "SELECT COUNT(*) AS n FROM v_all_drugs_2023"),
        ("All PTs helper",   "SELECT COUNT(*) AS n FROM v_all_pts_2023"),
    ]
    for label, q in checks:
        n = pd.read_sql_query(q, conn).iloc[0, 0]
        print(f"✓ {label}: {n:,} rows")

    # Example sanity peek
    peek = pd.read_sql_query("""
        SELECT ingredient_std, reaction_pt, a, b, c, d
        FROM v_anydrug_signal_2x2_2023
        WHERE reaction_pt='PERICARDIAL EFFUSION'
        ORDER BY a DESC LIMIT 5;
    """, conn)
    if not peek.empty:
        print("\nTop PERICARDIAL EFFUSION (any drug):")
        print(peek.to_string(index=False))


def main():
    print("=" * 80)
    print("FAERS SIGNAL DETECTION DATABASE SETUP (DuckDB)")
    print("=" * 80)

    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("Run data ingestion first.")
        return 1

    try:
        conn = duckdb.connect(DB_PATH)

        create_faers_events_2023_unique(conn)
        create_route_flags_view(conn)
        create_cohorts_view(conn)
        create_2x2_view(conn)
        create_anydrug_2x2_view(conn)
        create_lists_for_app(conn)
        validate_views(conn)

        conn.close()

        print("\n" + "=" * 80)
        print("DATABASE SETUP COMPLETE")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback; traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
