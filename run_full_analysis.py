import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Set aesthetic styling for charts
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Helvetica'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

output_dir = './charts'
os.makedirs(output_dir, exist_ok=True)

print("Starting Full VoltRelay Energy Analysis Pipeline...")

# ==========================================
# 1. LOAD DATASETS
# ==========================================
batteries = pd.read_csv('batteries.csv')
city_context = pd.read_csv('city_daily_context.csv')
fleet_partners = pd.read_csv('fleet_partners.csv')
riders = pd.read_csv('riders.csv')
stations = pd.read_csv('stations.csv')
support_tickets = pd.read_csv('support_tickets.csv')
hourly_status = pd.read_csv('station_hourly_status.csv')
swap_events = pd.read_csv('swap_events.csv')

# ==========================================
# 2. DATA CLEANING & STANDARDIZATION
# ==========================================
# Standardize riders home_city
city_map = {
    'Bengaluru': 'Bengaluru', 'BLR': 'Bengaluru', 'bengaluru': 'Bengaluru', 'Bangalore': 'Bengaluru',
    'Delhi NCR': 'Delhi NCR', 'Delhi': 'Delhi NCR', 'New Delhi': 'Delhi NCR', 'Gurgaon': 'Delhi NCR',
    'Hyderabad': 'Hyderabad', 'HYD': 'Hyderabad', 'Hyd': 'Hyderabad', 'hyderabad': 'Hyderabad',
    'Pune': 'Pune', 'PUN': 'Pune', 'pune': 'Pune',
    'Mumbai': 'Mumbai', 'MUM': 'Mumbai', 'Bombay': 'Mumbai',
    'Jaipur': 'Jaipur', 'JAI': 'Jaipur', 'jaipur': 'Jaipur'
}
riders['home_city_clean'] = riders['home_city'].map(city_map).fillna(riders['home_city'])
riders['partner_id_clean'] = riders['partner_id'].fillna('Independent/Retail')
riders['is_fleet'] = riders['partner_id'].notnull()

# Datetime parsing
swap_events['event_ts'] = pd.to_datetime(swap_events['event_ts'])
swap_events['date'] = swap_events['event_ts'].dt.date
swap_events['date_str'] = swap_events['event_ts'].dt.strftime('%Y-%m-%d')
swap_events['hour'] = swap_events['event_ts'].dt.hour
swap_events['day_of_week'] = swap_events['event_ts'].dt.day_name()
swap_events['day_type'] = np.where(swap_events['event_ts'].dt.dayofweek >= 5, 'Weekend', 'Weekday')
swap_events['hour_start_str'] = swap_events['event_ts'].dt.strftime('%Y-%m-%d %H:00:00')

hourly_status['hour_start_dt'] = pd.to_datetime(hourly_status['hour_start'])
hourly_status['date_str'] = hourly_status['hour_start_dt'].dt.strftime('%Y-%m-%d')
hourly_status['hour'] = hourly_status['hour_start_dt'].dt.hour
hourly_status['day_of_week'] = hourly_status['hour_start_dt'].dt.day_name()

city_context['date_dt'] = pd.to_datetime(city_context['date'])
city_context['date_str'] = city_context['date']

support_tickets['created_ts_dt'] = pd.to_datetime(support_tickets['created_ts'])
support_tickets['date_str'] = support_tickets['created_ts_dt'].dt.strftime('%Y-%m-%d')

batteries['manufacture_date_dt'] = pd.to_datetime(batteries['manufacture_date'])
batteries['commission_date_dt'] = pd.to_datetime(batteries['commission_date'])

# Define Stockouts in swap_events
swap_events['is_direct_stockout'] = (swap_events['event_type'] == 'failed_no_charged_battery').astype(int)
swap_events['is_abandoned'] = (swap_events['event_type'] == 'abandoned_queue').astype(int)
swap_events['is_stockout_event'] = (swap_events['event_type'].isin(['failed_no_charged_battery', 'abandoned_queue'])).astype(int)

# Define Stockouts in hourly_status
hourly_status['is_2w_stockout_hour'] = (hourly_status['charged_2w_min'] == 0).astype(int)
hourly_status['is_3w_stockout_hour'] = ((hourly_status['charged_3w_min'] == 0) & (hourly_status['charged_3w_min'].notnull())).astype(int)

