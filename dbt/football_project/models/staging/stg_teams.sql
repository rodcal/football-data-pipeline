-- stg_teams.sql
-- Cleans and types raw team data from the API

with source as (
    select * from {{ source('raw', 'teams') }}
),

staged as (
    select
        id              as team_id,
        competition_code,
        name            as team_name,
        short_name,
        tla,
        crest_url,
        founded,
        club_colors,
        venue,
        extracted_at
    from source
)

select * from staged
