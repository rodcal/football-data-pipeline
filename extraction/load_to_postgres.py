"""
load_to_postgres.py
-------------------
Loads raw JSON files (saved by extract_api.py) into PostgreSQL raw schema.

Usage:
    python extraction/load_to_postgres.py
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", 5432),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

RAW_DATA_DIR = Path("data/raw")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------


def get_connection():
    """Returns a psycopg2 connection to PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Connected to PostgreSQL successfully.")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise


def log_extraction(
    conn,
    competition_code: str,
    endpoint: str,
    records: int,
    status: str,
    error: str = None,
):
    """Inserts a record into raw.extraction_log."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw.extraction_log
                (competition_code, endpoint, records_loaded, status, error_message)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (competition_code, endpoint, records, status, error),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_matches(conn, data: dict, competition_code: str) -> int:
    """Loads matches into raw.matches."""
    matches = data.get("matches", [])
    if not matches:
        logger.warning(f"No matches found for {competition_code}.")
        return 0

    rows = []
    for m in matches:
        rows.append(
            (
                m["id"],
                competition_code,
                m.get("competition", {}).get("name"),
                m.get("season", {}).get("id"),
                m.get("season", {}).get("startDate"),
                m.get("season", {}).get("endDate"),
                m.get("utcDate"),
                m.get("status"),
                m.get("matchday"),
                m.get("stage"),
                m.get("group"),
                m.get("homeTeam", {}).get("id"),
                m.get("homeTeam", {}).get("name"),
                m.get("awayTeam", {}).get("id"),
                m.get("awayTeam", {}).get("name"),
                m.get("score", {}).get("fullTime", {}).get("home"),
                m.get("score", {}).get("fullTime", {}).get("away"),
                m.get("score", {}).get("winner"),
                json.dumps(m),
            )
        )

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO raw.matches (
                id, competition_code, competition_name,
                season_id, season_start_date, season_end_date,
                utc_date, status, matchday, stage, group_name,
                home_team_id, home_team_name,
                away_team_id, away_team_name,
                home_score, away_score, winner,
                raw_payload
            ) VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                status       = EXCLUDED.status,
                home_score   = EXCLUDED.home_score,
                away_score   = EXCLUDED.away_score,
                winner       = EXCLUDED.winner,
                raw_payload  = EXCLUDED.raw_payload,
                extracted_at = NOW()
        """,
            rows,
        )
    conn.commit()
    logger.info(f"Loaded {len(rows)} matches for {competition_code}.")
    return len(rows)


