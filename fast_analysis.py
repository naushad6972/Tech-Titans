import pandas as pd
import numpy as np
import time

t0 = time.time()
print("Loading datasets with optimized dtypes...")

stations = pd.read_csv('stations.csv')
riders = pd.read_csv('riders.csv')
fleet_partners = pd.read_csv('fleet_partners.csv')
city_context = pd.read_csv('city_daily_context.csv')
support_tickets = pd.read_csv('support_tickets.csv')
batteries = pd.read_csv('batteries.csv')
hourly_status = pd.read_csv('station_hourly_status.csv')

# Clean Riders
city_map = {
    'Bengaluru': 'Bengaluru', 'BLR': 'Bengaluru', 'bengaluru': 'Bengaluru', 'Bangalore': 'Bengaluru',
    'Delhi NCR': 'Delhi NCR', 'Delhi': 'Delhi NCR', 'New Delhi': 'Delhi NCR', 'Gurgaon': 'Delhi NCR',
    'Hyderabad': 'Hyderabad', 'HYD': 'Hyderabad', 'Hyd': 'Hyderabad', 'hyderabad': 'Hyderabad',
    'Pune': 'Pune', 'PUN': 'Pune', 'pune': 'Pune',
    'Mumbai': 'Mumbai', 'MUM': 'Mumbai', 'Bombay': 'Mumbai',
    'Jaipur': 'Jaipur', 'JAI': 'Jaipur', 'jaipur': 'Jaipur'
}
riders['home_city_clean'] = riders['home_city'].map(city_map).fillna(riders['home_city'])
riders['partner_id_clean'] = riders['partner_id'].fillna('Independent / Retail')
riders['is_fleet'] = riders['partner_id'].notnull()

# Map station to city, zone, location_type
stn_map = stations.set_index('station_id')[['city', 'zone', 'location_type', 'host_type', 'slots_2w', 'slots_3w', 'inventory_target_2w']].to_dict('index')

# Map rider to partner_id, is_fleet
rider_partner_map = riders.set_index('rider_id')['partner_id_clean'].to_dict()
rider_fleet_map = riders.set_index('rider_id')['is_fleet'].to_dict()

# Map partner_id to partner_name
fleet_name_map = fleet_partners.set_index('partner_id')['partner_name'].to_dict()
fleet_name_map['Independent / Retail'] = 'Independent / Retail'

print("Loading swap_events.csv...")
swaps = pd.read_csv('swap_events.csv', usecols=['event_id', 'rider_id', 'station_id', 'event_ts', 'event_type', 'queue_wait_sec'])

swaps['is_direct_stockout'] = (swaps['event_type'] == 'failed_no_charged_battery').astype(int)
swaps['is_abandoned'] = (swaps['event_type'] == 'abandoned_queue').astype(int)
swaps['is_stockout_event'] = (swaps['event_type'].isin(['failed_no_charged_battery', 'abandoned_queue'])).astype(int)

# Extract datetime fields
event_dt = pd.to_datetime(swaps['event_ts'])
swaps['hour'] = event_dt.dt.hour
swaps['day_of_week'] = event_dt.dt.day_name()
swaps['date_str'] = event_dt.dt.strftime('%Y-%m-%d')

# Map metadata
swaps['city'] = swaps['station_id'].map(lambda x: stn_map[x]['city'] if x in stn_map else 'Unknown')
swaps['zone'] = swaps['station_id'].map(lambda x: stn_map[x]['zone'] if x in stn_map else 'Unknown')
swaps['location_type'] = swaps['station_id'].map(lambda x: stn_map[x]['location_type'] if x in stn_map else 'Unknown')
swaps['partner_id'] = swaps['rider_id'].map(rider_partner_map).fillna('Independent / Retail')
swaps['is_fleet'] = swaps['rider_id'].map(rider_fleet_map).fillna(False)
swaps['partner_name'] = swaps['partner_id'].map(fleet_name_map).fillna('Independent / Retail')

print(f"Data mapped in {time.time() - t0:.2f} seconds!")

# Write summary output
out = []
out.append("================================================================================")
out.append("MASTER STATISTICAL ANALYSIS REPORT — VOLTRELAY BATTERY SWAP ANALYTICS")
out.append("================================================================================\n")

# 1. OVERALL SWAP & STOCKOUT SUMMARY
total_swaps = len(swaps)
direct_so = swaps['is_direct_stockout'].sum()
abandoned_so = swaps['is_abandoned'].sum()
total_so = swaps['is_stockout_event'].sum()
completed_swaps = (swaps['event_type'] == 'swap_completed').sum()
avg_wait = swaps['queue_wait_sec'].mean()

