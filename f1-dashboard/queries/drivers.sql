select 'All' as driver_name_select
union all
(
  select forename || ' ' || surname as driver_name_select
  from driver_season_summary 
  group by driver_name_select
  order by driver_name_select asc
)