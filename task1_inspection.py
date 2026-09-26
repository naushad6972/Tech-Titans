import pandas as pd
import numpy as np
import os

files = [
    'batteries.csv',
    'city_daily_context.csv',
    'fleet_partners.csv',
    'riders.csv',
    'stations.csv',
    'support_tickets.csv',
    'station_hourly_status.csv',
    'swap_events.csv'
]

print("================================================================================")
print("TASK 1: DATA LOADING & INITIAL INSPECTION REPORT")
print("================================================================================")

data_dict = {}

for f in files:
    print(f"\n--------------------------------------------------------------------------------")
    print(f"FILE: {f}")
    print(f"--------------------------------------------------------------------------------")
    
    filepath = os.path.join(".", f)
    df = pd.read_csv(filepath)
    data_dict[f] = df
    
    print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print("\nColumns & Data Types & Missing Values (%):")
    
    null_counts = df.isnull().sum()
    null_pcts = (null_counts / len(df)) * 100
    
    inspect_df = pd.DataFrame({
        'Column': df.columns,
        'Dtype': df.dtypes.astype(str),
        'Null Count': null_counts.values,
        'Null %': null_pcts.values.round(2)
    })
    print(inspect_df.to_string(index=False))
    
    dup_count = df.duplicated().sum()
    print(f"\nDuplicate Rows: {dup_count} ({round(dup_count/len(df)*100, 2)}%)")
    
    print("\nFirst 5 Rows Sample:")
    print(df.head(5).to_string())
    print("\nSummary Statistics / Unique Values:")
    for col in df.columns:
        n_unique = df[col].nunique()
        sample_vals = df[col].dropna().unique()[:3]
        print(f"  - {col}: {n_unique} unique values | Samples: {sample_vals}")

print("\n================================================================================")
print("DATA QUALITY ISSUES SUMMARY & FLAGGING")
print("================================================================================")
