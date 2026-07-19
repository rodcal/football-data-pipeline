-- int_team_match_results.sql
-- Unpivots matches so each row represents one team's perspective in a match

with matches as (
    select * from {{ ref('stg_matches') }}
    where is_finished = true
),

home_results as (
    select
        match_id,
        competition_code,
        match_date,
        stage,
        group_name,
        matchday,
        home_team_id                                as team_id,
        home_team_name                              as team_name,
        away_team_id                                as opponent_id,
        away_team_name                              as opponent_name,
        home_score                                  as goals_scored,
        away_score                                  as goals_conceded,
        'HOME'                                      as home_away,
        case
            when winner = 'HOME_TEAM' then 'WIN'
            when winner = 'AWAY_TEAM' then 'LOSS'
            when winner = 'DRAW'      then 'DRAW'
        end                                         as result,
        case
            when winner = 'HOME_TEAM' then 3
            when winner = 'DRAW'      then 1
            else 0
        end                                         as points_earned
    from matches
),

away_results as (
    select
        match_id,
        competition_code,
        match_date,
        stage,
        group_name,
        matchday,
        away_team_id                                as team_id,
        away_team_name                              as team_name,
        home_team_id                                as opponent_id,
        home_team_name                              as opponent_name,
        away_score                                  as goals_scored,
        home_score                                  as goals_conceded,
        'AWAY'                                      as home_away,
        case
            when winner = 'AWAY_TEAM' then 'WIN'
            when winner = 'HOME_TEAM' then 'LOSS'
            when winner = 'DRAW'      then 'DRAW'
        end                                         as result,
        case
            when winner = 'AWAY_TEAM' then 3
            when winner = 'DRAW'      then 1
            else 0
        end                                         as points_earned
    from matches
),

unioned as (
    select * from home_results
    union all
    select * from away_results
)

select * from unioned
