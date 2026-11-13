import sys
import os
import traceback

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from server import app
except Exception as e:
    from flask import Flask
    app = Flask(__name__)
    err_trace = traceback.format_exc()
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all_error(path):
        return f"<pre style='color:red; font-size:14px;'>Vercel Serverless Function Startup Error:\n\n{err_trace}</pre>", 500
