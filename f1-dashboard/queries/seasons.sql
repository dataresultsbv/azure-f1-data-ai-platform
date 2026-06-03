select 'All' as season_year
union all
(
  select cast(season as varchar) as season_year
  from driver_season_summary 
  group by season 
  order by season desc
)