def load_teams(conn, data: dict, competition_code: str) -> int:
    """Loads teams into raw.teams."""
    teams = data.get("teams", [])
    if not teams:
        logger.warning(f"No teams found for {competition_code}.")
        return 0

    rows = []
    for t in teams:
        rows.append(
            (
                t["id"],
                competition_code,
                t.get("name"),
                t.get("shortName"),
                t.get("tla"),
                t.get("crest"),
                t.get("address"),
                t.get("website"),
                t.get("founded"),
                t.get("clubColors"),
                t.get("venue"),
                json.dumps(t),
            )
        )

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO raw.teams (
                id, competition_code, name, short_name, tla,
                crest_url, address, website, founded,
                club_colors, venue, raw_payload
            ) VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                name         = EXCLUDED.name,
                raw_payload  = EXCLUDED.raw_payload,
                extracted_at = NOW()
        """,
            rows,
        )
    conn.commit()
    logger.info(f"Loaded {len(rows)} teams for {competition_code}.")
    return len(rows)


def load_standings(conn, data: dict, competition_code: str) -> int:
    """Loads standings into raw.standings."""
    standings_groups = data.get("standings", [])
    if not standings_groups:
        logger.warning(f"No standings found for {competition_code}.")
        return 0

    season_id = data.get("season", {}).get("id")
    rows = []

    for group in standings_groups:
        stage = group.get("stage")
        group_name = group.get("group")
        for entry in group.get("table", []):
            rows.append(
                (
                    competition_code,
                    season_id,
                    stage,
                    group_name,
                    entry.get("position"),
                    entry.get("team", {}).get("id"),
                    entry.get("team", {}).get("name"),
                    entry.get("playedGames"),
                    entry.get("won"),
                    entry.get("draw"),
                    entry.get("lost"),
                    entry.get("points"),
                    entry.get("goalsFor"),
                    entry.get("goalsAgainst"),
                    entry.get("goalDifference"),
                    json.dumps(entry),
                )
            )

    with conn.cursor() as cur:
        # Truncate before reload to avoid duplicates (standings change every round)
        cur.execute(
            "DELETE FROM raw.standings WHERE competition_code = %s AND season_id = %s",
            (competition_code, season_id),
        )
        execute_values(
            cur,
            """
            INSERT INTO raw.standings (
                competition_code, season_id, stage, group_name,
                position, team_id, team_name,
                played_games, won, draw, lost, points,
                goals_for, goals_against, goal_difference,
                raw_payload
            ) VALUES %s
        """,
            rows,
        )
    conn.commit()
    logger.info(f"Loaded {len(rows)} standing rows for {competition_code}.")
    return len(rows)


def load_scorers(conn, data: dict, competition_code: str) -> int:
    """Loads top scorers into raw.scorers."""
    scorers = data.get("scorers", [])
    if not scorers:
        logger.warning(f"No scorers found for {competition_code}.")
        return 0

    season_id = data.get("season", {}).get("id")
    rows = []

    for s in scorers:
        rows.append(
            (
                competition_code,
                season_id,
                s.get("player", {}).get("id"),
                s.get("player", {}).get("name"),
                s.get("player", {}).get("nationality"),
                s.get("team", {}).get("id"),
                s.get("team", {}).get("name"),
                s.get("goals") or 0,
                s.get("assists") or 0,
                s.get("penalties") or 0,
                json.dumps(s),
            )
        )

    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM raw.scorers WHERE competition_code = %s AND season_id = %s",
            (competition_code, season_id),
        )
        execute_values(
            cur,
            """
            INSERT INTO raw.scorers (
                competition_code, season_id,
                player_id, player_name, player_nationality,
                team_id, team_name,
                goals, assists, penalties,
                raw_payload
            ) VALUES %s
        """,
            rows,
        )
    conn.commit()
    logger.info(f"Loaded {len(rows)} scorers for {competition_code}.")
    return len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def load_competition(conn, competition_code: str, extraction_date: str = None) -> None:
    """
    Loads all endpoints for a competition from the raw JSON files.

    Args:
        conn:             PostgreSQL connection
        competition_code: e.g. 'WC'
        extraction_date:  Folder date (YYYY-MM-DD). Defaults to today.
    """
    date_folder = extraction_date or datetime.utcnow().strftime("%Y-%m-%d")
    base_path = RAW_DATA_DIR / competition_code / date_folder

    if not base_path.exists():
        logger.error(f"Raw data folder not found: {base_path}")
        logger.error("Run extract_api.py first to generate the raw files.")
        return

    loaders = {
        "matches": load_matches,
        "teams": load_teams,
        "standings": load_standings,
        "scorers": load_scorers,
    }

    for endpoint, loader_fn in loaders.items():
        filepath = base_path / f"{endpoint}.json"

        if not filepath.exists():
            logger.warning(f"File not found, skipping: {filepath}")
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            records = loader_fn(conn, data, competition_code)
            log_extraction(conn, competition_code, endpoint, records, "success")

        except Exception as e:
            logger.error(f"Error loading {endpoint} for {competition_code}: {e}")
            log_extraction(conn, competition_code, endpoint, 0, "error", str(e))
            raise


def run_load(competition_codes: list[str] = None) -> None:
    """Runs the full load for the given competitions."""
    codes = competition_codes or ["WC"]
    logger.info(f"Starting load for: {codes}")

    conn = get_connection()

    try:
        for code in codes:
            logger.info(f"--- Loading: {code} ---")
            load_competition(conn, code)
            logger.info(f"✓ {code} loaded successfully.")
    finally:
        conn.close()
        logger.info("Database connection closed.")


if __name__ == "__main__":
    run_load(competition_codes=["WC"])
