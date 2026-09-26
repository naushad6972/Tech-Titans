import pandas as pd
import numpy as np
import os

files_meta = [
    ('batteries.csv', 'Battery unit master data'),
    ('city_daily_context.csv', 'City-level daily weather and context factors'),
    ('fleet_partners.csv', 'Fleet-affiliated rider companies and contracts'),
    ('riders.csv', 'Individual rider profiles'),
    ('stations.csv', 'Swap station/cabinet master data'),
    ('support_tickets.csv', 'Customer complaints and issues'),
    ('station_hourly_status.csv', 'Hourly battery availability per station'),
    ('swap_events.csv', 'Actual swap transaction log')
]

print("=== COMPLETE SUMMARY FOR TASK 1 ===")
for fname, desc in files_meta:
    df = pd.read_csv(fname)
    print(f"\n### File: `{fname}` — {desc}")
    print(f"- **Shape**: {df.shape[0]:,} rows, {df.shape[1]} columns")
    print(f"- **Duplicate Rows**: {df.duplicated().sum()}")
    print(f"- **Columns & Missing Data**:")
    for col in df.columns:
        n_null = df[col].isnull().sum()
        pct_null = (n_null / len(df)) * 100
        dtype = str(df[col].dtype)
        n_uniq = df[col].nunique()
        print(f"  - `{col}` ({dtype}): {n_null:,} nulls ({pct_null:.2f}%) | {n_uniq:,} unique values")
