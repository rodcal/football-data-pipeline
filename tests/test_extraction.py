"""
test_extraction.py
------------------
Unit tests for extraction and load functions.
Uses mocking to avoid real API calls or database connections.
 
Run with:
    pytest tests/test_extraction.py -v
"""
 
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
 
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "extraction"))
 
# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
 
@pytest.fixture
def sample_matches_response():
    return {
        "competition": {"code": "WC", "name": "FIFA World Cup"},
        "season": {"id": 1, "startDate": "2026-06-11", "endDate": "2026-07-19"},
        "matches": [
            {
                "id": 100,
                "utcDate": "2026-06-12T18:00:00Z",
                "status": "FINISHED",
                "matchday": 1,
                "stage": "GROUP_STAGE",
                "group": "GROUP_A",
                "homeTeam": {"id": 10, "name": "Brazil"},
                "awayTeam": {"id": 11, "name": "Argentina"},
                "score": {
                    "fullTime": {"home": 2, "away": 1},
                    "winner": "HOME_TEAM"
                },
                "competition": {"name": "FIFA World Cup"},
                "season": {"id": 1, "startDate": "2026-06-11", "endDate": "2026-07-19"}
            },
            {
                "id": 101,
                "utcDate": "2026-06-12T21:00:00Z",
                "status": "FINISHED",
                "matchday": 1,
                "stage": "GROUP_STAGE",
                "group": "GROUP_B",
                "homeTeam": {"id": 12, "name": "France"},
                "awayTeam": {"id": 13, "name": "Germany"},
                "score": {
                    "fullTime": {"home": 1, "away": 1},
                    "winner": "DRAW"
                },
                "competition": {"name": "FIFA World Cup"},
                "season": {"id": 1, "startDate": "2026-06-11", "endDate": "2026-07-19"}
            }
        ]
    }
 
 
@pytest.fixture
def sample_teams_response():
    return {
        "competition": {"code": "WC"},
        "season": {"id": 1},
        "teams": [
            {
                "id": 10,
                "name": "Brazil",
                "shortName": "Brazil",
                "tla": "BRA",
                "crest": "https://example.com/brazil.png",
                "address": "Brasília, Brazil",
                "website": "https://cbf.com.br",
                "founded": 1914,
                "clubColors": "Yellow / Green",
                "venue": "Estádio do Maracanã"
            }
        ]
    }
 
 
@pytest.fixture
def sample_scorers_response():
    return {
        "season": {"id": 1},
        "scorers": [
            {
                "player": {"id": 1, "name": "Vinicius Jr", "nationality": "Brazil"},
                "team": {"id": 10, "name": "Brazil"},
                "goals": 5,
                "assists": 3,
                "penalties": 1
            },
            {
                "player": {"id": 2, "name": "Kylian Mbappé", "nationality": "France"},
                "team": {"id": 12, "name": "France"},
                "goals": 4,
                "assists": 2,
                "penalties": 0
            }
        ]
    }
 
# ---------------------------------------------------------------------------
# Tests — import_api.py
# ---------------------------------------------------------------------------
 
class TestGetHeaders:
    def test_returns_token_header(self):
        """get_headers should return X-Auth-Token header."""
        with patch.dict("os.environ", {"FOOTBALL_API_TOKEN": "test_token_123"}):
            with patch("import_api.API_TOKEN", "test_token_123"):
                from import_api import get_headers
                headers = get_headers()
                assert headers == {"X-Auth-Token": "test_token_123"}
 
    def test_raises_if_token_missing(self):
        """get_headers should raise ValueError if token is not set."""
        with patch("import_api.API_TOKEN", None):
            from import_api import get_headers
            with pytest.raises(ValueError, match="FOOTBALL_API_TOKEN not found"):
                get_headers()
 
 
