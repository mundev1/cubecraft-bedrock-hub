import sys
import os
import traceback

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from server import app

    class VercelPathFixMiddleware:
        """
        Ensures Flask router receives the actual requested URL path
        when deployed behind Vercel's serverless rewrite proxy.
        """
        def __init__(self, wsgi_app):
            self.wsgi_app = wsgi_app

        def __call__(self, environ, start_response):
            orig_path = (
                environ.get('HTTP_X_FORWARDED_PATH') or
                environ.get('HTTP_X_MATCHED_PATH') or
                environ.get('REQUEST_URI') or
                environ.get('RAW_URI')
            )
            path_info = environ.get('PATH_INFO', '')

            if orig_path:
                clean_path = orig_path.split('?')[0]
                if clean_path.startswith('/'):
                    environ['PATH_INFO'] = clean_path
            elif path_info in ('/api/index', '/api/index.py'):
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
