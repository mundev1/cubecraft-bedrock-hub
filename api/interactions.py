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
        import database
        db_info = {}
        try:
            conn = database.get_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM leaderboards")
            lb_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM players")
            pl_count = c.fetchone()[0]
            conn.close()
            db_info = {
                "db_path": database.DB_PATH,
                "db_exists": os.path.exists(database.DB_PATH),
                "leaderboards": lb_count,
                "players": pl_count
            }
        except Exception as e:
            db_info = {"error": str(e)}

        return jsonify({
            "status": "online",
            "endpoint": "/api/interactions",
            "public_key_configured": bool(public_key),
            "db_info": db_info,
            "cwd": os.getcwd(),
            "files_here": os.listdir('.')[:15]
        }), 200

    res_data, status_code = handle_discord_interaction(request.get_data(), request.headers)
    return jsonify(res_data), status_code
