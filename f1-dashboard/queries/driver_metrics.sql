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
  -- Driver Multi-Select Logic
  (forename || ' ' || surname) in ${inputs.driver.value}
  or (
    'All' in ${inputs.driver.value}
    and (
      select count(*) 
      from (select distinct forename || ' ' || surname as d_name from driver_season_summary)
      where d_name in ${inputs.driver.value}
    ) = 0
  )
)
and (
  cast(season as varchar) in ${inputs.season.value}
  or (
    'All' in ${inputs.season.value}
    and (
      select count(*) 
      from (select distinct cast(season as varchar) as s_name from driver_season_summary)
      where s_name in ${inputs.season.value}
    ) = 0
  )
)
order by season desc, championship_position asc