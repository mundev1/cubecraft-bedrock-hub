"""
CubeCraft Bedrock Community Hub - Flask REST API & Web Server
Encompassing 39 Bedrock game modes, 826+ real players, live leaderboards,
store bundles, playable Medal & community clips, and player encounter comments.
"""
from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import json
import os
import re
import math
import time
import urllib.request
from datetime import datetime
from database import (
    get_db, init_db, sync_cubecraft_leaderboards,
    sync_cubecraft_marketplace, seed_clips, seed_custom_players,
    parse_leaderboard_info, parse_minecraft_rank,
    init_server_tracker, log_server_status,
    get_cross_mode_masters, get_competitiveness_scores,
    get_rank_distribution, get_server_tracker_stats,
    seed_maps_strategy, get_all_maps_strategy,
    get_map_strategy_detail, get_generator_tiers_data,
    get_bridging_benchmarks_data
)
from discord_exporter import (
    build_player_discord_embed,
    build_leaderboard_champion_discord_embed,
    build_server_status_discord_embed,
    build_map_tactics_discord_embed,
    send_discord_webhook
)

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Ensure database is initialized
init_db()
seed_custom_players()
seed_clips()
init_server_tracker(6000)
seed_maps_strategy()

# Ensure marketplace has authentic data
conn_init = get_db()
cur_init = conn_init.cursor()
cur_init.execute('SELECT COUNT(*) FROM marketplace')
if cur_init.fetchone()[0] == 0:
    sync_cubecraft_marketplace()
conn_init.close()

# ----------------------------------------------------
# Live Bedrock Status Cache (Refreshes Every 30 Seconds)
# ----------------------------------------------------
_online_cache = {
    "count": 6000,
    "last_fetched": 0
}

def get_live_online_count():
    """Fetches real online count from CubeCraft status API with 30s in-memory caching."""
    now = time.time()
    if now - _online_cache["last_fetched"] < 30:
        return _online_cache["count"]

    try:
        req = urllib.request.Request('https://api.cc-data.ru/bedrock/status', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            status_data = json.loads(resp.read().decode('utf-8'))
            if isinstance(status_data, list) and len(status_data) > 0:
                for entry in status_data:
                    if entry.get('name') == 'online':
                        val = int(entry.get('value', 6000))
                        _online_cache["count"] = val
                        _online_cache["last_fetched"] = now
                        log_server_status(val)
                        return val
            elif isinstance(status_data, dict) and 'online' in status_data:
                val = int(status_data['online'])
                _online_cache["count"] = val
                _online_cache["last_fetched"] = now
                log_server_status(val)
                return val
    except Exception:
        pass

    return _online_cache["count"]

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
    cursor.execute('SELECT COUNT(*) FROM leaderboards')
    total_leaderboard_entries = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM encounters')
    total_encounters = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM clips')
    total_clips = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM marketplace')
    total_marketplace_items = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT game) FROM leaderboards')
    total_games = cursor.fetchone()[0]
    conn.close()

    online_count = get_live_online_count()

    return jsonify({
        "success": True,
        "stats": {
            "total_players": total_players,
            "total_leaderboard_entries": total_leaderboard_entries,
            "total_encounters": total_encounters,
            "total_clips": total_clips,
            "total_marketplace_items": total_marketplace_items,
            "active_bundles": total_marketplace_items,
            "total_games": total_games,
            "online_players": online_count,
            "online_bedrock_server": "play.cubecraft.net",
            "bedrock_port": 19132
        }
    })

