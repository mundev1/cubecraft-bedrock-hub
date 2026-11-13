#!/usr/bin/env python3
"""
CubeCraft Bedrock Community Hub — Official Discord Bot
======================================================
Full-featured Discord Bot with Slash Commands & Prefix Commands powered by the
authentic CubeCraft Bedrock database (826+ ranked players, 39 game modes,
922+ marketplace items, tactical map schematics, and live server telemetry).

Commands:
  /player <gamertag>              - Official Bedrock competitor stats, rank tier, rep & skin
  /leaderboard [game] [mode]      - Live official leaderboard & #1 champion point lead
  /server                         - Real-time online Bedrock player count & peak grinding hours
  /map <name>                     - Tactical map blueprints, void jump-bridge timings & gens
  /marketplace [query] [category] - Search 922+ authentic Bedrock marketplace items with prices
  /review <gt> <sentiment> <story>- Log an encounter review for a player & update their rep score
  /encounters <gamertag>          - View community reviews for a competitor
  /masters                        - Cross-Mode Dominance leaderboard (multi-game legends)
  /ping                           - Check bot gateway latency
  /help                           - Interactive commands directory & usage guide
"""

import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Optional, List

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import discord
from discord import app_commands
from discord.ext import commands

# Import database and discord embed builders
from database import (
    get_db,
    get_map_strategy_detail,
    get_server_tracker_stats,
    get_cross_mode_masters,
    get_live_online_count,
    search_marketplace_items,
    insert_encounter,
    get_player_encounters
)
from discord_exporter import (
    build_player_discord_embed,
    build_leaderboard_champion_discord_embed,
    build_server_status_discord_embed,
    build_map_tactics_discord_embed
)

# ---------------------------------------------------------------------------
# Bot Configuration
# ---------------------------------------------------------------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
PREFIX = os.getenv("DISCORD_COMMAND_PREFIX", "!")
GUILD_ID_RAW = os.getenv("DISCORD_GUILD_ID", "").strip()
TEST_GUILD_ID = int(GUILD_ID_RAW) if GUILD_ID_RAW.isdigit() else None

intents = discord.Intents.default()
# Enable message_content only if explicitly requested in .env (requires Privileged Gateway Intent toggle in Developer Portal)
if os.getenv("ENABLE_MESSAGE_CONTENT", "false").lower() == "true":
    intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Iconic Bedrock Maps
MAP_CHOICES = [
    app_commands.Choice(name="Tea Party (EggWars Solo/Duos)", value="eggwars_tea_party"),
    app_commands.Choice(name="Dwarven (EggWars Solo/Duos)", value="eggwars_dwarven"),
    app_commands.Choice(name="Atlantis (EggWars Teams)", value="eggwars_atlantis"),
    app_commands.Choice(name="Toys (EggWars Teams)", value="eggwars_toys"),
    app_commands.Choice(name="Trees (SkyWars Solo)", value="skywars_trees"),
    app_commands.Choice(name="Rainbow (SkyWars Solo/Teams)", value="skywars_rainbow"),
    app_commands.Choice(name="Magic (SkyWars Teams)", value="skywars_magic"),
]

# Popular Game Arenas for Autocomplete
POPULAR_GAMES = [
    "EggWars", "SkyWars", "Lucky Islands", "Survival Games",
    "BlockWars", "BedWars", "Minerware", "Parkour Classic"
]

POPULAR_MODES = ["Solo", "Teams", "Duos", "Squads", "Mega"]

MARKETPLACE_CATEGORIES = [
    app_commands.Choice(name="All Categories", value="all"),
    app_commands.Choice(name="Cages", value="cages"),
    app_commands.Choice(name="Loot", value="loot"),
    app_commands.Choice(name="Trails", value="trails"),
    app_commands.Choice(name="Buddies", value="buddies"),
    app_commands.Choice(name="Furniture", value="furniture"),
    app_commands.Choice(name="Skins", value="skins"),
]

SENTIMENT_CHOICES = [
    app_commands.Choice(name="Helpful (Positive)", value="Helpful"),
    app_commands.Choice(name="Good Game (Positive)", value="Good Game"),
    app_commands.Choice(name="Toxic (Negative)", value="Toxic"),
    app_commands.Choice(name="Teaming (Negative)", value="Teaming"),
    app_commands.Choice(name="Hacking (Negative)", value="Hacker"),
]

# ---------------------------------------------------------------------------
# Helper Query Functions
# ---------------------------------------------------------------------------

def fetch_player_full_data(gamertag: str):
    """Fetches player stats, top leaderboard entries, and community encounters."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE LOWER(gamertag) = LOWER(?)", (gamertag.strip(),))
    p_row = cursor.fetchone()

    if not p_row:
        # Check if they exist in leaderboards table even if not in players table
        cursor.execute("SELECT player_gamertag FROM leaderboards WHERE LOWER(player_gamertag) = LOWER(?) LIMIT 1", (gamertag.strip(),))
        lb_match = cursor.fetchone()
        if lb_match:
            player_data = {
                "gamertag": lb_match["player_gamertag"],
                "rank_title": "Bedrock Competitor",
                "avatar_color": "#00e5ff",
                "custom_bio": f"Competitor on CubeCraft Bedrock Edition.",
                "total_points": 0
            }
        else:
            conn.close()
            return None, None
    else:
        player_data = dict(p_row)

    # Fetch top leaderboards
    cursor.execute("""
        SELECT game, mode, rank, points
        FROM leaderboards
        WHERE LOWER(player_gamertag) = LOWER(?)
        ORDER BY points DESC
    """, (gamertag.strip(),))
    player_data["leaderboards"] = [dict(r) for r in cursor.fetchall()]

    # Fetch encounters
    cursor.execute("SELECT sentiment, comment, created_at FROM encounters WHERE LOWER(player_gamertag) = LOWER(?) AND reported = 0 ORDER BY id DESC", (gamertag.strip(),))
    encounters = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return player_data, encounters


def fetch_top_leaderboard(game: str, mode: str, limit: int = 10):
    """Fetches top N players for a given game and mode."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.player_gamertag, l.game, l.mode, l.points, l.rank, p.rank_title, p.avatar_color
        FROM leaderboards l
        LEFT JOIN players p ON LOWER(l.player_gamertag) = LOWER(p.gamertag)
        WHERE LOWER(l.game) = LOWER(?) AND LOWER(l.mode) = LOWER(?)
        ORDER BY l.rank ASC, l.points DESC
        LIMIT ?
    """, (game.strip(), mode.strip(), limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Bot Lifecycle Events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"==================================================")
    print(f"CubeCraft Bedrock Discord Bot Connected!")
    print(f"Logged in as: {bot.user} (ID: {bot.user.id})")
    print(f"Connected Guilds: {len(bot.guilds)}")
    print(f"Command Prefix: '{PREFIX}'")
    print(f"==================================================")

    # Set presence
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"play.cubecraft.net | {PREFIX}help or /help"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Synchronize Slash Commands
    try:
        if TEST_GUILD_ID:
            test_guild = discord.Object(id=TEST_GUILD_ID)
            bot.tree.copy_global_to(guild=test_guild)
            synced = await bot.tree.sync(guild=test_guild)
            print(f"⚡ Synced {len(synced)} Slash Commands instantly to test guild ID: {TEST_GUILD_ID}")
        else:
            synced = await bot.tree.sync()
            print(f"🌐 Synced {len(synced)} global Slash Commands across all servers!")
    except Exception as e:
        print(f"⚠️ Failed to sync slash commands: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Autocomplete Handlers for Slash Commands
# ---------------------------------------------------------------------------

async def game_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    choices = [g for g in POPULAR_GAMES if current.lower() in g.lower()]
    return [app_commands.Choice(name=g, value=g) for g in choices[:25]]


async def mode_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    choices = [m for m in POPULAR_MODES if current.lower() in m.lower()]
    return [app_commands.Choice(name=m, value=m) for m in choices[:25]]


# ---------------------------------------------------------------------------
# Slash Commands
# ---------------------------------------------------------------------------

@bot.tree.command(name="player", description="Inspect official CubeCraft Bedrock competitor stats, rank card & skin.")
@app_commands.describe(gamertag="The exact Minecraft Bedrock Gamertag to lookup (e.g. MundevPolite, ykelias1439)")
async def slash_player(interaction: discord.Interaction, gamertag: str):
    await interaction.response.defer()
    player_data, encounters = fetch_player_full_data(gamertag)

    if not player_data:
        embed = discord.Embed(
            title="🔍 Player Not Found",
            description=f"Could not find **{gamertag}** among the 826+ indexed CubeCraft Bedrock ranked competitors.\n\n"
                        f"Make sure the spelling is exact, or search for competitors like `MundevPolite`, `ykelias1439`, or `TottoOP`.",
            color=0xEF4444
        )
        embed.set_footer(text="CubeCraft Bedrock Community Hub • play.cubecraft.net")
        await interaction.followup.send(embed=embed)
        return

    result = build_player_discord_embed(player_data, encounters or [])
    embed = discord.Embed.from_dict(result["embed"])
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="leaderboard", description="View official Bedrock leaderboards and reigning #1 champions.")
@app_commands.describe(
    game="Game arena (EggWars, SkyWars, Lucky Islands, etc.)",
    mode="Match mode (Solo, Teams, Duos, Squads, etc.)"
)
@app_commands.autocomplete(game=game_autocomplete, mode=mode_autocomplete)
async def slash_leaderboard(interaction: discord.Interaction, game: Optional[str] = "EggWars", mode: Optional[str] = "Solo"):
    await interaction.response.defer()
    game = game or "EggWars"
    mode = mode or "Solo"

    rows = fetch_top_leaderboard(game, mode, limit=10)
    if not rows:
        embed = discord.Embed(
            title="⚠️ No Leaderboard Data",
            description=f"No leaderboard entries found for **{game} ({mode})** on Bedrock.\nTry `EggWars (Solo)`, `SkyWars (Solo)`, or `Lucky Islands (Solo)`.",
            color=0xF59E0B
        )
        await interaction.followup.send(embed=embed)
        return

    rank1 = rows[0]
    rank2 = rows[1] if len(rows) > 1 else None

    # Base champion embed
    champ_dict = build_leaderboard_champion_discord_embed(game, mode, rank1, rank2)
    embed = discord.Embed.from_dict(champ_dict["embed"])

    # Append top 10 ladder
    ladder_lines = []
    for r in rows:
        medal = "🥇" if r["rank"] == 1 else ("🥈" if r["rank"] == 2 else ("🥉" if r["rank"] == 3 else f"`#{r['rank']}`"))
        pts = f"{r['points']:,}"
        ladder_lines.append(f"{medal} **{r['player_gamertag']}** — `{pts} pts` *({r['rank_title'] or 'Player'})*")

    embed.add_field(
        name=f"🏆 Top {len(rows)} Official Standings",
        value="\n".join(ladder_lines),
        inline=False
    )

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="server", description="Live Bedrock server status, online player count & optimal grinding windows.")
async def slash_server(interaction: discord.Interaction):
    await interaction.response.defer()
    online = get_live_online_count()
    stats = get_server_tracker_stats()
    peak = stats.get("peak_window", "16:00 - 21:00 UTC")
    offpeak = stats.get("offpeak_window", "04:00 - 08:00 UTC")

    result = build_server_status_discord_embed(online, peak, offpeak)
    embed = discord.Embed.from_dict(result["embed"])
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="map", description="Tactical map blueprints, void jump-bridge distance benchmarks & generator tiers.")
@app_commands.describe(map_name="Choose one of the 7 official Bedrock arena maps")
@app_commands.choices(map_name=MAP_CHOICES)
async def slash_map(interaction: discord.Interaction, map_name: app_commands.Choice[str]):
    await interaction.response.defer()
    map_data = get_map_strategy_detail(map_name.value)

    if not map_data:
        embed = discord.Embed(
            title="⚠️ Map Not Found",
            description=f"Map blueprint `{map_name.value}` could not be retrieved.",
            color=0xEF4444
        )
        await interaction.followup.send(embed=embed)
        return

    result = build_map_tactics_discord_embed(map_data)
    embed = discord.Embed.from_dict(result["embed"])
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="marketplace", description="Search 922+ authentic CubeCraft Bedrock marketplace items & prices.")
@app_commands.describe(
    query="Search query (e.g. dragon, cyberpunk, neon, buddy)",
    category="Item category (cages, loot, trails, buddies, skins)"
)
@app_commands.choices(category=MARKETPLACE_CATEGORIES)
async def slash_marketplace(interaction: discord.Interaction, query: Optional[str] = "", category: Optional[app_commands.Choice[str]] = None):
    await interaction.response.defer()
    cat_val = category.value if category else "all"
    items, total = search_marketplace_items(query=query or "", category=cat_val, sort_by="rating", limit=3, offset=0)

    if not items:
        embed = discord.Embed(
            title="🛒 No Marketplace Items Found",
            description=f"No authentic Bedrock marketplace items matched `{query or 'all'}` in `{cat_val}`.",
            color=0xF59E0B
        )
        await interaction.followup.send(embed=embed)
        return

    embed = discord.Embed(
        title=f"🛒 CubeCraft Marketplace Catalog ({total:,} Items Indexed)",
        description=f"Showing top results matching **\"{query or 'all'}\"** in category *{cat_val.capitalize()}*.\n"
                    f"Official items sourced from the Minecraft Marketplace & CubeCraft Bedrock store.",
        color=0x00E5FF
    )

    for item in items:
        price_str = f"🪙 **{item['price_minecoins']} Minecoins**" if item['price_minecoins'] > 0 else "🟢 **Free**"
        rating_str = f"⭐ {item['rating']:.1f} / 5.0" if item['rating'] else "New"
        embed.add_field(
            name=f"📦 {item['title']}",
            value=f"{price_str} • {rating_str} • `{item['category']}`\n*{item['description'][:110]}...*",
            inline=False
        )

    # Set image of first item
    if items[0].get("image_url"):
        embed.set_thumbnail(url=items[0]["image_url"])

    embed.set_footer(text="Official CubeCraft Bedrock Marketplace • cc-data.ru mirror")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="review", description="Log a community encounter review for a Bedrock competitor.")
@app_commands.describe(
    gamertag="Bedrock gamertag to review (e.g. MundevPolite, ykelias1439)",
    sentiment="How was playing with or against them?",
    story="Brief description of the match or incident"
)
@app_commands.choices(sentiment=SENTIMENT_CHOICES)
async def slash_review(interaction: discord.Interaction, gamertag: str, sentiment: app_commands.Choice[str], story: str):
    await interaction.response.defer()

    if len(story.strip()) < 8:
        embed = discord.Embed(
            title="⚠️ Review Too Short",
            description="Please provide at least 8 characters describing the encounter.",
            color=0xEF4444
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    # Insert into database
    success, result = insert_encounter(
        player_gamertag=gamertag.strip(),
        reviewer_name=f"Discord:{interaction.user.name}",
        sentiment=sentiment.value,
        comment=story.strip(),
        game="Bedrock Arena",
        mode="Community Match"
    )

    if not success:
        embed = discord.Embed(
            title="❌ Review Submission Failed",
            description=result.get("error", "Database error logging encounter."),
            color=0xEF4444
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    is_positive = sentiment.value in ["Helpful", "Good Game"]
    embed = discord.Embed(
        title=f"📝 Encounter Review Logged — {gamertag}",
        description=f"Your review for **{gamertag}** has been registered in the Community Hub database!",
        color=0x10B981 if is_positive else 0xEF4444
    )
    embed.add_field(name="Rating", value=f"`{sentiment.name}`", inline=True)
    embed.add_field(name="Reviewer", value=f"`{interaction.user.name}`", inline=True)
    embed.add_field(name="Encounter Story", value=f"> *\"{story.strip()}\"*", inline=False)
    embed.set_thumbnail(url=f"https://mc-heads.net/avatar/{gamertag}/128")
    embed.set_footer(text="CubeCraft Bedrock Community Hub • Player Reputation System")

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="masters", description="View Cross-Mode Dominance leaders (competitors ranked in multiple game modes).")
async def slash_masters(interaction: discord.Interaction):
    await interaction.response.defer()
    masters = get_cross_mode_masters(limit=10)

    if not masters:
        embed = discord.Embed(
            title="📊 Cross-Mode Dominance",
            description="No cross-mode master data calculated yet.",
            color=0xF59E0B
        )
        await interaction.followup.send(embed=embed)
        return

    embed = discord.Embed(
        title="👑 Cross-Mode Dominance — \"All-Around Masters\"",
        description="Top Bedrock competitors who appear in the top-25 of the greatest number of distinct game modes.",
        color=0xA855F7
    )

    lines = []
    for idx, m in enumerate(masters, start=1):
        medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"`#{idx}`"))
        distinct = m.get('distinct_games', m.get('distinct_modes', 1))
        lines.append(f"{medal} **{m['gamertag']}** — **{distinct} Distinct Games** *({m['rank_title'] or 'Player'})*")

    embed.add_field(name="🏆 Top All-Around Bedrock Competitors", value="\n".join(lines), inline=False)
    embed.set_footer(text="39 Bedrock Game Modes Synchronized • play.cubecraft.net")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="ping", description="Check bot gateway latency.")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Gateway Latency: **`{latency}ms`**\nConnected to CubeCraft Bedrock Hub Engine.",
        color=0x10B981
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="help", description="Commands directory and interactive guide for the CubeCraft Bedrock Bot.")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 CubeCraft Bedrock Community Bot — Help Directory",
        description="Official competitive bot for Minecraft Bedrock Edition players across 39 game modes.\n"
                    "Use slash commands (`/command`) or text commands (`!command`).",
        color=0x5865F2
    )

    embed.add_field(
        name="👤 Player Telemetry",
        value="`/player <gamertag>` — Rank tier, community reputation %, leaderboard ranks & skin.\n"
              "`/review <gt> <sentiment> <story>` — Rate a player you encountered in-game.\n"
              "`/masters` — Cross-Mode Dominance: top players across multiple games.",
        inline=False
    )

    embed.add_field(
        name="🏆 Leaderboards & Competition",
        value="`/leaderboard [game] [mode]` — Live official leaderboards & #1 champion point lead.\n"
              "`/server` — Real-time Bedrock online count, peak hours & off-peak grind window.",
        inline=False
    )

    embed.add_field(
        name="🗺️ Tactical Maps & Marketplace",
        value="`/map <map_name>` — 2D void bridging distance benchmarks & generator upgrade costs.\n"
              "`/marketplace [query] [cat]` — Search 922+ authentic Marketplace items & Minecoin prices.",
        inline=False
    )

    embed.add_field(
        name="⚡ Server Connection",
        value="**Server IP**: `play.cubecraft.net` (Bedrock Port: `19132`)\n"
              "**Platform**: CubeCraft Bedrock Community Hub",
        inline=False
    )

    embed.set_thumbnail(url="https://mc-heads.net/avatar/CubeCraft/128")
    embed.set_footer(text="CubeCraft Bedrock Community Hub • Built for Bedrockers")
    await interaction.response.send_message(embed=embed)


# ---------------------------------------------------------------------------
# Traditional Prefix Text Commands (!player, !top, !server, etc.)
# ---------------------------------------------------------------------------

@bot.command(name="player", aliases=["stats", "profile"])
async def cmd_player(ctx, gamertag: Optional[str] = None):
    """Inspect competitor profile: !player MundevPolite"""
    if not gamertag:
        await ctx.send(f"⚠️ Usage: `{PREFIX}player <gamertag>` (e.g. `{PREFIX}player MundevPolite`)")
        return

    player_data, encounters = fetch_player_full_data(gamertag)
    if not player_data:
        await ctx.send(f"🔍 Could not find competitor `{gamertag}` among 826+ indexed Bedrock players.")
        return

    result = build_player_discord_embed(player_data, encounters or [])
    embed = discord.Embed.from_dict(result["embed"])
    await ctx.send(embed=embed)


@bot.command(name="top", aliases=["leaderboard", "lb"])
async def cmd_leaderboard(ctx, game: Optional[str] = "EggWars", mode: Optional[str] = "Solo"):
    """View leaderboard: !top EggWars Solo"""
    rows = fetch_top_leaderboard(game, mode, limit=10)
    if not rows:
        await ctx.send(f"⚠️ No leaderboard entries found for `{game} ({mode})`.")
        return

    rank1 = rows[0]
    rank2 = rows[1] if len(rows) > 1 else None

    champ_dict = build_leaderboard_champion_discord_embed(game, mode, rank1, rank2)
    embed = discord.Embed.from_dict(champ_dict["embed"])

    ladder_lines = []
    for r in rows:
        rnk = r.get("rank", 0)
        medal = "🥇" if rnk == 1 else ("🥈" if rnk == 2 else ("🥉" if rnk == 3 else f"` #{rnk:>2} `"))
        pts = f"{r['points']:,}"
        ladder_lines.append(f"{medal} **{r['player_gamertag']}** ── `{pts} pts`")

    embed.add_field(name=f"🏆 Top {len(rows)} Standings", value="\n".join(ladder_lines), inline=False)
    await ctx.send(embed=embed)


@bot.command(name="server", aliases=["status", "online"])
async def cmd_server(ctx):
    """Server status & grind hours: !server"""
    online = get_live_online_count()
    stats = get_server_tracker_stats()
    result = build_server_status_discord_embed(
        online,
        stats.get("peak_window", "16:00 - 21:00 UTC"),
        stats.get("offpeak_window", "04:00 - 08:00 UTC")
    )
    embed = discord.Embed.from_dict(result["embed"])
    await ctx.send(embed=embed)


@bot.command(name="map")
async def cmd_map(ctx, *, map_name: Optional[str] = "tea_party"):
    """Map blueprint: !map tea_party"""
    # Normalize map name
    slug = map_name.lower().replace(" ", "_")
    matched_id = None
    for c in MAP_CHOICES:
        if slug in c.value.lower() or slug in c.name.lower():
            matched_id = c.value
            break

    if not matched_id:
        matched_id = "eggwars_tea_party"

    map_data = get_map_strategy_detail(matched_id)
    if not map_data:
        await ctx.send(f"⚠️ Map `{map_name}` not found. Options: `tea party`, `dwarven`, `atlantis`, `toys`, `trees`, `rainbow`, `magic`.")
        return

    result = build_map_tactics_discord_embed(map_data)
    embed = discord.Embed.from_dict(result["embed"])
    await ctx.send(embed=embed)


@bot.command(name="market", aliases=["marketplace"])
async def cmd_market(ctx, *, query: Optional[str] = ""):
    """Marketplace search: !market dragon"""
    items, total = search_marketplace_items(query=query or "", category="all", sort_by="rating", limit=3, offset=0)
    if not items:
        await ctx.send(f"🛒 No marketplace items found matching `{query}`.")
        return

    embed = discord.Embed(
        title=f"🛒 CubeCraft Marketplace Catalog ({total:,} Items Indexed)",
        description=f"Showing top results matching **\"{query or 'all'}\"**.",
        color=0x00E5FF
    )
    for item in items:
        price_str = f"🪙 **{item['price_minecoins']} Minecoins**" if item['price_minecoins'] > 0 else "🟢 **Free**"
        embed.add_field(
            name=f"📦 {item['title']}",
            value=f"{price_str} • ⭐ {item['rating']:.1f} • `{item['category']}`\n*{item['description'][:100]}...*",
            inline=False
        )
    if items[0].get("image_url"):
        embed.set_thumbnail(url=items[0]["image_url"])
    await ctx.send(embed=embed)


@bot.command(name="masters", aliases=["crossmode"])
async def cmd_masters(ctx):
    """Cross-mode legends: !masters"""
    masters = get_cross_mode_masters(limit=10)
    embed = discord.Embed(
        title="👑 Cross-Mode Dominance — \"All-Around Masters\"",
        description="Top Bedrock competitors ranked in multiple game modes.",
        color=0xA855F7
    )
    lines = [f"`#{i+1}` **{m['gamertag']}** — **{m.get('distinct_games', m.get('distinct_modes', 1))} Distinct Games**" for i, m in enumerate(masters)]
    embed.add_field(name="🏆 Leaders", value="\n".join(lines), inline=False)
    await ctx.send(embed=embed)


@bot.command(name="ping")
async def cmd_ping(ctx):
    """Check ping: !ping"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency}ms`")


@bot.command(name="help")
async def cmd_help(ctx):
    """Interactive help: !help"""
    embed = discord.Embed(
        title="🎮 CubeCraft Bedrock Community Bot — Commands",
        description=f"Use `{PREFIX}` for text commands or `/` for interactive slash commands.",
        color=0x5865F2
    )
    embed.add_field(name=f"{PREFIX}player <gt>", value="Inspect competitor profile, rank tier & reputation score.", inline=False)
    embed.add_field(name=f"{PREFIX}top [game] [mode]", value="View official leaderboards & #1 champion point lead.", inline=False)
    embed.add_field(name=f"{PREFIX}server", value="Live Bedrock online count & peak grinding hours.", inline=False)
    embed.add_field(name=f"{PREFIX}map [name]", value="Tactical map blueprints & Bedrock jump-bridge distances.", inline=False)
    embed.add_field(name=f"{PREFIX}market [search]", value="Search 922+ authentic Marketplace items & prices.", inline=False)
    embed.add_field(name=f"{PREFIX}masters", value="Cross-Mode Dominance rankings.", inline=False)
    embed.add_field(name=f"{PREFIX}ping", value="Check gateway response latency.", inline=False)
    await ctx.send(embed=embed)


# ---------------------------------------------------------------------------
# Main Execution Entrypoint
# ---------------------------------------------------------------------------

def run():
    if not TOKEN or TOKEN == "your_discord_bot_token_here":
        print("\n" + "=" * 65, file=sys.stderr)
        print("❌ ERROR: DISCORD_BOT_TOKEN is missing or not configured!", file=sys.stderr)
        print("=" * 65, file=sys.stderr)
        print("\nTo start your CubeCraft Bedrock Discord Bot:", file=sys.stderr)
        print("  1. Create a Bot at: https://discord.com/developers/applications", file=sys.stderr)
        print("  2. Copy your Bot Token from Bot -> Reset Token", file=sys.stderr)
        print("  3. Set DISCORD_BOT_TOKEN in your .env file or environment variable:", file=sys.stderr)
        print("     export DISCORD_BOT_TOKEN=\"your_token_here\"", file=sys.stderr)
        print("  4. Run: python3 discord_bot.py", file=sys.stderr)
        print("=" * 65 + "\n", file=sys.stderr)
        sys.exit(1)

    print("🚀 Initializing CubeCraft Bedrock Discord Bot gateway connection...")
    bot.run(TOKEN)


if __name__ == "__main__":
    run()
