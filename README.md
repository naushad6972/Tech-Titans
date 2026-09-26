# 🚀 Tech Titans — Fleet & Battery Analytics

## 📌 Project Overview

**Tech Titans** is a data analysis project focused on understanding fleet operations, battery availability, swapping activity, rider demand, and operational issues.

The project analyzes multiple datasets to identify patterns such as:

* 🔋 Battery stockouts and availability
* 🛵 Battery swap activity
* 🏙️ City-wise operational performance
* ⏰ Peak operating hours
* 🌡️ Impact of heat and weather conditions
* 🚚 Fleet partner performance
* 📉 Battery degradation and supplier patterns
* 🎫 Support tickets and their relationship with stockouts

The analysis produces summaries and visualizations that can help identify operational bottlenecks and improve fleet and battery management.

---

## 📂 Repository Structure

```text
Tech-Titans/
│
├── batteries.csv
├── city_daily_context.csv
├── fleet_partners.csv
├── riders.csv
├── station_hourly_status.csv
├── support_tickets.csv
├── swap_events.csv
├── stations.csv
│
├── analysis_summary.txt
│
├── fast_analysis.py
├── generate_charts.py
├── run_full_analysis.py
├── task1_full_summary.py
├── task1_inspection.py
│
├── charts/
│   ├── chart1_stockouts_by_city.png
│   ├── chart2_peak_hours_heatmap.png
│   ├── chart3_heat_alert_impact.png
│   ├── chart4_fleet_segment_impact.png
│   ├── chart5_battery_degradation_supplier.png
│   └── chart6_tickets_vs_stockouts.png
│
└── 🚀 Executive Summary.docx
```

---

## 📊 Datasets

The project uses several datasets representing different parts of the fleet ecosystem.

| Dataset                     | Description                                         |
| --------------------------- | --------------------------------------------------- |
| `batteries.csv`             | Battery information and battery performance data    |
| `city_daily_context.csv`    | Daily city-level environmental/context information  |
| `fleet_partners.csv`        | Fleet partner information                           |
| `riders.csv`                | Rider-related information                           |
| `station_hourly_status.csv` | Hourly station and battery availability information |
| `support_tickets.csv`       | Customer/support ticket information                 |
| `swap_events.csv`           | Battery swapping event records                      |
| `stations.csv`              | Battery station information                         |

> **Note:** Some datasets are very large and are tracked using Git LFS.

---

## 📈 Analysis & Visualizations

The project generates several charts to explore important operational relationships.

### 1. Stockouts by City

Shows battery stockout patterns across different cities and helps identify locations experiencing availability issues.

### 2. Peak Hours Heatmap

Analyzes station activity by hour to identify periods of high demand.

### 3. Heat Alert Impact

Examines how heat/weather conditions relate to operational performance.

### 4. Fleet Segment Impact

Compares operational performance across different fleet partner segments.

### 5. Battery Degradation by Supplier

Analyzes battery degradation patterns across suppliers.

### 6. Support Tickets vs Stockouts

Explores the relationship between battery availability problems and support requests.

All generated visualizations are available in the `charts/` directory.

---

## 🛠️ Technologies Used

* **Python**
* **Pandas** — data processing and analysis
* **Matplotlib** — data visualization
* **Seaborn** — statistical visualization
* **CSV** — data storage
* **Git & GitHub**
* **Git LFS** — large dataset management

---

## ▶️ How to Run

### 1. Clone the repository

```bash
git clone https://github.com/naushad6972/Tech-Titans.git
cd Tech-Titans
```

### 2. Install dependencies

```bash
pip install pandas matplotlib seaborn
```

### 3. Run the analysis

For the complete analysis:

```bash
python run_full_analysis.py
```

For faster analysis:

```bash
python fast_analysis.py
```

### 4. Generate charts

```bash
python generate_charts.py
```

Additional analysis scripts can be executed individually:

```bash
python task1_inspection.py
python task1_full_summary.py
```

---

## 📋 Outputs

The project produces:

* Analytical summaries
* City-level insights
* Battery and station performance analysis
* Peak-hour analysis
* Environmental impact analysis
* Fleet partner comparisons
* Battery degradation analysis
* Support-ticket analysis
* Data visualizations

The main textual results can be found in:

```text
analysis_summary.txt
```

Visual outputs are stored in:

```text
charts/
```

---

## 🎯 Project Goals

The primary goals of this project are to:

1. Understand battery availability across stations and cities.
2. Identify periods of high operational demand.
3. Analyze factors associated with battery stockouts.
4. Investigate battery degradation patterns.
5. Understand fleet partner performance.
6. Examine environmental factors affecting operations.
7. Analyze support issues related to operational availability.
8. Convert raw operational data into actionable insights.

---

## 👥 Team

**Team:** Tech Titans

This project was developed as part of a data analysis / hackathon project.

---

## 📄 License

This project is intended for educational, analytical, and hackathon purposes.
