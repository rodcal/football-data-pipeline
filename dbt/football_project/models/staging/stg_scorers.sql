-- stg_scorers.sql
-- Cleans and types raw scorers data from the API

with source as (
    select * from {{ source('raw', 'scorers') }}
),

staged as (
    select
        id                  as scorer_id,
        competition_code,
        season_id,
        player_id,
        player_name,
        player_nationality,
        team_id,
        team_name,
        coalesce(goals, 0)      as goals,
        coalesce(assists, 0)    as assists,
        coalesce(penalties, 0)  as penalties,
        extracted_at
    from source
)

select * from staged
