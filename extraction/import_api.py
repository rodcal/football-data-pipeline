import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()

API_TOKEN = os.getenv("FOOTBALL_API_TOKEN")
BASE_URL = "https://api.football-data.org/v4"
RAW_DATA_DIR = Path("data/raw")

# Rate limit: free tier allows 10 requests/minute
RATE_LIMIT_SLEEP = 7  # seconds between requests (safe margin)

# Competitions to extract
COMPETITIONS = {
    "WC": "FIFA World Cup",
    "BSA": "Brasileirão Série A",
    "CL": "UEFA Champions League",
}

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
# HTTP Client
# ---------------------------------------------------------------------------


def get_headers() -> dict:
    """Returns authentication headers for the API."""
    if not API_TOKEN:
        raise ValueError(
            "FOOTBALL_API_TOKEN not found. "
            "Copy .env.example to .env and fill in your token."
        )
    return {"X-Auth-Token": API_TOKEN}


def fetch(endpoint: str, params: dict = None, retries: int = 3) -> dict:
    """
    Makes a GET request to the API with retry logic.

    Args:
        endpoint: API path, e.g. '/competitions/WC/matches'
        params:   Optional query parameters
        retries:  Number of attempts before raising an error

    Returns:
        Parsed JSON response as a dict
    """
    url = f"{BASE_URL}{endpoint}"

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Fetching: {url} (attempt {attempt}/{retries})")
            response = requests.get(
                url, headers=get_headers(), params=params, timeout=30
            )

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 429:
                # Rate limit hit — wait longer and retry
                wait = RATE_LIMIT_SLEEP * attempt
                logger.warning(f"Rate limit hit. Waiting {wait}s before retrying...")
                time.sleep(wait)

            elif response.status_code == 403:
                logger.error(
                    "403 Forbidden — check if your token has access to this competition."
                )
                raise PermissionError(f"Access denied for {url}")

            else:
                logger.warning(f"Unexpected status {response.status_code} for {url}")
                response.raise_for_status()

        except requests.exceptions.ConnectionError:
            logger.warning(
                f"Connection error on attempt {attempt}. Retrying in {RATE_LIMIT_SLEEP}s..."
            )
            time.sleep(RATE_LIMIT_SLEEP)

        except requests.exceptions.Timeout:
            logger.warning(
                f"Timeout on attempt {attempt}. Retrying in {RATE_LIMIT_SLEEP}s..."
            )
            time.sleep(RATE_LIMIT_SLEEP)

    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts.")


# ---------------------------------------------------------------------------
# Save raw JSON
# ---------------------------------------------------------------------------


def save_raw(data: dict, competition_code: str, endpoint_name: str) -> Path:
    """
    Saves the raw API response as a JSON file.

    Args:
        data:             Parsed JSON response
        competition_code: e.g. 'WC'
        endpoint_name:    e.g. 'matches', 'standings', 'teams'

    Returns:
        Path to the saved file
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    folder = RAW_DATA_DIR / competition_code / today
    folder.mkdir(parents=True, exist_ok=True)

    filepath = folder / f"{endpoint_name}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Raw data saved: {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# Extraction functions
# ---------------------------------------------------------------------------


def extract_matches(competition_code: str) -> dict:
    """Extracts all matches for a given competition."""
    data = fetch(f"/competitions/{competition_code}/matches")
    save_raw(data, competition_code, "matches")
    time.sleep(RATE_LIMIT_SLEEP)
    return data


def extract_standings(competition_code: str) -> dict:
    """Extracts current standings for a given competition."""
    data = fetch(f"/competitions/{competition_code}/standings")
    save_raw(data, competition_code, "standings")
    time.sleep(RATE_LIMIT_SLEEP)
    return data


def extract_teams(competition_code: str) -> dict:
    """Extracts all teams in a given competition."""
    data = fetch(f"/competitions/{competition_code}/teams")
    save_raw(data, competition_code, "teams")
    time.sleep(RATE_LIMIT_SLEEP)
    return data


def extract_scorers(competition_code: str) -> dict:
    """Extracts top scorers for a given competition."""
    data = fetch(f"/competitions/{competition_code}/scorers")
    save_raw(data, competition_code, "scorers")
    time.sleep(RATE_LIMIT_SLEEP)
    return data


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run_extraction(competition_codes: list[str] = None) -> None:
    """
    Runs the full extraction for the given competitions.

    Args:
        competition_codes: List of codes to extract. Defaults to all in COMPETITIONS.
    """
    codes = competition_codes or list(COMPETITIONS.keys())
    logger.info(f"Starting extraction for: {codes}")

    results = {}

    for code in codes:
        name = COMPETITIONS.get(code, code)
        logger.info(f"--- Extracting: {name} ({code}) ---")

        try:
            results[code] = {
                "matches": extract_matches(code),
                "standings": extract_standings(code),
                "teams": extract_teams(code),
                "scorers": extract_scorers(code),
            }
            logger.info(f"✓ {name} extracted successfully.")

        except PermissionError as e:
            # Some competitions may not be available on the free tier
            logger.warning(f"Skipping {name}: {e}")

        except Exception as e:
            logger.error(f"Failed to extract {name}: {e}")
            raise

    logger.info("Extraction complete.")
    return results


if __name__ == "__main__":
    # Extract only World Cup by default
    # Change to run_extraction() to extract all competitions
    run_extraction(competition_codes=["WC"])
