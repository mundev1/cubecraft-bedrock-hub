import sys
import os

# Add root directory to path for Python module resolution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app

# Vercel Serverless Function entrypoint
app = app