print(f"Total Swap Attempts: {len(swap_events):,}")
print(f"Total Direct Stockouts (failed_no_charged_battery): {swap_events['is_direct_stockout'].sum():,} ({swap_events['is_direct_stockout'].mean()*100:.2f}%)")
print(f"Total Abandoned Queue Events: {swap_events['is_abandoned'].sum():,} ({swap_events['is_abandoned'].mean()*100:.2f}%)")
print(f"Total Combined Stockout Impacted Swaps: {swap_events['is_stockout_event'].sum():,} ({swap_events['is_stockout_event'].mean()*100:.2f}%)")

# ==========================================
# 3. MERGE CORE MASTER TABLE (Sample/Agg for Performance)
# ==========================================
# Merge Station info to swap_events
swaps_merged = swap_events.merge(stations[['station_id', 'city', 'zone', 'location_type', 'host_type', 'slots_2w', 'slots_3w', 'inventory_target_2w', 'connectivity_tier', 'charger_generation']], on='station_id', how='left')

# Merge Rider info
swaps_merged = swaps_merged.merge(riders[['rider_id', 'partner_id_clean', 'is_fleet', 'vehicle_class', 'plan_type', 'declared_shift']], on='rider_id', how='left')

# Merge Fleet info
swaps_merged = swaps_merged.merge(fleet_partners[['partner_id', 'partner_name', 'partner_segment', 'contract_type']], left_on='partner_id_clean', right_on='partner_id', how='left')

# Merge City Context on city + date
swaps_merged = swaps_merged.merge(city_context[['city', 'date_str', 'max_temp_c', 'rainfall_mm', 'heat_alert', 'flood_disruption', 'festival_or_event', 'grid_outage_hours', 'competitor_promo_active', 'ecommerce_sale_event']], on=['city', 'date_str'], how='left')

print("Core dataset merged successfully! Merged shape:", swaps_merged.shape)

