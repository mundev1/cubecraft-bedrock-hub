import sys
import os

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def debug_info(path):
    return jsonify({
        "environ": {k: str(v) for k, v in request.environ.items() if 'KEY' not in k and 'SECRET' not in k and 'TOKEN' not in k},
        "headers": dict(request.headers),
        "path": request.path
    })
