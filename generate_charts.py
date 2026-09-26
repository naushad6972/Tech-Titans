import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs('charts', exist_ok=True)

# Set global matplotlib parameters for clean aesthetic design
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['figure.titlesize'] = 16

# Color Palette
PRIMARY_BLUE = '#1E3A8A'
TEAL_ACCENT = '#0D9488'
CORAL_WARNING = '#E11D48'
ORANGE_ALERT = '#F97316'
GRAY_TEXT = '#374151'
BG_LIGHT = '#F8FAFC'

# Load Cleaned Data
stations = pd.read_csv('stations.csv')
riders = pd.read_csv('riders.csv')
fleet_partners = pd.read_csv('fleet_partners.csv')
city_context = pd.read_csv('city_daily_context.csv')
support_tickets = pd.read_csv('support_tickets.csv')
batteries = pd.read_csv('batteries.csv')
swaps = pd.read_csv('swap_events.csv', usecols=['event_id', 'rider_id', 'station_id', 'event_ts', 'event_type', 'queue_wait_sec'])

# Mapping
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

stn_map = stations.set_index('station_id')['city'].to_dict()
rider_partner_map = riders.set_index('rider_id')['partner_id_clean'].to_dict()
fleet_name_map = fleet_partners.set_index('partner_id')['partner_name'].to_dict()
fleet_name_map['Independent / Retail'] = 'Independent / Retail'

swaps['is_stockout_event'] = (swaps['event_type'].isin(['failed_no_charged_battery', 'abandoned_queue'])).astype(int)
swaps['city'] = swaps['station_id'].map(stn_map).fillna('Unknown')
swaps['partner_id'] = swaps['rider_id'].map(rider_partner_map).fillna('Independent / Retail')
swaps['partner_name'] = swaps['partner_id'].map(fleet_name_map).fillna('Independent / Retail')

event_dt = pd.to_datetime(swaps['event_ts'])
swaps['hour'] = event_dt.dt.hour
swaps['day_of_week'] = event_dt.dt.day_name()
swaps['date_str'] = event_dt.dt.strftime('%Y-%m-%d')

print("Generating Charts...")

# ----------------------------------------------------
# CHART 1: Stockout Rate by City
# ----------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG_LIGHT)
city_summary = swaps.groupby('city')['is_stockout_event'].agg(['count', 'mean']).reset_index()
city_summary['stockout_pct'] = city_summary['mean'] * 100
city_summary = city_summary.sort_values(by='stockout_pct', ascending=False)

bars = ax.bar(city_summary['city'], city_summary['stockout_pct'], color=[CORAL_WARNING if x > 6.0 else PRIMARY_BLUE for x in city_summary['stockout_pct']], width=0.55, edgecolor='none', zorder=3)
ax.set_facecolor(BG_LIGHT)
ax.axhline(5.23, color=GRAY_TEXT, linestyle='--', linewidth=1.2, label='Network Average (5.23%)', zorder=4)

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.15, f"{yval:.2f}%", ha='center', va='bottom', fontweight='bold', color=GRAY_TEXT)

ax.set_title('Stockout Frequency Rate by City (% of Total Swap Attempts)', pad=15)
ax.set_ylabel('Stockout Rate (%)')
ax.set_ylim(0, 10)
ax.legend(frameon=True, facecolor='white')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('charts/chart1_stockouts_by_city.png', dpi=300)
plt.close()
print("Chart 1 generated.")

# ----------------------------------------------------
# CHART 2: Hour x Day Stockout Heatmap
# ----------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6.5), facecolor=BG_LIGHT)
pivot = swaps.pivot_table(index='hour', columns='day_of_week', values='is_stockout_event', aggfunc='mean') * 100
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
pivot = pivot[days_order]

sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd", cbar_kws={'label': 'Stockout Rate (%)'}, ax=ax, linewidths=0.5)
ax.set_title('Stockout Rate Heatmap: Hour of Day vs Day of Week', pad=15)
ax.set_xlabel('Day of Week')
ax.set_ylabel('Hour of Day (24-Hr Format)')
plt.tight_layout()
plt.savefig('charts/chart2_peak_hours_heatmap.png', dpi=300)
plt.close()
print("Chart 2 generated.")

# ----------------------------------------------------
# CHART 3: Heat Alert vs Normal Days Stockout Rate
# ----------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5.5), facecolor=BG_LIGHT)
daily_swaps = swaps.groupby(['city', 'date_str']).agg(
    total=('event_id', 'count'),
    stockouts=('is_stockout_event', 'sum')
).reset_index()
daily_swaps['stockout_pct'] = (daily_swaps['stockouts'] / daily_swaps['total']) * 100

