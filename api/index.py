import sys
import os
import traceback
import urllib.parse

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from server import app

    class VercelPathFixMiddleware:
        """
        Extracts the original requested route from Vercel's rewrite parameter
        or standard proxy headers so Flask matches all subroutes accurately.
        """
        def __init__(self, wsgi_app):
            self.wsgi_app = wsgi_app

        def __call__(self, environ, start_response):
            query = environ.get('QUERY_STRING', '')
            actual_path = None
            if '__path=' in query:
                params = query.split('&')
                remaining = []
                for p in params:
                    if p.startswith('__path='):
                        actual_path = urllib.parse.unquote(p[7:])
                    else:
                        remaining.append(p)
                environ['QUERY_STRING'] = '&'.join(remaining)

            if not actual_path:
                actual_path = (
                    environ.get('HTTP_X_FORWARDED_PATH') or
                    environ.get('HTTP_X_MATCHED_PATH') or
                    environ.get('REQUEST_URI') or
                    environ.get('RAW_URI')
                )

            if actual_path:
                clean_path = actual_path.split('?')[0]
                if not clean_path.startswith('/'):
                    clean_path = '/' + clean_path
                environ['PATH_INFO'] = clean_path
            elif environ.get('PATH_INFO', '') in ('/api/index', '/api/index.py'):
                environ['PATH_INFO'] = '/'

            return self.wsgi_app(environ, start_response)

    app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)

except Exception as e:
    from flask import Flask
    app = Flask(__name__)
    err_trace = traceback.format_exc()
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all_error(path):
        return f"<pre style='color:red; font-size:14px;'>Vercel Serverless Function Startup Error:\n\n{err_trace}</pre>", 500