@app.route('/api/games', methods=['GET'])
def get_games():
    """Returns all games along with their actual Bedrock sub-modes from the database."""
    conn = get_db()
    cursor = conn.cursor()

    game_icons = {
        'EggWars': '🥚',
        'SkyWars': '☁️',
        'BlockWars': '🧱',
        'BedWars': '🛏️',
        'Lucky Islands': '🍀',
        'Duels (Battle Arena)': '🏆',
        'Survival Games': '⚔️',
        'MinerWare': '⛏️',
        'Parkour': '🏃',
        'Pillars of Fortune': '🏛️',
        'Disasters': '🌋',
        'Mob Hunt': '🏹'
    }

    game_descriptions = {
        'EggWars': 'Protect your egg, farm diamonds & iron, destroy opponent eggs in Solo, Duos, Squads & Mega.',
        'SkyWars': 'High-stakes floating island combat with Solo, Duos, Squads, Chaos, and Duels.',
        'BlockWars': 'Competitive Bridges (5v5 & Duels), CTF, and massive 50v50 wars (Bridges, DTC, Domination, TDM).',
        'BedWars': 'Defend your bed, collect team iron and emeralds, eliminate opposing beds across Solo, Duos & Squads.',
        'Lucky Islands': 'Break lucky blocks to summon wands, explosive sheep, and chaotic battle gear.',
        'Duels (Battle Arena)': 'Fast 1v1 and 2v2 competitive PvP (Classic, Nodebuff, OP Duels, Free For All).',
        'Survival Games': 'The definitive battle royale: loot cornucopia chests, track players, survive deathmatch.',
        'MinerWare': 'Dozens of high-speed micro-games and boss challenges testing pure Bedrock reflexes.',
        'Parkour': 'Precision jumps, speedrunning checkpoints, and competitive timed leaderboards.',
        'Pillars of Fortune': 'Platform survival on pillars with random item drops and knockback rods.',
        'Disasters': 'Survive natural disasters, rising lava, meteors, and acid rain.',
        'Mob Hunt': 'Hide and seek prop hunt across interactive Bedrock maps.'
    }

    cursor.execute('SELECT DISTINCT game, mode FROM leaderboards ORDER BY game, mode')
    rows = cursor.fetchall()
    conn.close()

    games_dict = {}
    for r in rows:
        g = r['game']
        m = r['mode']
        if g not in games_dict:
            games_dict[g] = {
                "id": g,
                "name": g,
                "icon": game_icons.get(g, '🎮'),
                "desc": game_descriptions.get(g, 'CubeCraft Bedrock competitive mode.'),
                "modes": ["All Modes"]
            }
        if m and m not in games_dict[g]["modes"]:
            games_dict[g]["modes"].append(m)

    # Sort games with classic top games first
    preferred_order = [
        'EggWars', 'SkyWars', 'BlockWars', 'BedWars', 'Lucky Islands',
        'Duels (Battle Arena)', 'Survival Games', 'MinerWare', 'Parkour',
        'Pillars of Fortune', 'Disasters', 'Mob Hunt'
    ]
    games_list = []
    for p in preferred_order:
        if p in games_dict:
            games_list.append(games_dict.pop(p))
    games_list.extend(games_dict.values())

    return jsonify({"success": True, "games": games_list})

# ----------------------------------------------------
# Leaderboards API
# ----------------------------------------------------