out.append("--- 1. OVERALL SWAP METRICS ---")
out.append(f"Total Swap Transactions Logged: {total_swaps:,}")
out.append(f"Successfully Completed Swaps: {completed_swaps:,} ({completed_swaps/total_swaps*100:.2f}%)")
out.append(f"Direct Stockout Failures (no charged battery): {direct_so:,} ({direct_so/total_swaps*100:.2f}%)")
out.append(f"Abandoned Queue Events (due to stockout delay): {abandoned_so:,} ({abandoned_so/total_swaps*100:.2f}%)")
out.append(f"Total Stockout Impacted Swaps: {total_so:,} ({total_so/total_swaps*100:.2f}%)")
out.append(f"Overall Average Rider Queue Wait Time: {avg_wait:.1f} seconds ({avg_wait/60:.2f} minutes)\n")

# 2. STOCKOUT BY CITY
city_grp = swaps.groupby('city').agg(
    total_swaps=('event_id', 'count'),
    direct_stockouts=('is_direct_stockout', 'sum'),
    abandoned=('is_abandoned', 'sum'),
    total_stockouts=('is_stockout_event', 'sum'),
    avg_queue_wait_sec=('queue_wait_sec', 'mean')
).reset_index()
city_grp['stockout_rate_pct'] = (city_grp['total_stockouts'] / city_grp['total_swaps']) * 100
city_grp = city_grp.sort_values(by='stockout_rate_pct', ascending=False)

out.append("--- 2. STOCKOUT FREQUENCY BY CITY ---")
out.append(city_grp.to_string(index=False))
out.append("")

# 3. TOP 15 WORST STATIONS BY STOCKOUT RATE
stn_grp = swaps.groupby(['station_id', 'city', 'zone', 'location_type']).agg(
    total_swaps=('event_id', 'count'),
    total_stockouts=('is_stockout_event', 'sum'),
    direct_stockouts=('is_direct_stockout', 'sum'),
    avg_queue_wait_sec=('queue_wait_sec', 'mean')
).reset_index()
stn_grp['stockout_rate_pct'] = (stn_grp['total_stockouts'] / stn_grp['total_swaps']) * 100
top15 = stn_grp.sort_values(by='stockout_rate_pct', ascending=False).head(15)

out.append("--- 3. TOP 15 WORST STATIONS BY STOCKOUT RATE ---")
out.append(top15.to_string(index=False))
out.append("")

# 4. HOUR OF DAY & DAY OF WEEK PATTERNS
hour_grp = swaps.groupby('hour').agg(
    total_swaps=('event_id', 'count'),
    total_stockouts=('is_stockout_event', 'sum'),
    avg_queue_wait_sec=('queue_wait_sec', 'mean')
).reset_index()
hour_grp['stockout_rate_pct'] = (hour_grp['total_stockouts'] / hour_grp['total_swaps']) * 100

out.append("--- 4. STOCKOUT RATE BY HOUR OF DAY ---")
out.append(hour_grp.sort_values(by='hour').to_string(index=False))
out.append("")

# Heatmap table: Hour x Day of Week
heatmap_data = swaps.pivot_table(index='hour', columns='day_of_week', values='is_stockout_event', aggfunc='mean') * 100
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_data = heatmap_data[days_order]
out.append("--- 4B. STOCKOUT RATE HEATMAP (%) (HOUR x DAY OF WEEK) ---")
out.append(heatmap_data.round(2).to_string())
out.append("")

# 5. FLEET PARTNERS VS RETAIL RIDERS
fleet_grp = swaps.groupby(['is_fleet', 'partner_name']).agg(
    total_swaps=('event_id', 'count'),
    total_stockouts=('is_stockout_event', 'sum'),
    avg_queue_wait_sec=('queue_wait_sec', 'mean')
).reset_index()
fleet_grp['stockout_rate_pct'] = (fleet_grp['total_stockouts'] / fleet_grp['total_swaps']) * 100
fleet_grp = fleet_grp.sort_values(by='stockout_rate_pct', ascending=False)

out.append("--- 5. FLEET PARTNERS VS RETAIL STOCKOUT RATES ---")
out.append(fleet_grp.to_string(index=False))
out.append("")

# 6. EXTERNAL FACTORS & CITY DAILY CONTEXT CORRELATIONS
daily_swaps = swaps.groupby(['city', 'date_str']).agg(
    daily_swaps=('event_id', 'count'),
    daily_stockouts=('is_stockout_event', 'sum')
).reset_index()
daily_swaps['stockout_rate_pct'] = (daily_swaps['daily_stockouts'] / daily_swaps['daily_swaps']) * 100

merged_daily = daily_swaps.merge(city_context, left_on=['city', 'date_str'], right_on=['city', 'date'], how='inner')