class TestFetch:
    def test_successful_fetch(self, sample_matches_response):
        """fetch should return parsed JSON on 200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_matches_response
 
        with patch("import_api.requests.get", return_value=mock_response), \
             patch.dict("os.environ", {"FOOTBALL_API_TOKEN": "test_token"}):
            from import_api import fetch
            result = fetch("/competitions/WC/matches")
            assert result == sample_matches_response
 
    def test_retries_on_rate_limit(self):
        """fetch should retry when receiving 429 status."""
        mock_429 = MagicMock()
        mock_429.status_code = 429
 
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"matches": []}
 
        with patch("import_api.requests.get", side_effect=[mock_429, mock_200]), \
             patch("import_api.time.sleep"), \
             patch.dict("os.environ", {"FOOTBALL_API_TOKEN": "test_token"}):
            from import_api import fetch
            result = fetch("/competitions/WC/matches")
            assert result == {"matches": []}
 
    def test_raises_on_403(self):
        """fetch should raise PermissionError on 403 response."""
        mock_response = MagicMock()
        mock_response.status_code = 403
 
        with patch("import_api.requests.get", return_value=mock_response), \
             patch.dict("os.environ", {"FOOTBALL_API_TOKEN": "test_token"}):
            from import_api import fetch
            with pytest.raises(PermissionError):
                fetch("/competitions/WC/matches")
 
    def test_raises_after_max_retries(self):
        """fetch should raise RuntimeError after exhausting retries."""
        import requests as req
        with patch("import_api.requests.get", side_effect=req.exceptions.ConnectionError), \
             patch("import_api.time.sleep"), \
             patch.dict("os.environ", {"FOOTBALL_API_TOKEN": "test_token"}):
            from import_api import fetch
            with pytest.raises(RuntimeError, match="Failed to fetch"):
                fetch("/competitions/WC/matches", retries=2)
 
 
class TestSaveRaw:
    def test_saves_json_file(self, tmp_path, sample_matches_response):
        """save_raw should create a JSON file in the correct path."""
        with patch("import_api.RAW_DATA_DIR", tmp_path):
            from import_api import save_raw
            filepath = save_raw(sample_matches_response, "WC", "matches")
            assert filepath.exists()
            with open(filepath) as f:
                data = json.load(f)
            assert data == sample_matches_response
 
    def test_creates_directory_structure(self, tmp_path, sample_matches_response):
        """save_raw should create competition/date folder structure."""
        with patch("import_api.RAW_DATA_DIR", tmp_path):
            from import_api import save_raw
            filepath = save_raw(sample_matches_response, "WC", "matches")
            parts = filepath.parts
            assert "WC" in parts
            assert filepath.name == "matches.json"
 
# ---------------------------------------------------------------------------
# Tests — load_to_postgres.py
# ---------------------------------------------------------------------------
 
class TestLoadMatches:
    def test_loads_correct_number_of_rows(self, sample_matches_response):
        """load_matches should insert one row per match."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
 
        with patch("load_to_postgres.execute_values"):
            from load_to_postgres import load_matches
            count = load_matches(mock_conn, sample_matches_response, "WC")
            assert count == 2
 
    def test_returns_zero_on_empty_response(self):
        """load_matches should return 0 when no matches in response."""
        mock_conn = MagicMock()
        from load_to_postgres import load_matches
        count = load_matches(mock_conn, {"matches": []}, "WC")
        assert count == 0
 
 
class TestLoadTeams:
    def test_loads_correct_number_of_rows(self, sample_teams_response):
        """load_teams should insert one row per team."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
 
        with patch("load_to_postgres.execute_values"):
            from load_to_postgres import load_teams
            count = load_teams(mock_conn, sample_teams_response, "WC")
            assert count == 1
 
    def test_returns_zero_on_empty_response(self):
        """load_teams should return 0 when no teams in response."""
        mock_conn = MagicMock()
        from load_to_postgres import load_teams
        count = load_teams(mock_conn, {"teams": []}, "WC")
        assert count == 0
 
 
class TestLoadScorers:
    def test_loads_correct_number_of_rows(self, sample_scorers_response):
        """load_scorers should insert one row per scorer."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
 
        with patch("load_to_postgres.execute_values"):
            from load_to_postgres import load_scorers
            count = load_scorers(mock_conn, sample_scorers_response, "WC")
            assert count == 2
 
    def test_coalesces_null_goals(self):
        """load_scorers should handle missing goals/assists/penalties as 0 in Python."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
 
        response = {
            "season": {"id": 1},
            "scorers": [
                {
                    "player": {"id": 99, "name": "Test Player", "nationality": "Test"},
                    "team": {"id": 1, "name": "Test FC"},
                    "goals": None,
                    "assists": None,
                    "penalties": None
                }
            ]
        }
 
        captured_rows = []
        def capture_execute_values(cur, sql, rows):
            captured_rows.extend(rows)
 
        with patch("load_to_postgres.execute_values", side_effect=capture_execute_values):
            from load_to_postgres import load_scorers
            load_scorers(mock_conn, response, "WC")
 
        row = captured_rows[0]
        assert row[7] == 0   # goals
        assert row[8] == 0   # assists
        assert row[9] == 0   # penalties
 