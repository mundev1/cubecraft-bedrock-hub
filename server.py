"""
CubeCraft Bedrock Community Hub - Flask REST API & Web Server
Provides endpoints for Leaderboards, Marketplace Bundles, Playable Medal Clips,
and Player Encounter Comments & Reputation.
"""
from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import json
import os
import re
from datetime import datetime
from database import get_db, init_db, seed_db

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Ensure database exists
init_db()
seed_db()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ----------------------------------------------------
# Overview & Games
# ----------------------------------------------------

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM players')
    total_players = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM encounters')
    total_encounters = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM clips')
    total_clips = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM bundles')
    total_bundles = cursor.fetchone()[0]
    conn.close()

    return jsonify({
        "success": True,
        "stats": {
            "total_players": total_players,
            "total_encounters": total_encounters,
            "total_clips": total_clips,
            "active_bundles": total_bundles,
            "online_bedrock_server": "play.cubecraft.net",
            "bedrock_port": 19132
        }
    })

@app.route('/api/games', methods=['GET'])
def get_games():
    games = [
        {"id": "EggWars", "name": "EggWars", "icon": "🥚", "modes": ["All Modes", "Solo", "Duos", "Squads", "Mega"], "desc": "Protect your egg, gather diamonds & iron, destroy enemy eggs!"},
        {"id": "SkyWars", "name": "SkyWars", "icon": "☁️", "modes": ["All Modes", "Solo", "Teams", "Chaos"], "desc": "Fast-paced island combat with loot chests and void knockoffs."},
        {"id": "Lucky Islands", "name": "Lucky Islands", "icon": "🍀", "modes": ["All Modes", "Solo", "Teams"], "desc": "Break lucky blocks to summon explosive sheep, wands, and armor."},
        {"id": "BlockWars", "name": "BlockWars", "icon": "🧱", "modes": ["All Modes", "Bridges", "Core", "CTF"], "desc": "Competitive bridge rushing, capture the flag, and core destroy."},
        {"id": "Survival Games", "name": "Survival Games", "icon": "⚔️", "modes": ["All Modes", "Solo", "Teams"], "desc": "Classic battle royale: scavenge chests, craft gear, survive the deathmatch."},
        {"id": "MinerWare", "name": "MinerWare", "icon": "⛏️", "modes": ["All Modes", "Standard"], "desc": "Rapid-fire micro-challenges testing reflexes and agility."},
        {"id": "Duels", "name": "Duels (Battle Arena)", "icon": "🏆", "modes": ["All Modes", "Classic", "Nodebuff", "UHC"], "desc": "1v1 PvP combat across competitive Bedrock kits."}
    ]
    return jsonify({"success": True, "games": games})

# ----------------------------------------------------
# Leaderboards API
# ----------------------------------------------------

@app.route('/api/leaderboards', methods=['GET'])
def get_leaderboards():
    game = request.args.get('game', 'EggWars')
    mode = request.args.get('mode', 'All Modes')
    sort_by = request.args.get('sort_by', 'wins')
    search = request.args.get('search', '').strip()

    valid_sorts = {
        'wins': 'l.wins DESC',
        'kills': 'l.kills DESC',
        'streak': 'l.streak DESC',
        'rating': 'l.rating DESC'
    }
    order_clause = valid_sorts.get(sort_by, 'l.wins DESC')

    conn = get_db()
    cursor = conn.cursor()

    query = '''
        SELECT l.*, p.rank_title, p.reputation_score, p.avatar_color,
               (SELECT COUNT(*) FROM encounters WHERE player_gamertag = l.player_gamertag) as encounter_count
        FROM leaderboards l
        LEFT JOIN players p ON l.player_gamertag = p.gamertag
        WHERE 1=1
    '''
    params = []

    if game and game.lower() != 'all':
        query += ' AND LOWER(l.game) = LOWER(?)'
        params.append(game)

    if mode and mode.lower() != 'all modes' and mode.lower() != 'all':
        query += ' AND LOWER(l.mode) = LOWER(?)'
        params.append(mode)

    if search:
        query += ' AND LOWER(l.player_gamertag) LIKE LOWER(?)'
        params.append(f'%{search}%')

    query += f' ORDER BY {order_clause} LIMIT 50'
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for idx, r in enumerate(rows, 1):
        item = dict(r)
        item['dynamic_rank'] = idx
        results.append(item)

    podium = results[:3] if len(results) >= 3 else results

    conn.close()
    return jsonify({
        "success": True,
        "game": game,
        "mode": mode,
        "sort_by": sort_by,
        "podium": podium,
        "leaderboard": results,
        "total_results": len(results)
    })

