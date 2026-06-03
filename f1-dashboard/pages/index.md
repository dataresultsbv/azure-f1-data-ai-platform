---
title: F1 Analytics Portal
queries:
  - drivers: drivers.sql
  - seasons: seasons.sql
  - driver_metrics: driver_metrics.sql
---

# 🏎️ Formula 1 Driver Performance Dashboard

An interactive, metadata-driven visualization layer compiled directly from the Gold Medallion platform layer.

<Grid cols="2">
  <Dropdown
    data={drivers}
    name="driver"
    value="driver_name_select"
    label="driver_name_select"
    title="Select Drivers"
    defaultValue="All"
    multiple=true
  />
  <Dropdown
    data={seasons}
    name="season"
    value="season_year"
    label="season_year"
    title="Select Seasons"
    defaultValue="All"
    multiple=true
  />
</Grid>

Driver Standings Overview
<DataTable data={driver_metrics} search="true" pagination="true" rows="10">
  <Column id="season" title="Season" align="center"/>
  <Column id="driver_name" title="Driver"/>
  <Column id="nationality" title="Nationality"/>
  <Column id="championship_position" title="Rank" align="center"/>
  <Column id="total_points" title="Points"/>
  <Column id="wins" title="Wins" align="center"/>
  <Column id="podiums" title="Podiums" align="center"/>
</DataTable>

---

## 📊 Performance Analytics & Trends

<Grid cols="2">
  <BarChart
    data={driver_metrics}
    title="Championship Points Over Time"
    x="season"
    y="total_points"
    series="driver_name"
    xType="category"
  />

  <LineChart
    data={driver_metrics}
    title="Podium Finishes Trend"
    x="season"
    y="podiums"
    series="driver_name"
    xType="category"
  />
</Grid>

## 👑 Global Driver Longevity & Points Dominance

Tracks every driver's accumulated point profile across all logged seasons.

<ScatterPlot
  data={driver_metrics}
  x="season"
  y="total_points"
  series="driver_name"
  tooltipTitle="driver_name"
  xType="category"
/>

## 🏎️ Advanced Driver Performance Metrics

<Grid cols="2">
  <BarChart data="{driver_metrics}" series="driver_name" title="Total Fastest Laps by Season" x="season" xType="category" y="fastest_laps"/>

  <BarChart data="{driver_metrics}" series="driver_name" subtitle="Positive means gained positions from starting grid" title="Net Positions Gained/Lost in Races" x="season" xType="category" y="positions_gained"/>
</Grid>

## ⏱️ Qualifying Efficiency: Average Grid Position Trajectory

A lower number means better qualifying performance (e.g., closer to Pole Position).

<LineChart data="{driver_metrics}" series="driver_name" x="season" xType="category" y="avg_grid_position" yFmt="num"/>

## 🔄 Overtaking Leaderboard: Net Positions Gained/Lost

This ranking showcases race craft by tracking the net difference between a driver's starting grid slot and their final finishing position. Note that this visual only provides correct insights when filtering down to a single season. Higher positive values indicate exceptional overtaking and race-pace recovery. 

<BarChart 
  data={driver_metrics} 
  x="driver_name" 
  y="positions_gained" 
  title="Net Positions Gained/Lost Summary"
  subtitle="Total positions gained over the selected seasons (Positive = Gained, Negative = Lost)"
  swapXY=true
  sort="positions_gained"
  type="stacked"
/>