-- stg_standings.sql
-- Cleans and types raw standings data from the API

with source as (
    select * from {{ source('raw', 'standings') }}
),

staged as (
    select
        id              as standing_id,
        competition_code,
        season_id,
        stage,
        group_name,
        position,
        team_id,
        team_name,
        played_games,
        won,
        draw,
        lost,
        points,
        goals_for,
        goals_against,
        goal_difference,
        extracted_at
    from source
)

select * from staged