out.append("--- 6. CITY DAILY CONTEXT CORRELATIONS ---")
out.append(f"Avg Stockout Rate on Heat Alert Days: {merged_daily[merged_daily['heat_alert']==True]['stockout_rate_pct'].mean():.2f}% vs Normal: {merged_daily[merged_daily['heat_alert']==False]['stockout_rate_pct'].mean():.2f}%")
out.append(f"Avg Stockout Rate on Flood Disruption Days: {merged_daily[merged_daily['flood_disruption']==True]['stockout_rate_pct'].mean():.2f}% vs Normal: {merged_daily[merged_daily['flood_disruption']==False]['stockout_rate_pct'].mean():.2f}%")
out.append(f"Avg Stockout Rate on E-commerce Sale Event Days: {merged_daily[merged_daily['ecommerce_sale_event']==True]['stockout_rate_pct'].mean():.2f}% vs Normal: {merged_daily[merged_daily['ecommerce_sale_event']==False]['stockout_rate_pct'].mean():.2f}%")
out.append(f"Avg Stockout Rate on Grid Outage Days (>0 hrs): {merged_daily[merged_daily['grid_outage_hours']>0]['stockout_rate_pct'].mean():.2f}% vs Grid Normal: {merged_daily[merged_daily['grid_outage_hours']==0]['stockout_rate_pct'].mean():.2f}%")
out.append(f"Correlation between Grid Outage Hours & Daily Stockout Rate: {merged_daily['grid_outage_hours'].corr(merged_daily['stockout_rate_pct']):.4f}")
out.append(f"Correlation between Max Temp (C) & Daily Stockout Rate: {merged_daily['max_temp_c'].corr(merged_daily['stockout_rate_pct']):.4f}")
out.append(f"Correlation between Rainfall (mm) & Daily Stockout Rate: {merged_daily['rainfall_mm'].corr(merged_daily['stockout_rate_pct']):.4f}\n")

# 7. CROSS-VALIDATION WITH SUPPORT TICKETS
stn_ticket_counts = support_tickets[support_tickets['station_id'].notnull()].groupby('station_id').size().reset_index(name='total_tickets')
stn_long_queue_tickets = support_tickets[support_tickets['category']=='long_queue'].groupby('station_id').size().reset_index(name='queue_tickets')

stn_analysis = stn_grp.merge(stn_ticket_counts, on='station_id', how='left').merge(stn_long_queue_tickets, on='station_id', how='left').fillna(0)

corr_tickets = stn_analysis['total_stockouts'].corr(stn_analysis['total_tickets'])
corr_queue_tickets = stn_analysis['total_stockouts'].corr(stn_analysis['queue_tickets'])

out.append("--- 7. SUPPORT TICKET CROSS-VALIDATION ---")
out.append(f"Total Support Tickets: {len(support_tickets):,}")
out.append(f"Correlation (Station Stockout Count vs Total Support Tickets): {corr_tickets:.4f}")
out.append(f"Correlation (Station Stockout Count vs 'Long Queue' Complaints): {corr_queue_tickets:.4f}")
out.append(f"Top 5 Stations with Most 'Long Queue' Tickets:")
top_queue_stns = stn_analysis.sort_values(by='queue_tickets', ascending=False)[['station_id', 'city', 'zone', 'total_stockouts', 'stockout_rate_pct', 'queue_tickets']].head(5)
out.append(top_queue_stns.to_string(index=False))
out.append("")

# 8. BATTERY HEALTH & AGE DEGRADATION ANALYSIS
batteries['commission_dt'] = pd.to_datetime(batteries['commission_date'])
batteries['age_months'] = (pd.to_datetime('2025-06-30') - batteries['commission_dt']).dt.days / 30.44
batteries['soh_degradation'] = batteries['initial_soh_pct'] - batteries['current_soh_pct']

out.append("--- 8. BATTERY MASTER & DEGRADATION ANALYSIS ---")
out.append(f"Total Battery Units: {len(batteries):,}")
out.append(f"Active Batteries: {(batteries['retired_date'].isnull()).sum():,}")
out.append(f"Retired Batteries (end_of_life): {(batteries['retired_date'].notnull()).sum():,}")
out.append(f"Mean Initial SOH (%): {batteries['initial_soh_pct'].mean():.2f}%")
out.append(f"Mean Current SOH (%): {batteries['current_soh_pct'].mean():.2f}%")
out.append(f"Mean SOH Degradation: {batteries['soh_degradation'].mean():.2f}%")
out.append(f"Correlation (Battery Age in Months vs SOH Degradation): {batteries['age_months'].corr(batteries['soh_degradation']):.4f}")
supplier_soh = batteries.groupby('supplier').agg(
    battery_count=('battery_id', 'count'),
    mean_degradation=('soh_degradation', 'mean'),
    retired_pct=('retired_date', lambda x: (x.notnull().sum()/len(x))*100)
).reset_index()
out.append("\nDegradation & Retirement by Battery Supplier:")
out.append(supplier_soh.to_string(index=False))
out.append("")

# Save to file
report_text = "\n".join(out)
with open('analysis_summary.txt', 'w') as f:
    f.write(report_text)

print("Analysis executed successfully! Results saved to analysis_summary.txt.")
