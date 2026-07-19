-- fct_matches.sql
-- Final fact table for matches — ready for dashboards

with matches as (
    select * from {{ ref('stg_matches') }}
),

teams_home as (
    select team_id, team_name, tla, crest_url
    from {{ ref('stg_teams') }}
),

teams_away as (
    select team_id, team_name, tla, crest_url
    from {{ ref('stg_teams') }}
)

select
    m.match_id,
    m.competition_code,
    m.competition_name,
    m.season_id,
    m.match_date,
    m.stage,
    m.group_name,
    m.matchday,
    m.status,

    -- Home team
    m.home_team_id,
    m.home_team_name,
    th.tla                  as home_team_tla,
    th.crest_url            as home_team_crest,

    -- Away team
    m.away_team_id,
    m.away_team_name,
    ta.tla                  as away_team_tla,
    ta.crest_url            as away_team_crest,

    -- Score
    m.home_score,
    m.away_score,
    m.total_goals,
    m.winner,
    m.winner_name,
    m.is_finished,

    m.extracted_at

from matches m
left join teams_home th on m.home_team_id = th.team_id
left join teams_away ta on m.away_team_id = ta.team_id
