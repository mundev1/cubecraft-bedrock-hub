"""
CubeCraft Bedrock Community Hub - Database & Seed Data
SQLite schema and realistic pre-populated data for Bedrock games, leaderboards, bundles, clips, and player encounter comments.
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cubecraft.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        gamertag TEXT PRIMARY KEY,
        rank_title TEXT DEFAULT 'Player',
        total_games INTEGER DEFAULT 0,
        reputation_score INTEGER DEFAULT 100,
        avatar_color TEXT DEFAULT '#00e5ff',
        bio TEXT DEFAULT '',
        first_seen TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_gamertag TEXT,
        game TEXT,
        mode TEXT,
        wins INTEGER,
        kills INTEGER,
        streak INTEGER,
        rating INTEGER,
        rank INTEGER,
        favorite_kit TEXT,
        FOREIGN KEY(player_gamertag) REFERENCES players(gamertag)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bundles (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        tagline TEXT,
        description TEXT,
        price_minecoins INTEGER,
        original_price INTEGER,
        rarity TEXT,
        badge TEXT,
        banner_img TEXT,
        items_json TEXT,
        release_date TEXT,
        expiry_date TEXT,
        is_featured INTEGER DEFAULT 1
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        gamertag TEXT NOT NULL,
        game TEXT NOT NULL,
        medal_url TEXT,
        video_url TEXT,
        thumbnail_url TEXT,
        duration TEXT,
        views INTEGER DEFAULT 0,
        upvotes INTEGER DEFAULT 0,
        created_at TEXT
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS encounters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_gamertag TEXT NOT NULL,
        reviewer_name TEXT NOT NULL,
        game_played TEXT NOT NULL,
        encounter_type TEXT NOT NULL,
        sentiment TEXT DEFAULT 'positive',
        rating INTEGER DEFAULT 5,
        comment TEXT NOT NULL,
        helpful_votes INTEGER DEFAULT 0,
        reported INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY(player_gamertag) REFERENCES players(gamertag)
    )''')

    conn.commit()
    conn.close()

def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute('SELECT COUNT(*) FROM players')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Seed Players
    players_data = [
        ("Vxrtical", "Obsidian", 4820, 98, "#00e5ff", "Bedrock EggWars grinder & competitive duels player. Controller movement specialist.", "2021-04-12"),
        ("CubicPro", "Diamond", 3910, 95, "#38bdf8", "SkyWars void snipe enthusiast and bridge builder.", "2020-09-18"),
        ("AuraPvP", "Obsidian", 6150, 84, "#f43f5e", "High CPS jitterclicker, aggro rusher on Tea Party.", "2021-01-05"),
        ("BedrockKing", "Emerald", 5230, 96, "#10b981", "EggWars Squads commander. Always buys obsidian defense early.", "2019-11-20"),
        ("SwiftBladeX", "Iron", 2410, 91, "#fbbf24", "Duels & Survival Games tournament finalist.", "2022-03-15"),
        ("LuckyStrike", "Diamond", 3120, 89, "#a855f7", "Lucky Islands wand collector. Master of explosive sheep.", "2021-08-01"),
        ("BridgeGod_BE", "Obsidian", 5780, 97, "#00e5ff", "BlockWars Bridges fastest score record holder (18.4s).", "2020-05-10"),
        ("ShadowSniper", "Emerald", 3490, 93, "#06b6d4", "SkyWars punch bow specialist.", "2021-10-30"),
        ("MinerChief", "Gold", 1980, 92, "#f59e0b", "MinerWare micro-game undefeated 19 streaks.", "2022-07-22"),
        ("ClutchMaster99", "Player", 1420, 88, "#64748b", "Solo EggWars 1v4 defender. Diamond generator holder.", "2023-01-14"),
        ("GhostlyDash", "Diamond", 2890, 90, "#c084fc", "Survival Games chest router. Never misses crits.", "2022-11-04"),
        ("NeonPulse", "Emerald", 4320, 94, "#22c55e", "EggWars Mega team leader. Tactical wool spammer.", "2021-06-19")
    ]
    cursor.executemany(
        'INSERT INTO players (gamertag, rank_title, total_games, reputation_score, avatar_color, bio, first_seen) VALUES (?, ?, ?, ?, ?, ?, ?)',
        players_data
    )

    # Seed Leaderboards (Bedrock Games)
    leaderboards_data = [
        # EggWars
        ("Vxrtical", "EggWars", "Squads", 3140, 18920, 42, 2890, 1, "Healer / Tank"),
        ("BedrockKing", "EggWars", "Squads", 2980, 16400, 31, 2820, 2, "Builder"),
        ("NeonPulse", "EggWars", "Squads", 2740, 15100, 28, 2760, 3, "Pusher"),
        ("AuraPvP", "EggWars", "Solo", 2490, 19800, 35, 2710, 4, "Warrior"),
        ("ClutchMaster99", "EggWars", "Duos", 1850, 9400, 19, 2450, 5, "Egg Breaker"),
        ("BridgeGod_BE", "EggWars", "Squads", 1620, 8900, 15, 2390, 6, "Speeder"),
        
        # SkyWars
        ("CubicPro", "SkyWars", "Solo", 2840, 14200, 38, 2850, 1, "Archer"),
        ("ShadowSniper", "SkyWars", "Solo", 2610, 13900, 29, 2790, 2, "Punch Bow"),
        ("SwiftBladeX", "SkyWars", "Teams", 2390, 12100, 24, 2680, 3, "Swordsman"),
        ("LuckyStrike", "SkyWars", "Chaos", 1950, 10200, 18, 2520, 4, "Scout"),
        ("Vxrtical", "SkyWars", "Solo", 1740, 9800, 14, 2440, 5, "Tank"),

        # Lucky Islands
        ("LuckyStrike", "Lucky Islands", "Solo", 2410, 11800, 26, 2780, 1, "Lucky Knight"),
        ("CubicPro", "Lucky Islands", "Teams", 2180, 10600, 21, 2690, 2, "Alchemist"),
        ("ClutchMaster99", "Lucky Islands", "Solo", 1870, 8900, 16, 2510, 3, "Chaos Lord"),
        ("ShadowSniper", "Lucky Islands", "Teams", 1540, 7800, 12, 2380, 4, "Wand Magician"),

        # BlockWars
        ("BridgeGod_BE", "BlockWars", "Bridges", 3420, 15800, 54, 2980, 1, "Speed Runner"),
        ("Vxrtical", "BlockWars", "Bridges", 3110, 14200, 39, 2890, 2, "Defender"),
        ("AuraPvP", "BlockWars", "Core", 2650, 13100, 27, 2740, 3, "Miner"),
        ("SwiftBladeX", "BlockWars", "CTF", 2290, 11400, 22, 2610, 4, "Flag Runner"),

        # Survival Games
        ("SwiftBladeX", "Survival Games", "Solo", 1980, 9800, 18, 2720, 1, "Berserker"),
        ("GhostlyDash", "Survival Games", "Solo", 1820, 8900, 15, 2640, 2, "Tracker"),
        ("BedrockKing", "Survival Games", "Teams", 1640, 8100, 13, 2530, 3, "Chest Hunter"),

        # MinerWare
        ("MinerChief", "MinerWare", "Standard", 1840, 4200, 32, 2810, 1, "Fast Reflexes"),
        ("CubicPro", "MinerWare", "Standard", 1560, 3600, 21, 2670, 2, "Boss Slayer"),
        ("LuckyStrike", "MinerWare", "Standard", 1390, 3100, 17, 2520, 3, "Speedster"),

        # Duels (Battle Arena)
        ("AuraPvP", "Duels", "Nodebuff", 4120, 16800, 68, 3050, 1, "PotPvP Master"),
        ("Vxrtical", "Duels", "Classic", 3890, 15400, 52, 2960, 2, "Combo King"),
        ("SwiftBladeX", "Duels", "UHC", 3240, 12900, 36, 2810, 3, "Rod Specialist")
    ]
    cursor.executemany(
        'INSERT INTO leaderboards (player_gamertag, game, mode, wins, kills, streak, rating, rank, favorite_kit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        leaderboards_data
    )

    # Seed Bundles
    now = datetime.utcnow()
    exp_cyber = (now + timedelta(days=6, hours=14)).isoformat() + "Z"
    exp_frost = (now + timedelta(days=13, hours=8)).isoformat() + "Z"
    exp_solar = (now + timedelta(days=20, hours=22)).isoformat() + "Z"
    exp_arcade = (now + timedelta(days=2, hours=4)).isoformat() + "Z"

    bundles_data = [
        (
            "cyber-samurai-2026",
            "Cyber Samurai Void Bundle",
            "Neon katanas, holographic cage, and digitized egg destruction.",
            "Transform your Bedrock matches with futuristic neon aesthetic. Includes an exclusive animated Cyber Egg skin, the Holographic Dojo cage, and digital glitch kill effects.",
            1340,
            1800,
            "Mythic",
            "Featured Deal",
            "cyber_samurai.jpg",
            json.dumps([
                {"name": "Holo-Dojo Cage", "type": "Cage Skin", "rarity": "Mythic", "desc": "Glowing neon pillars with floating cherry blossoms and cybernetic sound effects."},
                {"name": "Cyber Core Egg", "type": "Egg Skin", "rarity": "Legendary", "desc": "Pulsating matrix egg that emits circuit particles when defended."},
                {"name": "Glitch Void Kill Effect", "type": "Kill Effect", "rarity": "Legendary", "desc": "Vanishes fallen foes into a pixelated matrix rupture."},
                {"name": "Neon Blade Arrow Trail", "type": "Arrow Trail", "rarity": "Epic", "desc": "Fires cybernetic laser arrows with teal trail flare."},
                {"name": "Ronin Prefix Title", "type": "Chat Prefix", "rarity": "Rare", "desc": "Exclusive [Ronin] cyan chat badge."}
            ]),
            "2026-11-01",
            exp_cyber,
            1
        ),
        (
            "frostbite-crystal-pack",
            "Frostbite Crystal Core",
            "Glacial cages, cryo egg shells, and howling blizzard win fanfare.",
            "Cool down intense EggWars matches with the Frostbite collection. Features frosted crystalline structures and sub-zero victory animations.",
            990,
            1340,
            "Legendary",
            "New Arrival",
            "frostbite_pack.jpg",
            json.dumps([
                {"name": "Glacial Spire Cage", "type": "Cage Skin", "rarity": "Legendary", "desc": "Encased in translucent icicles that shatter upon game start."},
                {"name": "Sub-Zero Egg", "type": "Egg Skin", "rarity": "Epic", "desc": "Permafrost coated egg with cold vapor mist."},
                {"name": "Blizzard Win Effect", "type": "Win Effect", "rarity": "Legendary", "desc": "Freezes the entire podium island in ice blocks with Aurora Borealis skybox."},
                {"name": "Frost Nova Gravestone", "type": "Gravestone", "rarity": "Rare", "desc": "Leaves an icy crystalline tombstone on defeat."}
            ]),
            "2026-11-05",
            exp_frost,
            1
        ),
        (
            "solar-flare-eggwars",
            "Solar Flare Celestial Pack",
            "Harness cosmic supernova energy across the Bedrock arena.",
            "A celestial pack containing solar flare particle effects, the Sun-Forge cage, and meteorite egg protection effects.",
            830,
            1100,
            "Epic",
            "Popular",
            "solar_flare.jpg",
            json.dumps([
                {"name": "Sun-Forge Cage", "type": "Cage Skin", "rarity": "Epic", "desc": "Solar ring cage orbiting with golden plasma flares."},
                {"name": "Supernova Egg Skin", "type": "Egg Skin", "rarity": "Epic", "desc": "Miniature sun with glowing corona flares."},
                {"name": "Solar Beam Kill Effect", "type": "Kill Effect", "rarity": "Rare", "desc": "Strikes opponents with an orbital ray of light upon defeat."}
            ]),
            "2026-10-25",
            exp_solar,
            0
        ),
        (
            "retro-arcade-pixel",
            "8-Bit Retro Arcade Bundle",
            "Chiptune soundbites, pixelated cages, and retro victory music.",
            "Throw it back to vintage arcade classics. Features chiptune elimination noises and 8-bit voxel egg cosmetics.",
            660,
            900,
            "Rare",
            "Last Chance",
            "retro_arcade.jpg",
            json.dumps([
                {"name": "Arcade Cabinet Cage", "type": "Cage Skin", "rarity": "Rare", "desc": "Spawn inside an authentic retro arcade machine with joystick animations."},
                {"name": "Pixel Sprite Egg", "type": "Egg Skin", "rarity": "Rare", "desc": "Voxelized 8-bit heart sprite egg."},
                {"name": "Insert Coin Kill Effect", "type": "Kill Effect", "rarity": "Rare", "desc": "Drops floating pixel coins whenever you eliminate a foe."}
            ]),
            "2026-10-15",
            exp_arcade,
            0
        )
    ]
    cursor.executemany(
        '''INSERT INTO bundles (id, title, tagline, description, price_minecoins, original_price, rarity, badge, banner_img, items_json, release_date, expiry_date, is_featured)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        bundles_data
    )

    # Seed Medal Clips
    clips_data = [
        (
            "1v4 EggWars Squads Clutch on Tea Party (No Armor!)",
            "Vxrtical",
            "EggWars",
            "https://medal.tv/games/minecraft/clips/i4CubeBedrockClutch/sample",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=600&q=80",
            "0:44",
            1420,
            87,
            "2026-11-09 18:24:00"
        ),
        (
            "Insane 68-Block Void Punch Bow Snipe in SkyWars Solo",
            "ShadowSniper",
            "SkyWars",
            "https://medal.tv/games/minecraft/clips/i4BowSnipeBedrock/sample",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=600&q=80",
            "0:28",
            980,
            64,
            "2026-11-08 14:15:00"
        ),
        (
            "Fastest BlockWars Bridges Score (18.4 Seconds WR Route)",
            "BridgeGod_BE",
            "BlockWars",
            "https://medal.tv/games/minecraft/clips/i4BridgesSpeedScore/sample",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=600&q=80",
            "0:32",
            2140,
            142,
            "2026-11-07 20:05:00"
        ),
        (
            "Wand of Explosive Sheep 4-Man Team Wipe in Lucky Islands",
            "LuckyStrike",
            "Lucky Islands",
            "https://medal.tv/games/minecraft/clips/i4LuckyWandWipe/sample",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
            "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?auto=format&fit=crop&w=600&q=80",
            "0:39",
            830,
            51,
            "2026-11-06 11:40:00"
        ),
        (
            "Double Trapdoor Obby Trap Clutch in EggWars Mega",
            "NeonPulse",
            "EggWars",
            "https://medal.tv/games/minecraft/clips/i4MegaTrapEgg/sample",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
            "https://images.unsplash.com/photo-1579373903781-fd5c0c30c4cd?auto=format&fit=crop&w=600&q=80",
            "0:52",
            1190,
            76,
            "2026-11-04 16:30:00"
        ),
        (
            "Unreal 52-Hit Combo in Nodebuff Duels vs #3 Ranked",
            "AuraPvP",
            "Duels",
            "https://medal.tv/games/minecraft/clips/i4Nodebuff52Combo/sample",
            "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
            "https://images.unsplash.com/photo-1563089145-599997674d42?auto=format&fit=crop&w=600&q=80",
            "0:35",
            1750,
            118,
            "2026-11-03 22:10:00"
        )
    ]
    cursor.executemany(
        '''INSERT INTO clips (title, gamertag, game, medal_url, video_url, thumbnail_url, duration, views, upvotes, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        clips_data
    )

    # Seed Player Encounters & Comments
    encounters_data = [
        (
            "Vxrtical",
            "KryptonBE",
            "EggWars Squads",
            "God-tier Clutch",
            "positive",
            5,
            "Ran into Vxrtical on Tea Party while playing solo queue squads. Our other two teammates quit within 2 minutes. He coordinated diamond generator control, bought obsidian while keeping the enemy occupied, and clutched the final 1v2 fight. Absolute legend and calm communicator.",
            24,
            0,
            "2026-11-09 21:12:00"
        ),
        (
            "Vxrtical",
            "SweatDetector",
            "EggWars Duos",
            "Sweaty Opponent",
            "positive",
            5,
            "Facing Vxrtical is scary on Bedrock controller. He speed-bridges backwards without stopping and placed blocks mid-air to save himself from a void knockoff. Good game, hard to counter but respectful.",
            15,
            0,
            "2026-11-07 19:30:00"
        ),
        (
            "CubicPro",
            "ArrowDodge_99",
            "SkyWars Solo",
            "Tactical Trapper",
            "positive",
            4,
            "Fell right into CubicPro's ghost block TNT trap on the Medieval map. I wasn't even mad, the setup was genius. 10/10 game sense.",
            19,
            0,
            "2026-11-08 16:45:00"
        ),
        (
            "AuraPvP",
            "ShieldMaster",
            "Duels Nodebuff",
            "Sweaty Opponent",
            "positive",
            4,
            "His CPS is unreal. He was w-tapping every hit and had optimal pot heals. Definitely a top tier Bedrock duelist. Hard to beat unless you have lower ping.",
            11,
            0,
            "2026-11-06 23:10:00"
        ),
        (
            "BedrockKing",
            "BlockBuster9",
            "EggWars Squads",
            "Helpful Teammate",
            "positive",
            5,
            "Always shares iron and gold at the starter generator! When I asked for wool he dropped 64 blocks immediately and protected the egg with 3 layers before rushing mid. Wish every random teammate was like him.",
            32,
            0,
            "2026-11-10 12:05:00"
        ),
        (
            "LuckyStrike",
            "WandVictim",
            "Lucky Islands Teams",
            "Wholesome Teammate",
            "positive",
            5,
            "Hilarious teammate. He got 3 sheep wands from lucky blocks and escorted our entire squad across the bridge firing exploding rainbow sheep. We were dying of laughter in party chat.",
            28,
            0,
            "2026-11-05 18:20:00"
        ),
        (
            "BridgeGod_BE",
            "SpeedTester",
            "BlockWars Bridges",
            "God-tier Clutch",
            "positive",
            5,
            "He literally scored 3 goals in under 70 seconds. Jump-bridging without placing sneak blocks. The enemy team didn't even have time to build a barrier. Unreal speed on Bedrock.",
            22,
            0,
            "2026-11-08 10:14:00"
        ),
        (
            "ClutchMaster99",
            "RandomGamer_21",
            "EggWars Duos",
            "Helpful Teammate",
            "positive",
            5,
            "Our egg got broken in the first 3 minutes by pink team. ClutchMaster didn't give up, scavenged emeralds from mid while stealthing, bought punch bow and knocked the last team off. We actually won!",
            17,
            0,
            "2026-11-09 14:02:00"
        )
    ]
    cursor.executemany(
        '''INSERT INTO encounters (player_gamertag, reviewer_name, game_played, encounter_type, sentiment, rating, comment, helpful_votes, reported, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        encounters_data
    )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("Initializing SQLite database...")
    init_db()
    seed_db()
    print("Database initialized and seeded successfully!")
