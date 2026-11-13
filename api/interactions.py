import sys
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from flask import Flask, request, jsonify
from discord_interactions_handler import handle_discord_interaction

app = Flask(__name__)

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def interactions_entry(path):
    if request.method == 'GET':
        public_key = os.getenv("DISCORD_PUBLIC_KEY", "").strip()
        return jsonify({
            "status": "online",
            "endpoint": "/api/interactions",
            "public_key_configured": bool(public_key),
            "instructions": "Paste this full URL into Discord Developer Portal -> General Information -> Interactions Endpoint URL: https://cubecraft-bedrock-hub.vercel.app/api/interactions"
        }), 200

    res_data, status_code = handle_discord_interaction(request.get_data(), request.headers)
    return jsonify(res_data), status_code
