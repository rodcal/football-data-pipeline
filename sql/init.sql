-- =============================================================================
-- init.sql
-- Runs automatically when the PostgreSQL container starts for the first time.
-- Creates the raw schema and all ingestion tables.
-- =============================================================================
 
-- Schema for raw data (direct from API, no transformation)
CREATE SCHEMA IF NOT EXISTS raw;
 
-- ---------------------------------------------------------------------------
-- Matches
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.matches (
    id                  INTEGER PRIMARY KEY,
    competition_code    VARCHAR(10),
    competition_name    VARCHAR(100),
    season_id           INTEGER,
    season_start_date   DATE,
    season_end_date     DATE,
    utc_date            TIMESTAMP,
    status              VARCHAR(30),
    matchday            INTEGER,
    stage               VARCHAR(50),
    group_name          VARCHAR(50),
    home_team_id        INTEGER,
    home_team_name      VARCHAR(100),
    away_team_id        INTEGER,
    away_team_name      VARCHAR(100),
    home_score          INTEGER,
    away_score          INTEGER,
    winner              VARCHAR(20),
    raw_payload         JSONB,          -- full original JSON for reference
    extracted_at        TIMESTAMP DEFAULT NOW()
);
 
-- ---------------------------------------------------------------------------
-- Teams
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.teams (
    id                  INTEGER PRIMARY KEY,
    competition_code    VARCHAR(10),
    name                VARCHAR(100),
    short_name          VARCHAR(50),
    tla                 VARCHAR(10),
    crest_url           TEXT,
    address             TEXT,
    website             TEXT,
    founded             INTEGER,
    club_colors         VARCHAR(100),
    venue               VARCHAR(100),
    raw_payload         JSONB,
    extracted_at        TIMESTAMP DEFAULT NOW()
);
 
-- ---------------------------------------------------------------------------
-- Standings
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.standings (
    id                  SERIAL PRIMARY KEY,
    competition_code    VARCHAR(10),
    season_id           INTEGER,
    stage               VARCHAR(50),
    group_name          VARCHAR(50),
    position            INTEGER,
    team_id             INTEGER,
    team_name           VARCHAR(100),
    played_games        INTEGER,
    won                 INTEGER,
    draw                INTEGER,
    lost                INTEGER,
    points              INTEGER,
    goals_for           INTEGER,
    goals_against       INTEGER,
    goal_difference     INTEGER,
    raw_payload         JSONB,
    extracted_at        TIMESTAMP DEFAULT NOW()
);
 
-- ---------------------------------------------------------------------------
-- Scorers
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.scorers (
    id                  SERIAL PRIMARY KEY,
    competition_code    VARCHAR(10),
    season_id           INTEGER,
    player_id           INTEGER,
    player_name         VARCHAR(100),
    player_nationality  VARCHAR(100),
    team_id             INTEGER,
    team_name           VARCHAR(100),
    goals               INTEGER,
    assists             INTEGER,
    penalties           INTEGER,
    raw_payload         JSONB,
    extracted_at        TIMESTAMP DEFAULT NOW()
);
 
-- ---------------------------------------------------------------------------
-- Extraction log (tracks every run)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.extraction_log (
    id                  SERIAL PRIMARY KEY,
    competition_code    VARCHAR(10),
    endpoint            VARCHAR(50),
    records_loaded      INTEGER,
    status              VARCHAR(20),    -- 'success' or 'error'
    error_message       TEXT,
    extracted_at        TIMESTAMP DEFAULT NOW()
);