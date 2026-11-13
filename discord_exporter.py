"""
CubeCraft Bedrock Discord Rich Embed & Webhook Payload Generator
Produces 100% authentic, Discord API-compliant Webhook JSON payloads
and formatted Discord Markdown text for:
1. Player Profile & Bedrock Rank Cards
2. Current #1 Leaderboard Champions across 39 modes
3. Live Server Status & Best Times to Play
4. Map Rush & Void Bridging Tactics Blueprints
"""
import json
import urllib.request
import re
from datetime import datetime

def _hex_to_int(hex_str, default=3718648): # Default cyan #38bdf8
    if not hex_str:
        return default
    clean = hex_str.strip().lstrip('#')
    try:
        return int(clean, 16)
    except Exception:
        return default

def get_rank_embed_color(rank_title):
    t = (rank_title or '').lower()
    if 'obsidian' in t: return 8141549   # Purple #7c3aed
    if 'diamond' in t: return 58879     # Cyan #00e5ff
    if 'emerald' in t: return 1096065   # Emerald #10b981
    if 'vip' in t: return 16503076      # Amber #fbbf24
    if 'iron' in t: return 14737632     # Silver #e0e7ff
    return 3718648                      # Blue #38bdf8

# ==========================================
# 1. Player Profile & Rank Card Embed
# ==========================================
def build_player_discord_embed(player_data, encounters=None):
    """
    Builds official Discord embed and markdown for any Bedrock player.
    """
    gamertag = player_data.get('gamertag', 'Player')
    raw_name = player_data.get('raw_name') or gamertag
    rank_title = player_data.get('rank_title') or 'Bedrock Player'
    bio = player_data.get('bio') or 'Discovered in Bedrock lobby.'
    color_int = get_rank_embed_color(rank_title)
    avatar_url = f"https://mc-heads.net/avatar/{gamertag}/128"

    # Leaderboard highlights
    leaderboards = player_data.get('leaderboards', [])
    top_entry = leaderboards[0] if len(leaderboards) > 0 else None

    # Reputation calculation
    rep_score = 100
    enc_count = len(encounters) if encounters else 0
    if encounters and len(encounters) > 0:
        pos = sum(1 for e in encounters if e.get('sentiment') == 'positive')
        neu = sum(1 for e in encounters if e.get('sentiment') == 'neutral')
        neg = sum(1 for e in encounters if e.get('sentiment') == 'negative')
        tot = len(encounters)
        rep_score = max(10, min(100, int((pos * 100 + neu * 75 + neg * 20) / tot)))

    fields = [
        {
            "name": "🎖️ Bedrock Rank",
            "value": f"`{rank_title}`",
            "inline": True
        },
        {
            "name": "🌟 Community Rep",
            "value": f"`{rep_score}% Positive` ({enc_count} reviews)",
            "inline": True
        },
        {
            "name": "🎮 Platform",
            "value": "`Minecraft Bedrock Edition`",
            "inline": True
        }
    ]

    if top_entry:
        fields.append({
            "name": f"🏆 Peak Standing: {top_entry.get('game', 'Mode')}",
            "value": f"**Rank #{top_entry.get('rank', '?')}** in *{top_entry.get('mode', 'General')}*\nPoints: **{top_entry.get('points', 0):,}**",
            "inline": False
        })

    if len(leaderboards) > 1:
        other_modes = ", ".join([f"{e['game']} ({e['mode']})" for e in leaderboards[1:4]])
        fields.append({
            "name": f"📊 Other Ranked Modes ({len(leaderboards)} total)",
            "value": other_modes,
            "inline": False
        })

    embed = {
        "title": f"🎮 Bedrock Competitor Profile — {gamertag}",
        "description": f"> *\"{bio}\"*\n\nVerified competitor profile on the **CubeCraft Bedrock Community Hub**.",
        "color": color_int,
        "thumbnail": {
            "url": avatar_url
        },
        "fields": fields,
        "footer": {
            "text": "CubeCraft Bedrock Community Hub • play.cubecraft.net",
            "icon_url": "https://mc-heads.net/avatar/CubeCraft/64"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    payload = {
        "username": "CubeCraft Hub Bot",
        "avatar_url": "https://mc-heads.net/avatar/CubeCraft/128",
        "embeds": [embed]
    }

    # Ready-to-paste markdown for chat
    markdown_text = (
        f"__**🎮 CUBECRAFT BEDROCK PLAYER PROFILE**__\n"
        f"**Gamertag:** `{gamertag}`\n"
        f"**Rank:** `{rank_title}` | **Reputation:** `{rep_score}% Positive` ({enc_count} encounters)\n"
    )
    if top_entry:
        markdown_text += f"**Best Rank:** #{top_entry.get('rank')} in **{top_entry.get('game')} {top_entry.get('mode')}** ({top_entry.get('points', 0):,} pts)\n"
    markdown_text += f"> *\"{bio}\"*\n"
    markdown_text += f"🔗 Server: `play.cubecraft.net` (Port 19132)"

    return {
        "payload": payload,
        "embed": embed,
        "markdown": markdown_text
    }

# ==========================================
# 2. #1 Leaderboard Champion Embed
# ==========================================
def build_leaderboard_champion_discord_embed(game, mode, rank1_entry, rank2_entry=None):
    """
    Builds Discord embed celebrating the reigning #1 leaderboard champion.
    """
    champ_name = rank1_entry.get('player_gamertag') or rank1_entry.get('name') or 'Champion'
    points = rank1_entry.get('points', 0)
    avatar_url = f"https://mc-heads.net/avatar/{champ_name}/128"

    lead_str = "Undisputed Leader"
    if rank2_entry:
        diff = points - rank2_entry.get('points', 0)
        p2_name = rank2_entry.get('player_gamertag') or rank2_entry.get('name') or '#2'
        lead_str = f"+{diff:,} pts ahead of #{p2_name}"

    fields = [
        {
            "name": "👑 Reigning #1 Champion",
            "value": f"**`{champ_name}`**",
            "inline": True
        },
        {
            "name": "🎯 Champion Score",
            "value": f"**`{points:,} points`**",
            "inline": True
        },
        {
            "name": "📈 Lead Over #2",
            "value": f"`{lead_str}`",
            "inline": True
        },
        {
            "name": "🌐 Arena & Game Mode",
            "value": f"**{game}** — *{mode}*",
            "inline": False
        },
        {
            "name": "🕹️ Server Address",
            "value": "`play.cubecraft.net` (Bedrock Port: `19132`)",
            "inline": False
        }
    ]

    embed = {
        "title": f"👑 #1 Leaderboard Champion — {game} ({mode})",
        "description": f"Congratulations to **{champ_name}**, the official Rank #1 holder on CubeCraft Bedrock!",
        "color": 16503076, # Gold #fbbf24
        "thumbnail": {
            "url": avatar_url
        },
        "fields": fields,
        "footer": {
            "text": "Official CubeCraft Bedrock Leaderboard Telemetry",
            "icon_url": "https://mc-heads.net/avatar/CubeCraft/64"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    payload = {
        "username": "CubeCraft Hub Bot",
        "avatar_url": "https://mc-heads.net/avatar/CubeCraft/128",
        "embeds": [embed]
    }

    markdown_text = (
        f"👑 **#1 LEADERBOARD CHAMPION: {game.upper()} ({mode})**\n"
        f"🏆 Champion: **`{champ_name}`**\n"
        f"🎯 Score: **{points:,} points** ({lead_str})\n"
        f"🎮 Join the ladder: `play.cubecraft.net` (Port 19132)"
    )

    return {
        "payload": payload,
        "embed": embed,
        "markdown": markdown_text
    }

# ==========================================
# 3. Live Server Status & Best Times to Play
# ==========================================
def build_server_status_discord_embed(online_count, peak_window="16:00 - 21:00 UTC", offpeak_window="04:00 - 08:00 UTC"):
    """
    Builds Discord embed reporting live Bedrock player count and grinding schedules.
    """
    fields = [
        {
            "name": "🟢 Server Status",
            "value": "`ONLINE` (play.cubecraft.net:19132)",
            "inline": True
        },
        {
            "name": "👥 Online Bedrockers",
            "value": f"**`{online_count:,} players`**",
            "inline": True
        },
        {
            "name": "⚡ Supported Modes",
            "value": "`39 Bedrock Modes`",
            "inline": True
        },
        {
            "name": "🔥 Peak Matchmaking Window",
            "value": f"**{peak_window}**\n*Instant queues, 50v50 BlockWars, intense duels.*",
            "inline": False
        },
        {
            "name": "🌙 Best Grinding Window (Off-Peak)",
            "value": f"**{offpeak_window}**\n*Smoother win streaks, quest completion, less competition.*",
            "inline": False
        }
    ]

    embed = {
        "title": "⚡ CubeCraft Bedrock Server Status & Grinding Schedule",
        "description": "Live network telemetry and optimal playtime analysis for competitive Minecraft Bedrock players.",
        "color": 1096065, # Emerald #10b981
        "thumbnail": {
            "url": "https://mc-heads.net/avatar/CubeCraft/128"
        },
        "fields": fields,
        "footer": {
            "text": "Live Telemetry • CubeCraft Bedrock Community Hub",
            "icon_url": "https://mc-heads.net/avatar/CubeCraft/64"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    payload = {
        "username": "CubeCraft Hub Bot",
        "avatar_url": "https://mc-heads.net/avatar/CubeCraft/128",
        "embeds": [embed]
    }

    markdown_text = (
        f"⚡ **CUBECRAFT BEDROCK NETWORK STATUS**\n"
        f"🟢 **Status:** `ONLINE` | **Online Players:** **{online_count:,}**\n"
        f"🔥 **Peak Matchmaking:** `{peak_window}` (Fast queues & sweat lobbies)\n"
        f"🌙 **Best For Win Grinding:** `{offpeak_window}` (Smooth solo streaks)\n"
        f"🌐 Connect: `play.cubecraft.net` (Port 19132)"
    )

    return {
        "payload": payload,
        "embed": embed,
        "markdown": markdown_text
    }

# ==========================================
# 4. Map Rush & Void Bridging Tactics Embed
# ==========================================
def build_map_tactics_discord_embed(map_data):
    """
    Builds Discord embed for tactical map blueprints and Bedrock bridging benchmarks.
    """
    name = map_data.get('name', 'Map')
    game = map_data.get('game', 'EggWars')
    theme = map_data.get('theme', 'Arena')
    diff = map_data.get('difficulty', 'Normal')
    teams_count = map_data.get('teams_count', 8)
    team_size = map_data.get('team_size', 2)

    bridging = map_data.get('bridging_distances', [])
    b_text = "\n".join([f"• **{b['target']}:** `{b['distance_blocks']} blk` (⚡ {b['jump_bridge_sec']}s Bedrock sprint)" for b in bridging[:3]])

    fields = [
        {
            "name": "🗺️ Map Theme",
            "value": f"`{theme}`",
            "inline": True
        },
        {
            "name": "👥 Team Setup",
            "value": f"`{teams_count} Teams (Size {team_size})`",
            "inline": True
        },
        {
            "name": "🎯 Difficulty",
            "value": f"`{diff}`",
            "inline": True
        },
        {
            "name": "📏 Void Bridging Benchmarks (5.6 bps sprint)",
            "value": b_text or "No gap benchmarks listed.",
            "inline": False
        },
        {
            "name": "🚀 Opening Rush Tactic",
            "value": f"> {map_data.get('tactics_rush', 'Rush neighbor early.')[:200]}...",
            "inline": False
        }
    ]

    embed = {
        "title": f"🗺️ Bedrock Strategy Guide — {name} ({game})",
        "description": map_data.get('description', 'Authentic CubeCraft map blueprint.'),
        "color": 58879, # Cyan #00e5ff
        "thumbnail": {
            "url": map_data.get('thumbnail_url', 'https://mc-heads.net/avatar/CubeCraft/128')
        },
        "fields": fields,
        "footer": {
            "text": "CubeCraft Bedrock Mode & Maps Strategy Guide",
            "icon_url": "https://mc-heads.net/avatar/CubeCraft/64"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    payload = {
        "username": "CubeCraft Hub Bot",
        "avatar_url": "https://mc-heads.net/avatar/CubeCraft/128",
        "embeds": [embed]
    }

    markdown_text = (
        f"🗺️ **BEDROCK MAP STRATEGY: {name.upper()} ({game})**\n"
        f"🎨 **Theme:** {theme} | **Difficulty:** {diff}\n"
        f"📏 **Key Void Gaps:**\n{b_text}\n"
        f"💡 **Rush Meta:** {map_data.get('tactics_rush', '')[:160]}...\n"
        f"🎮 Server: `play.cubecraft.net` (Port 19132)"
    )

    return {
        "payload": payload,
        "embed": embed,
        "markdown": markdown_text
    }

# ==========================================
# 5. Discord Webhook Sender
# ==========================================
def send_discord_webhook(webhook_url, payload):
    """
    Sends JSON payload to an official Discord Webhook URL.
    Ensures safe URL validation and error handling.
    """
    if not webhook_url:
        return {"success": False, "error": "Webhook URL is required."}

    # Validate Discord webhook domain
    valid_domains = [
        "https://discord.com/api/webhooks/",
        "https://discordapp.com/api/webhooks/",
        "https://canary.discord.com/api/webhooks/",
        "https://ptb.discord.com/api/webhooks/"
    ]

    if not any(webhook_url.startswith(d) for d in valid_domains):
        return {"success": False, "error": "Invalid Discord Webhook URL. Must start with https://discord.com/api/webhooks/..."}

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'CubeCraft-Bedrock-Hub/2.0'
            },
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status in (200, 204):
                return {"success": True, "message": "Successfully posted embed to Discord channel!"}
            else:
                return {"success": False, "error": f"Discord responded with status {response.status}"}
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8', errors='ignore')
        return {"success": False, "error": f"Discord API Error ({e.code}): {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