merged_daily = daily_swaps.merge(city_context, left_on=['city', 'date_str'], right_on=['city', 'date'], how='inner')
heat_summary = merged_daily.groupby('heat_alert')['stockout_pct'].mean().reset_index()
heat_summary['label'] = heat_summary['heat_alert'].map({False: 'Normal Temp Days\n(<40°C)', True: 'Heat Alert Days\n(≥40°C)'})

bars = ax.bar(heat_summary['label'], heat_summary['stockout_pct'], color=[PRIMARY_BLUE, CORAL_WARNING], width=0.45, zorder=3)
ax.set_facecolor(BG_LIGHT)

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.3, f"{yval:.2f}%", ha='center', va='bottom', fontweight='bold', size=13, color=GRAY_TEXT)

ax.set_title('Impact of Extreme Heat Alerts (≥40°C) on Stockout Rate', pad=15)
ax.set_ylabel('Average Daily Stockout Rate (%)')
ax.set_ylim(0, 18)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('charts/chart3_heat_alert_impact.png', dpi=300)
plt.close()
print("Chart 3 generated.")

# ----------------------------------------------------
# CHART 4: Fleet Partner Stockout Rates
# ----------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG_LIGHT)
fleet_summary = swaps.groupby('partner_name')['is_stockout_event'].agg(['count', 'mean']).reset_index()
fleet_summary['stockout_pct'] = fleet_summary['mean'] * 100
fleet_summary = fleet_summary.sort_values(by='stockout_pct', ascending=True)

colors = [CORAL_WARNING if 'Haul' in name or 'Tuk' in name else PRIMARY_BLUE for name in fleet_summary['partner_name']]
bars = ax.barh(fleet_summary['partner_name'], fleet_summary['stockout_pct'], color=colors, height=0.6, zorder=3)
ax.set_facecolor(BG_LIGHT)
ax.axvline(5.23, color=GRAY_TEXT, linestyle='--', linewidth=1.2, label='Network Average (5.23%)', zorder=4)

for bar in bars:
    xval = bar.get_width()
    ax.text(xval + 0.15, bar.get_y() + bar.get_height()/2.0, f"{xval:.2f}%", ha='left', va='center', fontweight='bold', color=GRAY_TEXT)

ax.set_title('Stockout Rate by Rider Fleet Partner (Cargo 3W vs Delivery 2W vs Retail)', pad=15)
ax.set_xlabel('Stockout Rate (%)')
ax.set_xlim(0, 11)
ax.legend(frameon=True, facecolor='white', loc='lower right')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('charts/chart4_fleet_segment_impact.png', dpi=300)
plt.close()
print("Chart 4 generated.")

# ----------------------------------------------------
# CHART 5: Battery Degradation & Retirement by Supplier
# ----------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=BG_LIGHT)
batteries['commission_dt'] = pd.to_datetime(batteries['commission_date'])
batteries['soh_degradation'] = batteries['initial_soh_pct'] - batteries['current_soh_pct']

supplier_grp = batteries.groupby('supplier')['soh_degradation'].mean().reset_index()

bars = ax.bar(supplier_grp['supplier'], supplier_grp['soh_degradation'], color=[PRIMARY_BLUE, PRIMARY_BLUE, CORAL_WARNING], width=0.45, zorder=3)
ax.set_facecolor(BG_LIGHT)

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f"{yval:.2f}% SOH Loss", ha='center', va='bottom', fontweight='bold', color=GRAY_TEXT)

ax.set_title('Average Battery Capacity Degradation (SOH Loss %) by Supplier', pad=15)
ax.set_ylabel('Mean SOH Degradation (%)')
ax.set_ylim(0, 42)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('charts/chart5_battery_degradation_supplier.png', dpi=300)
plt.close()
print("Chart 5 generated.")

# ----------------------------------------------------
# CHART 6: Support Tickets vs Stockouts Scatter Plot
# ----------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 6), facecolor=BG_LIGHT)
stn_so = swaps.groupby('station_id')['is_stockout_event'].sum().reset_index(name='stockout_count')
stn_tk = support_tickets[support_tickets['station_id'].notnull()].groupby('station_id').size().reset_index(name='ticket_count')
merged_stn = stn_so.merge(stn_tk, on='station_id', how='inner')

sns.regplot(data=merged_stn, x='stockout_count', y='ticket_count', ax=ax, color=PRIMARY_BLUE, scatter_kws={'alpha':0.6, 's':40}, line_kws={'color':CORAL_WARNING, 'linewidth':2})
ax.set_facecolor(BG_LIGHT)
ax.set_title('Cross-Validation: Station Stockout Count vs Customer Support Tickets (r = 0.976)', pad=15)
ax.set_xlabel('Total Station Stockout Incidents')
ax.set_ylabel('Total Support Complaints Filed')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('charts/chart6_tickets_vs_stockouts.png', dpi=300)
plt.close()
print("Chart 6 generated successfully!")