@app.route('/api/leaderboards', methods=['GET'])
def get_leaderboards():
    game = request.args.get('game', 'EggWars')
    mode = request.args.get('mode', 'All Modes')
    search = request.args.get('search', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = '''
        SELECT l.id, l.player_gamertag, l.game, l.mode, l.sub_mode_id, l.points, l.rank,
               COALESCE(l.player_icon, p.avatar_icon) as player_avatar_icon,
               p.rank_title, p.avatar_color, p.raw_name,
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

    query += ' ORDER BY l.points DESC LIMIT 100'
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
        "podium": podium,
        "leaderboard": results,
        "total_results": len(results)
    })

@app.route('/api/sync-leaderboards', methods=['POST'])
def sync_leaderboards():
    """Trigger a live sync of all 39 CubeCraft leaderboards."""
    try:
        rows, players = sync_cubecraft_leaderboards()
        return jsonify({
            "success": True,
            "message": f"Synchronized {rows} leaderboard ranks across {players} players successfully!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------------------------------------------
# Cross-Mode Dominance & Server Analytics API
# ----------------------------------------------------

@app.route('/api/analytics/all-around-masters', methods=['GET'])
def get_all_around_masters_api():
    limit = max(1, min(100, int(request.args.get('limit', 25))))
    masters = get_cross_mode_masters(limit)
    return jsonify({
        "success": True,
        "masters": masters,
        "total": len(masters)
    })

@app.route('/api/analytics/competitiveness', methods=['GET'])
def get_competitiveness_api():
    sort = request.args.get('sort', 'tightest').lower()
    game_filter = request.args.get('game', 'all').lower()

    scores = get_competitiveness_scores()
    if game_filter and game_filter != 'all':
        scores = [s for s in scores if s['game'].lower() == game_filter]

    if sort == 'widest':
        scores.sort(key=lambda s: s['point_spread'], reverse=True)
    elif sort == 'highest_threshold':
        scores.sort(key=lambda s: s['min_points'], reverse=True)
    elif sort == 'highest_leader':
        scores.sort(key=lambda s: s['max_points'], reverse=True)
    elif sort == 'alphabetical':
        scores.sort(key=lambda s: (s['game'], s['mode']))
    else:  # tightest
        scores.sort(key=lambda s: s['point_spread'])

    return jsonify({
        "success": True,
        "competitiveness": scores,
        "total_modes": len(scores)
    })

@app.route('/api/analytics/rank-distribution', methods=['GET'])
def get_rank_distribution_api():
    ranks = get_rank_distribution()
    return jsonify({
        "success": True,
        **ranks
    })

@app.route('/api/analytics/server-tracker', methods=['GET'])
def get_server_tracker_api():
    get_live_online_count()
    stats = get_server_tracker_stats()
    return jsonify({
        "success": True,
        **stats
    })

@app.route('/api/analytics/overview', methods=['GET'])
def get_analytics_overview_api():
    masters = get_cross_mode_masters(15)
    scores = get_competitiveness_scores()
    ranks = get_rank_distribution()
    tracker = get_server_tracker_stats()

    return jsonify({
        "success": True,
        "masters": masters,
        "competitiveness": scores,
        "rank_distribution": ranks,
        "server_tracker": tracker
    })

# ----------------------------------------------------
# CubeCraft Bedrock Marketplace API (900+ Official Items)
# ----------------------------------------------------

@app.route('/api/marketplace', methods=['GET'])
def get_marketplace():
    """
    Returns authentic CubeCraft Bedrock Marketplace catalog from SQLite cache.
    Supports pagination (page, limit), full-text search, filter pills, and sorting.
    """
    page = max(1, int(request.args.get('page', 1)))
    limit = max(1, min(100, int(request.args.get('limit', 24))))
    search = request.args.get('search', '').strip()
    filter_val = request.args.get('filter', 'all').lower()
    sort_by = request.args.get('sort', 'rating').lower()

    conn = get_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if search:
        conditions.append('(LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?) OR LOWER(search_name) LIKE LOWER(?))')
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    if filter_val == 'available':
        conditions.append('available = 1')
    elif filter_val == 'high_rated':
        conditions.append('rating >= 4.5')
    elif filter_val == 'under_500':
        conditions.append('price <= 500')
    elif filter_val == 'free':
        conditions.append('price = 0')
    elif filter_val == 'cages':
        conditions.append('(LOWER(name) LIKE "%cage%" OR LOWER(description) LIKE "%cage%")')
    elif filter_val == 'egg':
        conditions.append('(LOWER(name) LIKE "%egg%" OR LOWER(description) LIKE "%egg%")')
    elif filter_val == 'skins':
        conditions.append('(LOWER(name) LIKE "%skin%" OR LOWER(description) LIKE "%skin%")')

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count matching items
    cursor.execute(f"SELECT COUNT(*) FROM marketplace {where_clause}", params)
    total_matching = cursor.fetchone()[0]

    # Sorting
    if sort_by == 'price_low':
        order_clause = "ORDER BY price ASC, rating DESC"
    elif sort_by == 'price_high':
        order_clause = "ORDER BY price DESC, rating DESC"
    elif sort_by == 'recent':
        order_clause = "ORDER BY creation_date DESC"
    elif sort_by == 'name':
        order_clause = "ORDER BY name ASC"
    else:  # 'rating' / 'popular' default
        order_clause = "ORDER BY CASE WHEN rating IS NULL THEN 1 ELSE 0 END, rating DESC, price DESC"

    offset = (page - 1) * limit
    query = f"SELECT * FROM marketplace {where_clause} {order_clause} LIMIT ? OFFSET ?"
    cursor.execute(query, params + [limit, offset])
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    total_pages = math.ceil(total_matching / limit) if limit > 0 else 1

    return jsonify({
        "success": True,
        "items": rows,
        "total": total_matching,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    })

@app.route('/api/marketplace/<item_id>', methods=['GET'])
def get_marketplace_item(item_id):
    """Returns single authentic marketplace item detail."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM marketplace WHERE id = ? OR LOWER(search_name) = LOWER(?)', (item_id, item_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "error": "Marketplace item not found"}), 404

    return jsonify({"success": True, "item": dict(row)})

@app.route('/api/sync-marketplace', methods=['POST'])
def trigger_sync_marketplace():
    """Trigger an authentic sync of the 900+ Bedrock Marketplace items."""
    try:
        count = sync_cubecraft_marketplace()
        return jsonify({
            "success": True,
            "message": f"Synchronized {count} authentic Bedrock Marketplace items!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------------------------------------------
# Legacy Bundles API (Compatibility Alias)
# ----------------------------------------------------

@app.route('/api/bundles', methods=['GET'])
def get_bundles():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM marketplace WHERE available = 1 ORDER BY rating DESC LIMIT 24')
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "bundles": rows, "items": rows, "total": len(rows)})

@app.route('/api/bundles/<bundle_id>', methods=['GET'])
def get_bundle_detail(bundle_id):
    return get_marketplace_item(bundle_id)

# ----------------------------------------------------
# Playable Medal & Community Clips API
# ----------------------------------------------------

@app.route('/api/clips', methods=['GET'])
def get_clips():
    game = request.args.get('game', 'all')
    clip_type = request.args.get('type', 'all')
    sort = request.args.get('sort', 'recent')
    search = request.args.get('search', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = 'SELECT * FROM clips WHERE 1=1'
    params = []

    if game and game.lower() != 'all':
        query += ' AND LOWER(game) = LOWER(?)'
        params.append(game)

    if clip_type == 'community':
        query += ' AND is_community = 1'
    elif clip_type == 'featured':
        query += ' AND is_community = 0'

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
    """Allows players to submit their own clips with Medal / YouTube / Video support."""
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    gamertag = data.get('gamertag', '').strip()
    game = data.get('game', 'EggWars').strip()
    clip_url = data.get('clip_url', '').strip() or data.get('medal_url', '').strip() or data.get('video_url', '').strip()
    duration = data.get('duration', '0:30').strip()
    description = data.get('description', '').strip()

    if not title or not gamertag:
        return jsonify({"success": False, "error": "Title and Player Gamertag are required"}), 400

    # Auto detect source type
    if 'youtube.com' in clip_url or 'youtu.be' in clip_url:
        source_type = 'youtube'
        medal_url = clip_url
        video_url = clip_url
    elif 'medal.tv' in clip_url:
        source_type = 'medal'
        medal_url = clip_url
        # Reliable fallback video stream for browser playback
        video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
    else:
        source_type = 'direct'
        medal_url = clip_url
        video_url = clip_url if clip_url else "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

    # Default Bedrock game thumbnail
    game_thumbnails = {
        'EggWars': 'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=600&q=80',
        'SkyWars': 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=600&q=80',
        'BlockWars': 'https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=600&q=80',
        'BedWars': 'https://images.unsplash.com/photo-1579373903781-fd5c0c30c4cd?auto=format&fit=crop&w=600&q=80',
        'Lucky Islands': 'https://images.unsplash.com/photo-1538481199705-c710c4e965fc?auto=format&fit=crop&w=600&q=80',
        'Duels (Battle Arena)': 'https://images.unsplash.com/photo-1563089145-599997674d42?auto=format&fit=crop&w=600&q=80'
    }
    thumbnail_url = data.get('thumbnail_url') or game_thumbnails.get(game, 'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=600&q=80')
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clips (title, gamertag, game, medal_url, video_url, thumbnail_url, duration, views, upvotes, is_community, source_type, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, 1, ?, ?, ?)
    ''', (title, gamertag, game, medal_url, video_url, thumbnail_url, duration, source_type, description, now_str))
    new_id = cursor.lastrowid
    conn.commit()

    # Register player if new
    cursor.execute('SELECT gamertag FROM players WHERE LOWER(gamertag) = LOWER(?)', (gamertag,))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO players (gamertag, raw_name, rank_title, avatar_color, bio, first_seen)
            VALUES (?, ?, 'Community Creator', '#00e5ff', 'CubeCraft Bedrock community clip submitter.', ?)
        ''', (gamertag, gamertag, datetime.utcnow().strftime('%Y-%m-%d')))
        conn.commit()

    conn.close()
    return jsonify({
        "success": True,
        "message": f"Community clip '{title}' submitted successfully!",
        "clip_id": new_id
    })

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
    limit = int(request.args.get('limit', 20))
    tag = request.args.get('tag', 'all')

    conn = get_db()
    cursor = conn.cursor()
    query = '''
        SELECT e.*, p.rank_title, p.avatar_color, p.avatar_icon
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
        # Return featured community players when search query is empty
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*,
                   (SELECT COUNT(*) FROM encounters WHERE player_gamertag = p.gamertag) as encounter_count
            FROM players p
            WHERE LOWER(p.gamertag) IN ('mundevpolite', 'joealbadmash')
        ''')
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "players": [dict(r) for r in rows]})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*,
               (SELECT COUNT(*) FROM encounters WHERE player_gamertag = p.gamertag) as encounter_count
        FROM players p
        WHERE LOWER(p.gamertag) LIKE LOWER(?)
        ORDER BY 
            CASE 
                WHEN LOWER(p.gamertag) = 'mundevpolite' THEN 1
                WHEN LOWER(p.gamertag) = 'joealbadmash' THEN 2
                ELSE 3 
            END,
            p.gamertag ASC
        LIMIT 15
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

    # If player is not yet in SQLite, attempt real-time lookup from CubeCraft Bedrock API
    if not player_row:
        external_profile = None
        try:
            req = urllib.request.Request(
                f'https://api.cc-data.ru/bedrock/players/name/{urllib.parse.quote(gamertag)}',
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                external_profile = json.loads(resp.read().decode('utf-8'))
        except Exception:
            pass

        if external_profile and external_profile.get('name'):
            actual_gt = external_profile['name']
            raw_name = external_profile.get('rawName', actual_gt)
            icon = external_profile.get('icon', '')
            rank_title, avatar_color = parse_minecraft_rank(raw_name)

            cursor.execute('''
                INSERT INTO players (gamertag, raw_name, rank_title, avatar_icon, avatar_color, bio, first_seen)
                VALUES (?, ?, ?, ?, ?, 'CubeCraft Bedrock Ranked Player', ?)
            ''', (actual_gt, raw_name, rank_title, icon, avatar_color, datetime.utcnow().strftime('%Y-%m-%d')))
            conn.commit()

            # Insert their external leaderboards
            for lb in external_profile.get('leaderboards', []):
                lb_name = lb.get('name', '')
                g, m = parse_leaderboard_info(lb_name)
                pos = lb.get('position', 1)
                pts = lb.get('points', 0)
                cursor.execute('''
                    INSERT INTO leaderboards (player_gamertag, game, mode, sub_mode_id, points, rank, player_icon, raw_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (actual_gt, g, m, lb_name, pts, pos, icon, raw_name))
            conn.commit()

            cursor.execute('SELECT * FROM players WHERE gamertag = ?', (actual_gt,))
            player_row = cursor.fetchone()

    if not player_row:
        player = {
            "gamertag": gamertag,
            "raw_name": gamertag,
            "rank_title": "Bedrock Player",
            "avatar_icon": None,
            "avatar_color": "#00e5ff",
            "bio": "Minecraft Bedrock adventurer.",
            "first_seen": "Recently Seen",
            "is_new": True
        }
    else:
        player = dict(player_row)
        player['is_new'] = False

    # Fetch player's leaderboard stats
    cursor.execute('SELECT * FROM leaderboards WHERE LOWER(player_gamertag) = LOWER(?) ORDER BY points DESC', (gamertag,))
    leaderboards = [dict(r) for r in cursor.fetchall()]

    # Fetch player encounters
    cursor.execute('''
        SELECT * FROM encounters
        WHERE LOWER(player_gamertag) = LOWER(?) AND reported = 0
        ORDER BY created_at DESC
    ''', (gamertag,))
    encounters = [dict(r) for r in cursor.fetchall()]

    total_encounters = len(encounters)
    positive_count = sum(1 for e in encounters if e['sentiment'] == 'positive')
    avg_rating = round(sum(e['rating'] for e in encounters) / total_encounters, 1) if total_encounters > 0 else 5.0
    
    tag_counts = {}
    for e in encounters:
        t = e['encounter_type']
        tag_counts[t] = tag_counts.get(t, 0) + 1

    badges = []
    if leaderboards:
        best_lb = leaderboards[0]
        badges.append({"name": f"Rank #{best_lb['rank']} in {best_lb['game']}", "icon": "👑", "color": "#fbbf24"})
    if tag_counts.get("God-tier Clutch", 0) >= 1:
        badges.append({"name": "Clutch God", "icon": "⚡", "color": "#00e5ff"})
    if tag_counts.get("Helpful Teammate", 0) >= 1:
        badges.append({"name": "Team Anchor", "icon": "🛡️", "color": "#10b981"})
    if tag_counts.get("Tactical Trapper", 0) >= 1:
        badges.append({"name": "Architect Trapper", "icon": "🕸️", "color": "#f59e0b"})
    if tag_counts.get("Sweaty Opponent", 0) >= 1:
        badges.append({"name": "High ELO Threat", "icon": "🔥", "color": "#f43f5e"})
    if not badges and total_encounters > 0:
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

    cursor.execute('SELECT * FROM players WHERE LOWER(gamertag) = LOWER(?)', (gamertag,))
    player_row = cursor.fetchone()
    if not player_row:
        colors = ["#00e5ff", "#38bdf8", "#10b981", "#fbbf24", "#a855f7", "#f43f5e"]
        chosen_color = colors[len(gamertag) % len(colors)]
        cursor.execute('''
            INSERT INTO players (gamertag, raw_name, rank_title, avatar_color, bio, first_seen)
            VALUES (?, ?, 'Bedrock Player', ?, 'Discovered in Bedrock lobby.', ?)
        ''', (gamertag.strip(), gamertag.strip(), chosen_color, datetime.utcnow().strftime('%Y-%m-%d')))
        player_actual_tag = gamertag.strip()
    else:
        player_actual_tag = player_row['gamertag']

    cursor.execute('''
        INSERT INTO encounters (player_gamertag, reviewer_name, game_played, encounter_type, sentiment, rating, comment, helpful_votes, reported, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
    ''', (player_actual_tag, reviewer_name, game_played, encounter_type, sentiment, rating, comment, now_str))

    cursor.execute('SELECT sentiment FROM encounters WHERE LOWER(player_gamertag) = LOWER(?) AND reported = 0', (gamertag,))
    all_sentiments = [row['sentiment'] for row in cursor.fetchall()]
    total = len(all_sentiments)
    positives = sum(1 for s in all_sentiments if s == 'positive')
    neutrals = sum(1 for s in all_sentiments if s == 'neutral')
    negatives = sum(1 for s in all_sentiments if s == 'negative')

    if total > 0:
        new_score = max(10, min(100, int((positives * 100 + neutrals * 75 + negatives * 20) / total)))
    else:
        new_score = 100

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

