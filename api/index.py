"""
Vercel Serverless Function Handler for SkyPulse Weather Dashboard.
Exports 'app', 'application', and 'handler' conforming to Vercel Python Runtime.
"""

import sys
from pathlib import Path

# Ensure project root is in path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import top-level handlers from main
from main import app, application, handler
