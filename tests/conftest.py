# conftest.py
# Pytest configuration file — runs automatically before any test.

import sys
from pathlib import Path

# Make extraction modules importable from any test file
sys.path.insert(0, str(Path(__file__).parent.parent / "extraction"))