# ----------------------------------------------------
# Official Bedrock Mode & Maps Strategy Guide API
# ----------------------------------------------------

@app.route('/api/strategy/maps', methods=['GET'])
def get_strategy_maps():
    """Returns authentic Bedrock map blueprints, optionally filtered by ?game=EggWars|SkyWars."""
    game = request.args.get('game', None)
    maps = get_all_maps_strategy(game)
    return jsonify({
        "success": True,
        "count": len(maps),
        "maps": maps
    })

@app.route('/api/strategy/maps/<map_id>', methods=['GET'])
def get_strategy_map_detail(map_id):
    """Returns complete tactical blueprint for a specific map."""
    map_data = get_map_strategy_detail(map_id)
    if not map_data:
        return jsonify({"success": False, "error": f"Map '{map_id}' not found"}), 404
    return jsonify({
        "success": True,
        "map": map_data
    })

@app.route('/api/strategy/schematic/<map_id>', methods=['GET'])
def get_strategy_map_schematic(map_id):
    """Returns the top-down 2D vector schematic (islands, coordinates, rush vectors) for a map."""
    map_data = get_map_strategy_detail(map_id)
    if not map_data:
        return jsonify({"success": False, "error": f"Map '{map_id}' not found"}), 404
    return jsonify({
        "success": True,
        "map_id": map_id,
        "name": map_data.get('name'),
        "game": map_data.get('game'),
        "schematic_2d": map_data.get('schematic_2d')
    })

