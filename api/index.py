"""
Vercel Serverless Function entrypoint for APTS
Directly interfaces with APTSRequestHandler from server.py
"""
import os
import sys
import traceback
import json

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server import APTSRequestHandler, init_db

# Initialize database on cold start
try:
    init_db()
except Exception as e:
    print(f"[VERCEL COLD START] init_db exception: {e}")

class handler(APTSRequestHandler):
    def __init__(self, *args, **kwargs):
        # Prevent any duplicate directory keyword arguments
        kwargs.pop('directory', None)
        super().__init__(*args, **kwargs)

    def _normalize_path(self):
        # In Vercel serverless, requests may be rewritten. Check headers for original client URI.
        real_uri = (
            self.headers.get('x-forwarded-uri') or
            self.headers.get('x-matched-path') or
            self.headers.get('x-original-uri')
        )
        if real_uri:
            self.path = real_uri

    def do_GET(self):
        try:
            self._normalize_path()
            super().do_GET()
        except Exception as e:
            self._send_server_error(e)

    def do_POST(self):
        try:
            self._normalize_path()
            super().do_POST()
        except Exception as e:
            self._send_server_error(e)

    def do_PUT(self):
        try:
            self._normalize_path()
            super().do_PUT()
        except Exception as e:
            self._send_server_error(e)

    def do_OPTIONS(self):
        try:
            self._normalize_path()
            super().do_OPTIONS()
        except Exception as e:
            self._send_server_error(e)

    def _send_server_error(self, exc):
        tb = traceback.format_exc()
        print(f"[VERCEL ERROR] {exc}\n{tb}")
        try:
            body = json.dumps({
                "success": False,
                "error": f"Server Error: {str(exc)}"
            }).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass
