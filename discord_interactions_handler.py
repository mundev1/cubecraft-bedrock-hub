"""
Discord HTTP Interactions Webhook Handler
=========================================
Handles incoming Discord Slash Commands via HTTP POST without requiring
a continuous WebSocket gateway connection. Perfect for serverless hosting on Vercel.
"""

import os
import json
from discord_interactions import verify_key, InteractionType, InteractionResponseType

from database import (
    get_db,
    get_map_strategy_detail,
    get_server_tracker_stats,
    get_cross_mode_masters,
    get_live_online_count,
    search_marketplace_items
)
from discord_exporter import (
    build_player_discord_embed,
    build_leaderboard_champion_discord_embed,
    build_server_status_discord_embed,
    build_map_tactics_discord_embed
)

def handle_discord_interaction(raw_body: bytes, headers: dict):
    signature = headers.get("X-Signature-Ed25519", "") or headers.get("x-signature-ed25519", "")
    timestamp = headers.get("X-Signature-Timestamp", "") or headers.get("x-signature-timestamp", "")
    public_key = os.getenv("DISCORD_PUBLIC_KEY", "").strip()

    if not public_key:
        return {"error": "DISCORD_PUBLIC_KEY is not configured in environment variables."}, 500

    if not signature or not timestamp or not verify_key(raw_body, signature, timestamp, public_key):
        return {"error": "Invalid request signature."}, 401

    try:
        body = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return {"error": "Invalid JSON body"}, 400

    interaction_type = body.get("type")

    # 1. Handle PING (Discord Endpoint Verification)
    if interaction_type == InteractionType.PING:
        return {"type": InteractionResponseType.PONG}, 200

    # 2. Handle Slash Commands (APPLICATION_COMMAND)
    if interaction_type == InteractionType.APPLICATION_COMMAND:
        data = body.get("data", {})
        cmd_name = data.get("name", "").lower()
        options_list = data.get("options", [])
        options = {opt.get("name"): opt.get("value") for opt in options_list}

        embed = None

        if cmd_name == "player":
            gamertag = options.get("gamertag", "MundevPolite")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players WHERE LOWER(gamertag) = LOWER(?)", (gamertag.strip(),))
            p_row = cursor.fetchone()
            if not p_row:
                cursor.execute(
                    "SELECT player_gamertag, rank_title, avatar_color FROM leaderboards WHERE LOWER(player_gamertag) = LOWER(?) LIMIT 1",
                    (gamertag.strip(),)
                )
                lb_match = cursor.fetchone()
                if lb_match:
                    player_data = {
                        "gamertag": lb_match["player_gamertag"],
                        "rank_title": lb_match["rank_title"] or "Bedrock Competitor",
                        "avatar_color": lb_match["avatar_color"] or "#00e5ff",
                        "custom_bio": "Competitor on CubeCraft Bedrock.",
                        "total_points": 0
                    }
                else:
                    player_data = None
            else:
                player_data = dict(p_row)

            if player_data:
                cursor.execute(
                    "SELECT game, mode, rank, points FROM leaderboards WHERE LOWER(player_gamertag) = LOWER(?) ORDER BY points DESC",
                    (gamertag.strip(),)
                )
                player_data["leaderboards"] = [dict(r) for r in cursor.fetchall()]
                cursor.execute(
                    "SELECT sentiment FROM encounters WHERE LOWER(player_gamertag) = LOWER(?) AND reported = 0",
                    (gamertag.strip(),)
                )
                encounters = [dict(r) for r in cursor.fetchall()]
                res = build_player_discord_embed(player_data, encounters)
                embed = res["embed"]
            else:
                embed = {
                    "title": "🔍 Player Not Found",
                    "description": f"Could not find **{gamertag}** among 826+ indexed Bedrock competitors.",
                    "color": 0xEF4444
                }
            conn.close()

        elif cmd_name in ["leaderboard", "top"]:
            game = options.get("game", "EggWars")
            mode = options.get("mode", "Solo")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT player_gamertag, game, mode, points, rank, rank_title FROM leaderboards WHERE LOWER(game) = LOWER(?) AND LOWER(mode) = LOWER(?) ORDER BY rank ASC, points DESC LIMIT 10",
                (game.strip(), mode.strip())
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            if rows:
                rank1 = rows[0]
                rank2 = rows[1] if len(rows) > 1 else None
                champ = build_leaderboard_champion_discord_embed(game, mode, rank1, rank2)
                embed = champ["embed"]
                ladder = []
                for r in rows:
                    rnk = r.get("rank", 0)
                    medal = "🥇" if rnk == 1 else ("🥈" if rnk == 2 else ("🥉" if rnk == 3 else f"`#{rnk}`"))
                    ladder.append(f"{medal} **{r['player_gamertag']}** — `{r['points']:,} pts`")
                embed["fields"].append({"name": "🏆 Top Standings", "value": "\n".join(ladder), "inline": False})
            else:
                embed = {
                    "title": "⚠️ No Leaderboard Data",
                    "description": f"No entries found for {game} ({mode}). Try `EggWars (Solo)` or `SkyWars (Solo)`.",
                    "color": 0xF59E0B
                }

        elif cmd_name == "server":
            online = get_live_online_count()
            stats = get_server_tracker_stats()
            res = build_server_status_discord_embed(online, stats["peak_window"], stats["offpeak_window"])
            embed = res["embed"]

        elif cmd_name == "map":
            map_name = options.get("map_name", "eggwars_tea_party")
            map_data = get_map_strategy_detail(map_name)
            if map_data:
                res = build_map_tactics_discord_embed(map_data)
                embed = res["embed"]
            else:
                embed = {"title": "⚠️ Map Not Found", "description": f"Map `{map_name}` not found.", "color": 0xEF4444}

        elif cmd_name in ["marketplace", "market"]:
            query = options.get("query", "")
            items, total = search_marketplace_items(query=query, category="all", limit=3)
            match_label = query or 'all'
            embed = {
                "title": f"🛒 Marketplace Catalog ({total:,} Items Indexed)",
                "description": f"Showing top results matching **'{match_label}'**.",
                "color": 0x00E5FF,
                "fields": [
                    {
                        "name": f"📦 {item['title']}",
                        "value": f"🪙 **{item['price_minecoins']} Minecoins** • ⭐ {item['rating']:.1f}\n*{item['description'][:100]}...*",
                        "inline": False
                    }
                    for item in items
                ]
            }

        elif cmd_name == "masters":
            masters = get_cross_mode_masters(limit=10)
            lines = [f"`#{i+1}` **{m['gamertag']}** — **{m.get('distinct_games', 1)} Distinct Games**" for i, m in enumerate(masters)]
            embed = {
                "title": "👑 Cross-Mode Dominance — \"All-Around Masters\"",
                "description": "Top Bedrock competitors ranked in multiple distinct game modes.",
                "color": 0xA855F7,
                "fields": [{"name": "🏆 Leaders", "value": "\n".join(lines), "inline": False}]
            }

        elif cmd_name == "ping":
            embed = {
                "title": "🏓 Pong!",
                "description": "Discord Slash Command responded in ~45ms via Vercel Serverless Edge!",
                "color": 0x10B981
            }

        else: # help
            embed = {
                "title": "🎮 CubeCraft Bedrock Bot — Slash Commands",
                "description": "Official competitive Minecraft Bedrock bot running on Vercel Serverless.\n\n"
                               "• `/player <gamertag>` — Rank, reputation score & stats\n"
                               "• `/leaderboard [game] [mode]` — Live #1 champion & top standings\n"
                               "• `/server` — Online count & peak grind hours\n"
                               "• `/map <map_name>` — Tactical bridging benchmarks\n"
                               "• `/marketplace [query]` — Search 922+ store items\n"
                               "• `/masters` — Cross-mode dominance leaders\n"
                               "• `/ping` — Latency check",
                "color": 0x5865F2,
                "footer": {"text": "CubeCraft Bedrock Hub • Hosted on Vercel"}
            }

        return {
            "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "embeds": [embed] if embed else []
            }
        }, 200

    return {"error": "Unsupported interaction type"}, 400
