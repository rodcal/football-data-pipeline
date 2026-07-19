-- stg_matches.sql
-- Cleans and types raw match data from the API

with source as (
    select * from {{ source('raw', 'matches') }}
),

staged as (
    select
        id                                          as match_id,
        competition_code,
        competition_name,
        season_id,
        season_start_date,
        season_end_date,
        utc_date::timestamp                         as match_date,
        status,
        matchday,
        stage,
        group_name,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        coalesce(home_score, 0)                     as home_score,
        coalesce(away_score, 0)                     as away_score,
        winner,

        -- Derived fields
        case
            when status = 'FINISHED' then true
            else false
        end                                         as is_finished,

        case
            when winner = 'HOME_TEAM'  then home_team_name
            when winner = 'AWAY_TEAM'  then away_team_name
            when winner = 'DRAW'       then 'DRAW'
            else null
        end                                         as winner_name,

        coalesce(home_score, 0)
            + coalesce(away_score, 0)               as total_goals,

        extracted_at

    from source
)

select * from staged
