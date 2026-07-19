-- mart_world_cup_summary.sql
-- Aggregated performance per team in the World Cup

with results as (
    select * from {{ ref('int_team_match_results') }}
    where competition_code = 'WC'
),

teams as (
    select team_id, tla, crest_url
    from {{ ref('stg_teams') }}
),

aggregated as (
    select
        team_id,
        team_name,
        count(*)                                        as matches_played,
        count(*) filter (where result = 'WIN')          as wins,
        count(*) filter (where result = 'DRAW')         as draws,
        count(*) filter (where result = 'LOSS')         as losses,
        sum(points_earned)                              as total_points,
        sum(goals_scored)                               as goals_scored,
        sum(goals_conceded)                             as goals_conceded,
        sum(goals_scored) - sum(goals_conceded)         as goal_difference,
        round(avg(goals_scored), 2)                     as avg_goals_scored,
        round(avg(goals_conceded), 2)                   as avg_goals_conceded,
        max(match_date)                                 as last_match_date
    from results
    group by team_id, team_name
)

select
    a.*,
    t.tla,
    t.crest_url
from aggregated a
left join teams t on a.team_id = t.team_id
order by total_points desc, goal_difference desc