# Save intermediate summary metrics to file
with open("analysis_summary.txt", "w") as f:
    f.write("=== VOLTRELAY ENERGY CORE DATA ANALYTICS RESULTS ===\n\n")

    # Metric 1: Stockout by City
    city_summary = swaps_merged.groupby('city').agg(
        total_swaps=('event_id', 'count'),
        stockout_events=('is_stockout_event', 'sum'),
        direct_stockouts=('is_direct_stockout', 'sum'),
        abandoned=('is_abandoned', 'sum'),
        avg_queue_sec=('queue_wait_sec', 'mean')
    ).reset_index()
    city_summary['stockout_rate_pct'] = (city_summary['stockout_events'] / city_summary['total_swaps']) * 100
    city_summary = city_summary.sort_values(by='stockout_rate_pct', ascending=False)
    
    f.write("--- STOCKOUT FREQUENCY BY CITY ---\n")
    f.write(city_summary.to_string(index=False) + "\n\n")

    # Metric 2: Stockout by Station (Top 15 worst stations)
    stn_summary = swaps_merged.groupby(['station_id', 'city', 'zone', 'location_type', 'host_type']).agg(
        total_swaps=('event_id', 'count'),
        stockout_events=('is_stockout_event', 'sum'),
        direct_stockouts=('is_direct_stockout', 'sum'),
        avg_queue_sec=('queue_wait_sec', 'mean')
    ).reset_index()
    stn_summary['stockout_rate_pct'] = (stn_summary['stockout_events'] / stn_summary['total_swaps']) * 100
    top15_stns = stn_summary.sort_values(by='stockout_rate_pct', ascending=False).head(15)
    
    f.write("--- TOP 15 WORST STATIONS BY STOCKOUT RATE ---\n")
    f.write(top15_stns.to_string(index=False) + "\n\n")

    # Metric 3: Peak Hours & Day of Week
    hour_summary = swaps_merged.groupby(['day_of_week', 'hour']).agg(
        total_swaps=('event_id', 'count'),
        stockout_events=('is_stockout_event', 'sum'),
        avg_queue_sec=('queue_wait_sec', 'mean')
    ).reset_index()
    hour_summary['stockout_rate_pct'] = (hour_summary['stockout_events'] / hour_summary['total_swaps']) * 100
    
    peak_hours = swaps_merged.groupby('hour').agg(
        total_swaps=('event_id', 'count'),
        stockout_events=('is_stockout_event', 'sum'),
        avg_queue_sec=('queue_wait_sec', 'mean')
    ).reset_index()
    peak_hours['stockout_rate_pct'] = (peak_hours['stockout_events'] / peak_hours['total_swaps']) * 100
    
    f.write("--- STOCKOUT RATE BY HOUR OF DAY ---\n")
    f.write(peak_hours.sort_values(by='hour').to_string(index=False) + "\n\n")

    # Metric 4: Fleet vs Independent Riders
    fleet_summary = swaps_merged.groupby(['is_fleet', 'partner_name']).agg(
        total_swaps=('event_id', 'count'),
        stockout_events=('is_stockout_event', 'sum'),
        avg_queue_sec=('queue_wait_sec', 'mean')
    ).reset_index()
    fleet_summary['stockout_rate_pct'] = (fleet_summary['stockout_events'] / fleet_summary['total_swaps']) * 100
    
    f.write("--- FLEET PARTNER VS RETAIL STOCKOUT RATES ---\n")
    f.write(fleet_summary.sort_values(by='stockout_rate_pct', ascending=False).to_string(index=False) + "\n\n")

    # Metric 5: External Weather & Daily Context Correlations
    daily_city = swaps_merged.groupby(['city', 'date_str', 'max_temp_c', 'heat_alert', 'flood_disruption', 'grid_outage_hours', 'ecommerce_sale_event']).agg(
        total_swaps=('event_id', 'count'),
        stockout_events=('is_stockout_event', 'sum')
    ).reset_index()
    daily_city['stockout_rate_pct'] = (daily_city['stockout_events'] / daily_city['total_swaps']) * 100

    f.write("--- CONTEXTUAL IMPACT ON STOCKOUTS ---\n")
    f.write(f"Average Stockout Rate on Heat Alert Days: {daily_city[daily_city['heat_alert']==True]['stockout_rate_pct'].mean():.2f}%\n")
    f.write(f"Average Stockout Rate on Normal Temp Days: {daily_city[daily_city['heat_alert']==False]['stockout_rate_pct'].mean():.2f}%\n")
    f.write(f"Average Stockout Rate on E-commerce Sale Days: {daily_city[daily_city['ecommerce_sale_event']==True]['stockout_rate_pct'].mean():.2f}%\n")
    f.write(f"Average Stockout Rate on Normal Days: {daily_city[daily_city['ecommerce_sale_event']==False]['stockout_rate_pct'].mean():.2f}%\n\n")

    # Metric 6: Support Tickets Correlation
    stn_tickets = support_tickets[support_tickets['category'].isin(['long_queue', 'no_battery', 'station_issue', 'other'])].groupby('station_id').size().reset_index(name='ticket_count')
    stn_merged_tickets = stn_summary.merge(stn_tickets, on='station_id', how='left').fillna({'ticket_count': 0})
    corr = stn_merged_tickets['stockout_events'].corr(stn_merged_tickets['ticket_count'])
    f.write(f"Correlation between Station Stockout Events and Support Tickets: {corr:.4f}\n\n")

    # Metric 7: Battery Health & Age Degradation
    batteries['age_months'] = (pd.to_datetime('2025-06-30') - batteries['commission_date_dt']).dt.days / 30.44
    batteries['soh_loss'] = batteries['initial_soh_pct'] - batteries['current_soh_pct']
    f.write("--- BATTERY HEALTH & AGE METRICS ---\n")
    f.write(f"Average Battery Age (Months): {batteries['age_months'].mean():.1f}\n")
    f.write(f"Average SOH Degradation (%): {batteries['soh_loss'].mean():.2f}%\n")
    f.write(f"Retired Battery Count: {(batteries['retired_date'].notnull()).sum()}\n\n")

print("Summary statistics computed and saved to analysis_summary.txt!")
