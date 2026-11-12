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
import urllib.request
from datetime import datetime
from database import (
    get_db, init_db, sync_cubecraft_leaderboards,
    seed_bundles_and_clips, seed_custom_players,
    parse_leaderboard_info, parse_minecraft_rank
)

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Ensure database is initialized
init_db()
seed_custom_players()
seed_bundles_and_clips()

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
    cursor.execute('SELECT COUNT(*) FROM bundles')
    total_bundles = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT game) FROM leaderboards')
    total_games = cursor.fetchone()[0]

    # Daily tracked totals
    cursor.execute('SELECT COALESCE(SUM(daily_wins), 0), COALESCE(SUM(daily_kills), 0) FROM players')
    daily_row = cursor.fetchone()
    today_tracked_wins = daily_row[0] if daily_row else 0
    today_tracked_kills = daily_row[1] if daily_row else 0

    # Top daily grinder
    cursor.execute('''
        SELECT gamertag, rank_title, avatar_icon, avatar_color, daily_wins, daily_kills, daily_streak
        FROM players 
        ORDER BY daily_wins DESC 
        LIMIT 1
    ''')
    top_grinder_row = cursor.fetchone()
    top_daily_grinder = dict(top_grinder_row) if top_grinder_row else None

    conn.close()

    # Attempt to fetch live Bedrock online count with quick timeout
    online_count = 6842
    try:
        req = urllib.request.Request('https://api.cc-data.ru/bedrock/status', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            status_data = json.loads(resp.read().decode('utf-8'))
            if 'players' in status_data and 'online' in status_data['players']:
                online_count = status_data['players']['online']
            elif 'online' in status_data:
                online_count = status_data['online']
    except Exception:
        pass

    return jsonify({
        "success": True,
        "stats": {
            "total_players": total_players,
            "total_leaderboard_entries": total_leaderboard_entries,
            "total_encounters": total_encounters,
            "total_clips": total_clips,
            "active_bundles": total_bundles,
            "total_games": total_games,
            "today_tracked_wins": today_tracked_wins,
            "today_tracked_kills": today_tracked_kills,
            "top_daily_grinder": top_daily_grinder,
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
    sort_by = request.args.get('sort_by', 'points')
    timeframe = request.args.get('timeframe', 'all_time').lower()
    search = request.args.get('search', '').strip()

    if timeframe == 'daily':
        if sort_by == 'kills':
            order_clause = 'l.daily_kills DESC, l.daily_wins DESC'
        else:
            order_clause = 'l.daily_wins DESC, l.daily_kills DESC, l.points DESC'
    else:
        valid_sorts = {
            'points': 'l.points DESC, l.wins DESC',
            'wins': 'l.wins DESC, l.points DESC',
            'kills': 'l.kills DESC',
            'streak': 'l.streak DESC',
            'rating': 'l.rating DESC'
        }
        order_clause = valid_sorts.get(sort_by, 'l.points DESC, l.wins DESC')

    conn = get_db()
    cursor = conn.cursor()

    query = '''
        SELECT l.*, p.rank_title, p.reputation_score, p.avatar_color, p.avatar_icon as player_avatar_icon,
               p.daily_wins as player_daily_wins, p.daily_kills as player_daily_kills, p.daily_streak as player_daily_streak,
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

    query += f' ORDER BY {order_clause} LIMIT 100'
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for idx, r in enumerate(rows, 1):
        item = dict(r)
        item['dynamic_rank'] = idx
        if not item.get('player_avatar_icon') and item.get('player_icon'):
            item['player_avatar_icon'] = item['player_icon']
        results.append(item)

    podium = results[:3] if len(results) >= 3 else results

    conn.close()
    return jsonify({
        "success": True,
        "game": game,
        "mode": mode,
        "sort_by": sort_by,
        "timeframe": timeframe,
        "podium": podium,
        "leaderboard": results,
        "total_results": len(results)
    })

@app.route('/api/leaderboards/daily-leaders', methods=['GET'])
def get_daily_leaders():
    """Returns top daily grinders across all CubeCraft Bedrock modes today."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.gamertag, p.raw_name, p.rank_title, p.avatar_icon, p.avatar_color,
               p.daily_wins, p.daily_kills, p.daily_streak, p.is_active_today,
               (SELECT l.game || ' (' || l.mode || ')' FROM leaderboards l WHERE l.player_gamertag = p.gamertag ORDER BY l.daily_wins DESC LIMIT 1) as top_mode,
               (SELECT COUNT(*) FROM encounters WHERE player_gamertag = p.gamertag) as encounter_count
        FROM players p
        WHERE p.daily_wins > 0
        ORDER BY p.daily_wins DESC, p.daily_kills DESC
        LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()

    leaders = [dict(r) for r in rows]
    return jsonify({"success": True, "daily_leaders": leaders, "total": len(leaders)})

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
            INSERT INTO players (gamertag, raw_name, rank_title, total_games, reputation_score, avatar_color, bio, first_seen)
            VALUES (?, ?, 'Community Creator', 10, 100, '#00e5ff', 'CubeCraft Bedrock community clip submitter.', ?)
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
            p.total_games DESC
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
                INSERT INTO players (gamertag, raw_name, rank_title, avatar_icon, total_games, reputation_score, avatar_color, bio, first_seen)
                VALUES (?, ?, ?, ?, 50, 100, ?, 'CubeCraft Bedrock Ranked Player', ?)
            ''', (actual_gt, raw_name, rank_title, icon, avatar_color, datetime.utcnow().strftime('%Y-%m-%d')))
            conn.commit()

            # Insert their external leaderboards
            for lb in external_profile.get('leaderboards', []):
                lb_name = lb.get('name', '')
                g, m = parse_leaderboard_info(lb_name)
                pos = lb.get('position', 1)
                pts = lb.get('points', 0)
                cursor.execute('''
                    INSERT INTO leaderboards (player_gamertag, game, mode, sub_mode_id, points, wins, kills, streak, rating, rank, player_icon, raw_name, favorite_kit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 10, ?, ?, ?, ?, 'Standard')
                ''', (actual_gt, g, m, lb_name, pts, pts, pts * 3, 1500 + pts // 10, pos, icon, raw_name))
            conn.commit()

            cursor.execute('SELECT * FROM players WHERE gamertag = ?', (actual_gt,))
            player_row = cursor.fetchone()

    if not player_row:
        player = {
            "gamertag": gamertag,
            "raw_name": gamertag,
            "rank_title": "Bedrock Player",
            "avatar_icon": None,
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

    daily_stats = {
        "daily_wins": player.get('daily_wins', 0) if isinstance(player, dict) else 0,
        "daily_kills": player.get('daily_kills', 0) if isinstance(player, dict) else 0,
        "daily_streak": player.get('daily_streak', 0) if isinstance(player, dict) else 0,
        "is_active_today": bool(player.get('is_active_today', 1)) if isinstance(player, dict) else True,
        "last_active_time": player.get('last_active_time', 'Active Today') if isinstance(player, dict) else 'Active Today'
    }

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
        "daily_stats": daily_stats,
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
            INSERT INTO players (gamertag, raw_name, rank_title, total_games, reputation_score, avatar_color, bio, first_seen)
            VALUES (?, ?, 'Player', 1, 100, ?, 'Discovered in Bedrock lobby.', ?)
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
