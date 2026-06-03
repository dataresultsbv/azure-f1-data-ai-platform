---
title: F1 Analytics Portal
---

# 🏎️ Formula 1 Driver Performance Dashboard

An interactive, metadata-driven visualization layer compiled directly from the Gold Medallion platform layer.

```sql drivers
select 'All' as driver_name_select
union all
(
  select forename || ' ' || surname as driver_name_select
  from driver_season_summary 
  group by driver_name_select
  order by driver_name_select asc
)
```

```sql seasons
select 'All' as season_year
union all
(
  select cast(season as varchar) as season_year
  from driver_season_summary 
  group by season 
  order by season desc
)
```

```sql driver_metrics
select 
    season,
    forename || ' ' || surname as driver_name,
    nationality,
    championship_position,
    total_points,
    wins,
    podiums,
    fastest_laps,
    dnfs,
    avg_grid_position,
    positions_gained
from driver_season_summary
where (
  '${inputs.driver.value}' = 'All' 
  or '${inputs.driver.value}' = 'undefined' 
  or (forename || ' ' || surname) = '${inputs.driver.value}'
)
and (
  '${inputs.season.value}' = 'All' 
  or '${inputs.season.value}' = 'undefined' 
  or cast(season as varchar) = '${inputs.season.value}'
)
order by season desc, championship_position asc
```

<Grid cols="2">
  <Dropdown
    data={drivers}
    name="driver"
    value="driver_name_select"
    label="driver_name_select"
    title="Select Driver"
    defaultValue="All"
  />
  <Dropdown
    data={seasons}
    name="season"
    value="season_year"
    label="season_year"
    title="Select Season"
    defaultValue="All"
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

## 🏎️ Advanced Driver Performance Metrics

<Grid cols="2">
  <BarChart data="{driver_metrics}" series="driver_name" title="Total Fastest Laps by Season" x="season" xType="category" y="fastest_laps"/>

  <BarChart data="{driver_metrics}" series="driver_name" subtitle="Positive means gained positions from starting grid" title="Net Positions Gained/Lost in Races" x="season" xType="category" y="positions_gained"/>
</Grid>

## ⏱️ Qualifying Efficiency: Average Grid Position Trajectory

A lower number means better qualifying performance (e.g., closer to Pole Position).

<LineChart data="{driver_metrics}" series="driver_name" x="season" xType="category" y="avg_grid_position" yFmt="num"/>

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