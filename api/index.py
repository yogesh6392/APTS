"""
Vercel Serverless Function entrypoint for APTS
Directly interfaces with APTSRequestHandler from server.py
"""
import os
import sys

# Ensure root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import APTSRequestHandler, init_db

# Initialize database on cold start if needed
try:
    init_db()
except Exception as e:
    print(f"[VERCEL] Database initialization notice: {e}")

class handler(APTSRequestHandler):
    def __init__(self, *args, **kwargs):
        # On Vercel, directory is ROOT_DIR
        super().__init__(*args, directory=ROOT_DIR, **kwargs)