@app.route('/api/strategy/generators', methods=['GET'])
def get_strategy_generators():
    """Returns official CubeCraft Bedrock generator upgrade costs and timer parameters."""
    gens = get_generator_tiers_data()
    return jsonify({
        "success": True,
        "generators": gens
    })

@app.route('/api/strategy/bridging-benchmarks', methods=['GET'])
def get_strategy_bridging_benchmarks():
    """Returns void bridging distances, sprint jump-bridging timings, and block requirements."""
    benchmarks_data = get_bridging_benchmarks_data()
    return jsonify({
        "success": True,
        **benchmarks_data
    })

@app.route('/api/strategy/overview', methods=['GET'])
def get_strategy_overview():
    """Bundles maps, generator tiers, and bridging benchmarks for unified UI initialization."""
    maps = get_all_maps_strategy()
    gens = get_generator_tiers_data()
    benchmarks = get_bridging_benchmarks_data()
    return jsonify({
        "success": True,
        "maps": maps,
        "generators": gens,
        "bridging": benchmarks
    })

# ----------------------------------------------------
# Discord Rich Embed / Webhook Exporter API
# ----------------------------------------------------

@app.route('/api/discord/export/player/<gamertag>', methods=['GET'])
def export_discord_player(gamertag):
    """Generates official Discord Rich Embed & Webhook payload for any player."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM players WHERE LOWER(gamertag) = LOWER(?)', (gamertag.strip(),))
    p_row = cursor.fetchone()

    if not p_row:
        conn.close()
        return jsonify({"success": False, "error": f"Player '{gamertag}' not found."}), 404

    player_data = dict(p_row)

    # Fetch top leaderboards
    cursor.execute('''
        SELECT game, mode, rank, points
        FROM leaderboards
        WHERE LOWER(player_gamertag) = LOWER(?)
        ORDER BY points DESC
    ''', (gamertag.strip(),))
    player_data['leaderboards'] = [dict(lr) for lr in cursor.fetchall()]

    # Fetch encounters
    cursor.execute('SELECT sentiment FROM encounters WHERE LOWER(player_gamertag) = LOWER(?) AND reported = 0', (gamertag.strip(),))
    encounters = [dict(er) for er in cursor.fetchall()]
    conn.close()

    result = build_player_discord_embed(player_data, encounters)
    return jsonify({
        "success": True,
        "type": "player",
        "target": player_data['gamertag'],
        **result
    })

@app.route('/api/discord/export/leaderboard', methods=['GET'])
def export_discord_leaderboard():
    """Generates Discord Rich Embed celebrating current #1 leaderboard holder."""
    game = request.args.get('game', 'EggWars')
    mode = request.args.get('mode', 'Solo')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT player_gamertag, game, mode, points, rank
        FROM leaderboards
        WHERE LOWER(game) = LOWER(?) AND LOWER(mode) = LOWER(?)
        ORDER BY rank ASC, points DESC
        LIMIT 2
    ''', (game.strip(), mode.strip()))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({"success": False, "error": f"No leaderboard entries found for {game} ({mode})."}), 404

    rank1 = dict(rows[0])
    rank2 = dict(rows[1]) if len(rows) > 1 else None

    result = build_leaderboard_champion_discord_embed(game, mode, rank1, rank2)
    return jsonify({
        "success": True,
        "type": "leaderboard",
        "game": game,
        "mode": mode,
        **result
    })

@app.route('/api/discord/export/server', methods=['GET'])
def export_discord_server():
    """Generates Discord Rich Embed for live server status and grinding schedule."""
    online = get_live_online_count()
    tracker_stats = get_server_tracker_stats()
    peak = tracker_stats.get('peak_window', '16:00 - 21:00 UTC')
    offpeak = tracker_stats.get('offpeak_window', '04:00 - 08:00 UTC')

    result = build_server_status_discord_embed(online, peak, offpeak)
    return jsonify({
        "success": True,
        "type": "server",
        "online_count": online,
        **result
    })

@app.route('/api/discord/export/map/<map_id>', methods=['GET'])
def export_discord_map(map_id):
    """Generates Discord Rich Embed for map tactics and void bridging benchmarks."""
    map_data = get_map_strategy_detail(map_id)
    if not map_data:
        return jsonify({"success": False, "error": f"Map '{map_id}' not found."}), 404

    result = build_map_tactics_discord_embed(map_data)
    return jsonify({
        "success": True,
        "type": "map",
        "map_id": map_id,
        **result
    })

@app.route('/api/discord/send-webhook', methods=['POST'])
def handle_send_discord_webhook():
    """Proxies and sends payload to an official Discord Webhook URL."""
    body = request.get_json(silent=True) or {}
    webhook_url = body.get('webhook_url', '').strip()
    payload = body.get('payload', {})

    if not webhook_url:
        return jsonify({"success": False, "error": "Discord Webhook URL is required."}), 400

    result = send_discord_webhook(webhook_url, payload)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5055))
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"CubeCraft Bedrock Community Hub starting on http://0.0.0.0:{port} (debug={debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