# ----------------------------------------------------
# Bundles API
# ----------------------------------------------------

@app.route('/api/bundles', methods=['GET'])
def get_bundles():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bundles ORDER BY is_featured DESC, price_minecoins DESC')
    rows = cursor.fetchall()
    conn.close()

    bundles = []
    for r in rows:
        b = dict(r)
        try:
            b['items'] = json.loads(b['items_json'])
        except Exception:
            b['items'] = []
        b.pop('items_json', None)
        bundles.append(b)

    return jsonify({"success": True, "bundles": bundles})

@app.route('/api/bundles/<bundle_id>', methods=['GET'])
def get_bundle_detail(bundle_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bundles WHERE id = ?', (bundle_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "error": "Bundle not found"}), 404

    b = dict(row)
    try:
        b['items'] = json.loads(b['items_json'])
    except Exception:
        b['items'] = []
    b.pop('items_json', None)

    return jsonify({"success": True, "bundle": b})

# ----------------------------------------------------
# Playable Medal Clips API
# ----------------------------------------------------

@app.route('/api/clips', methods=['GET'])
def get_clips():
    game = request.args.get('game', 'all')
    sort = request.args.get('sort', 'recent')
    search = request.args.get('search', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = 'SELECT * FROM clips WHERE 1=1'
    params = []

    if game and game.lower() != 'all':
        query += ' AND LOWER(game) = LOWER(?)'
        params.append(game)

    if search:
        query += ' AND (LOWER(title) LIKE LOWER(?) OR LOWER(gamertag) LIKE LOWER(?))'
        params.extend([f'%{search}%', f'%{search}%'])

    if sort == 'popular':
        query += ' ORDER BY upvotes DESC, views DESC'
    elif sort == 'views':
        query += ' ORDER BY views DESC'
    else:
        query += ' ORDER BY created_at DESC'

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    clips = [dict(r) for r in rows]
    return jsonify({"success": True, "clips": clips, "total": len(clips)})

@app.route('/api/clips', methods=['POST'])
def add_clip():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    gamertag = data.get('gamertag', '').strip()
    game = data.get('game', 'EggWars').strip()
    medal_url = data.get('medal_url', '').strip()
    video_url = data.get('video_url', '').strip()
    duration = data.get('duration', '0:30').strip()

    if not title or not gamertag:
        return jsonify({"success": False, "error": "Title and Player Gamertag are required"}), 400

    # Format or sanitize medal/video URL
    if not video_url and not medal_url:
        video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

    # Default Bedrock game thumbnail
    thumbnail_url = data.get('thumbnail_url') or "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=600&q=80"

    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clips (title, gamertag, game, medal_url, video_url, thumbnail_url, duration, views, upvotes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?)
    ''', (title, gamertag, game, medal_url, video_url, thumbnail_url, duration, now_str))
    new_id = cursor.lastrowid
    conn.commit()

    # Also register player if new
    cursor.execute('SELECT gamertag FROM players WHERE LOWER(gamertag) = LOWER(?)', (gamertag,))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO players (gamertag, rank_title, total_games, reputation_score, avatar_color, bio, first_seen)
            VALUES (?, 'Player', 10, 100, '#00e5ff', 'Community Bedrock clip creator.', ?)
        ''', (gamertag, datetime.utcnow().strftime('%Y-%m-%d')))
        conn.commit()

    conn.close()
    return jsonify({"success": True, "message": "Clip submitted successfully!", "clip_id": new_id})

@app.route('/api/clips/<int:clip_id>/upvote', methods=['POST'])
def upvote_clip(clip_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE clips SET upvotes = upvotes + 1 WHERE id = ?', (clip_id,))
    conn.commit()
    cursor.execute('SELECT upvotes FROM clips WHERE id = ?', (clip_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "error": "Clip not found"}), 404

    return jsonify({"success": True, "upvotes": row['upvotes']})

@app.route('/api/clips/<int:clip_id>/view', methods=['POST'])
def view_clip(clip_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE clips SET views = views + 1 WHERE id = ?', (clip_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# ----------------------------------------------------
# Player Encounters & Community Comments API
# ----------------------------------------------------

@app.route('/api/encounters/recent', methods=['GET'])
def get_recent_encounters():
    limit = int(request.args.get('limit', 15))
    tag = request.args.get('tag', 'all')

    conn = get_db()
    cursor = conn.cursor()
    query = '''
        SELECT e.*, p.rank_title, p.avatar_color
        FROM encounters e
        LEFT JOIN players p ON e.player_gamertag = p.gamertag
        WHERE e.reported = 0
    '''
    params = []
    if tag and tag.lower() != 'all':
        query += ' AND LOWER(e.encounter_type) = LOWER(?)'
        params.append(tag)

    query += ' ORDER BY e.created_at DESC LIMIT ?'
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    encounters = [dict(r) for r in rows]
    return jsonify({"success": True, "encounters": encounters})

@app.route('/api/players/search', methods=['GET'])
def search_players():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"success": True, "players": []})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*,
               (SELECT COUNT(*) FROM encounters WHERE player_gamertag = p.gamertag) as encounter_count
        FROM players p
        WHERE LOWER(p.gamertag) LIKE LOWER(?)
        LIMIT 10
    ''', (f'%{q}%',))
    rows = cursor.fetchall()
    conn.close()

    return jsonify({"success": True, "players": [dict(r) for r in rows]})

@app.route('/api/players/<gamertag>', methods=['GET'])
def get_player_profile(gamertag):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM players WHERE LOWER(gamertag) = LOWER(?)', (gamertag,))
    player_row = cursor.fetchone()

    # If player does not exist yet in players table, provide dynamic profile
    if not player_row:
        player = {
            "gamertag": gamertag,
            "rank_title": "Bedrock Player",
            "total_games": 0,
            "reputation_score": 100,
            "avatar_color": "#00e5ff",
            "bio": "Minecraft Bedrock CubeCraft adventurer.",
            "first_seen": "Recently Seen",
            "is_new": True
        }
    else:
        player = dict(player_row)
        player['is_new'] = False

    # Fetch player's leaderboard stats
    cursor.execute('SELECT * FROM leaderboards WHERE LOWER(player_gamertag) = LOWER(?)', (gamertag,))
    leaderboards = [dict(r) for r in cursor.fetchall()]

    # Fetch player encounters
    cursor.execute('''
        SELECT * FROM encounters
        WHERE LOWER(player_gamertag) = LOWER(?) AND reported = 0
        ORDER BY created_at DESC
    ''', (gamertag,))
    encounters = [dict(r) for r in cursor.fetchall()]

    # Calculate statistics & sentiment
    total_encounters = len(encounters)
    positive_count = sum(1 for e in encounters if e['sentiment'] == 'positive')
    avg_rating = round(sum(e['rating'] for e in encounters) / total_encounters, 1) if total_encounters > 0 else 5.0
    
    # Dynamic badges based on tags
    tag_counts = {}
    for e in encounters:
        t = e['encounter_type']
        tag_counts[t] = tag_counts.get(t, 0) + 1

    badges = []
    if tag_counts.get("God-tier Clutch", 0) >= 2:
        badges.append({"name": "Clutch God", "icon": "⚡", "color": "#00e5ff"})
    if tag_counts.get("Helpful Teammate", 0) >= 2:
        badges.append({"name": "Team Anchor", "icon": "🛡️", "color": "#10b981"})
    if tag_counts.get("Tactical Trapper", 0) >= 1:
        badges.append({"name": "Architect Trapper", "icon": "🕸️", "color": "#f59e0b"})
    if tag_counts.get("Sweaty Opponent", 0) >= 2:
        badges.append({"name": "High ELO Threat", "icon": "🔥", "color": "#f43f5e"})
    if len(badges) == 0 and total_encounters > 0:
        badges.append({"name": "Community Verified", "icon": "✨", "color": "#38bdf8"})

    conn.close()

    return jsonify({
        "success": True,
        "player": player,
        "stats": {
            "total_encounters": total_encounters,
            "positive_count": positive_count,
            "positive_rate": round((positive_count / total_encounters) * 100) if total_encounters > 0 else 100,
            "avg_rating": avg_rating,
            "badges": badges,
            "tag_breakdown": tag_counts
        },
        "leaderboards": leaderboards,
        "encounters": encounters
    })

@app.route('/api/players/<gamertag>/encounters', methods=['POST'])
def add_player_encounter(gamertag):
    data = request.get_json() or {}
    reviewer_name = data.get('reviewer_name', '').strip() or 'Anonymous Bedrocker'
    game_played = data.get('game_played', 'EggWars').strip()
    encounter_type = data.get('encounter_type', 'Helpful Teammate').strip()
    rating = int(data.get('rating', 5))
    comment = data.get('comment', '').strip()

    if not comment:
        return jsonify({"success": False, "error": "Comment story cannot be empty"}), 400

    # Classify sentiment
    negative_types = ["Suspicious / Cheater Alert", "Toxic / Unsportsmanlike", "Game Thrower"]
    neutral_types = ["AFK Teammate", "Neutral Encounter"]
    if encounter_type in negative_types:
        sentiment = 'negative'
    elif encounter_type in neutral_types:
        sentiment = 'neutral'
    else:
        sentiment = 'positive'

    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    cursor = conn.cursor()

    # Ensure player exists in players table
    cursor.execute('SELECT * FROM players WHERE LOWER(gamertag) = LOWER(?)', (gamertag,))
    player_row = cursor.fetchone()
    if not player_row:
        colors = ["#00e5ff", "#38bdf8", "#10b981", "#fbbf24", "#a855f7", "#f43f5e"]
        chosen_color = colors[len(gamertag) % len(colors)]
        cursor.execute('''
            INSERT INTO players (gamertag, rank_title, total_games, reputation_score, avatar_color, bio, first_seen)
            VALUES (?, 'Player', 1, 100, ?, 'Discovered in Bedrock lobby.', ?)
        ''', (gamertag.strip(), chosen_color, datetime.utcnow().strftime('%Y-%m-%d')))
        player_actual_tag = gamertag.strip()
    else:
        player_actual_tag = player_row['gamertag']

    # Insert encounter
    cursor.execute('''
        INSERT INTO encounters (player_gamertag, reviewer_name, game_played, encounter_type, sentiment, rating, comment, helpful_votes, reported, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
    ''', (player_actual_tag, reviewer_name, game_played, encounter_type, sentiment, rating, comment, now_str))

    # Recalculate reputation score
    cursor.execute('SELECT sentiment FROM encounters WHERE LOWER(player_gamertag) = LOWER(?) AND reported = 0', (gamertag,))
    all_sentiments = [row['sentiment'] for row in cursor.fetchall()]
    total = len(all_sentiments)
    positives = sum(1 for s in all_sentiments if s == 'positive')
    neutrals = sum(1 for s in all_sentiments if s == 'neutral')
    negatives = sum(1 for s in all_sentiments if s == 'negative')

    # Formula: 100 base score weighted by sentiment ratio
    if total > 0:
        new_score = max(10, min(100, int((positives * 100 + neutrals * 75 + negatives * 20) / total)))
    else:
        new_score = 100

    cursor.execute('UPDATE players SET reputation_score = ? WHERE LOWER(gamertag) = LOWER(?)', (new_score, gamertag))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Encounter review posted for {player_actual_tag}!",
        "new_reputation": new_score
    })

@app.route('/api/encounters/<int:encounter_id>/helpful', methods=['POST'])
def upvote_encounter(encounter_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE encounters SET helpful_votes = helpful_votes + 1 WHERE id = ?', (encounter_id,))
    conn.commit()
    cursor.execute('SELECT helpful_votes FROM encounters WHERE id = ?', (encounter_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "error": "Encounter not found"}), 404

    return jsonify({"success": True, "helpful_votes": row['helpful_votes']})

@app.route('/api/encounters/<int:encounter_id>/report', methods=['POST'])
def report_encounter(encounter_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE encounters SET reported = 1 WHERE id = ?', (encounter_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Encounter reported for community review."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5055))
    print(f"CubeCraft Bedrock Community Hub starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
