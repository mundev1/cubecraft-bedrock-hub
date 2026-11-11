# 🧊 CubeCraft Bedrock Community Hub

A minimalist, dark-themed community web platform designed specifically for the Minecraft Bedrock community playing on the CubeCraft network (`play.cubecraft.net`).

---

## 🌟 Key Features

1. **🏆 39 Game Mode Leaderboards & 800+ Real Bedrock Competitors**
   - Synchronized directly with official CubeCraft Bedrock leaderboards (`cc-data.ru` API).
   - Covers all Bedrock game modes:
     - **EggWars**: Solo, Duos (Teams of 2), Squads (Teams of 4), Mega, Duels
     - **SkyWars**: Solo, Duos (Teams of 2), Squads (Teams of 4), Chaos, Mega, Duels
     - **BlockWars**: Bridges 5v5, Bridges Duels, CTF 5v5, CTF Duels, 50v50 Bridges, 50v50 DTC, 50v50 Domination, 50v50 TDM, 50v50 CTF
     - **BedWars**: Solo, Duos (Teams of 2), Squads (Teams of 4)
     - **Lucky Islands**: Solo, Teams, Duels
     - **Duels (Battle Arena)**: 1v1 Duels, 2v2 Duels, 1v1 OP Duels, 2v2 OP Duels, Free For All
     - **Survival Games**: Solo, Duos (Teams of 2)
     - **MinerWare**, **Parkour** (Classic & Competitive), **Pillars of Fortune**, **Disasters**, **Mob Hunt**
   - Top 3 Podiums (#1 Gold, #2 Silver, #3 Bronze) featuring **official 3D CubeCraft player skin renders** from the CubeCraft CDN (`files.cubecraftcdn.com`).
   - Dynamic mode selector pills with live searching across all 800+ gamertags.

2. **🎬 Playable Medal & Community Clips Hub**
   - Built-in video theatre interface with zero CSP failures, supporting **Medal.tv clips**, **YouTube embeds**, and direct video streams.
   - Includes full video controls (play/pause, seek scrubber, volume, playback speed, theater mode, fullscreen).
   - **Community Submission Section**: An interactive, prominent submission panel right on the page allowing any player to submit their Medal or YouTube clutches, tag their gamertag and game mode, and publish them to the community feed.
   - Community upvoting and view counters.

3. **🎁 Bedrock Bundles & Cosmetics Showcase**
   - Catalog of official CubeCraft Bedrock store & Marketplace bundles (e.g. *Cyber Samurai Void Bundle*, *Frostbite Crystal Core*, *Solar Flare Celestial Pack*, *Retro Arcade*).
   - Real-time countdown clock tracking bundle availability.
   - Prices in Minecoins with discounts and rarity tier badges (*Mythic*, *Legendary*, *Epic*, *Rare*).
   - Interactive **Inspect Bundle** modal detailing cage skins, egg skins, arrow trails, kill effects, and gravestones.

4. **💬 Player Encounters & Community Reputation System**
   - Dedicated gamertag search with autocomplete across 800+ Bedrock players.
   - Player Profile view with community reputation score, dynamic badges (⚡ *Clutch God*, 🛡️ *Team Anchor*, 🕸️ *Architect Trapper*, 🔥 *High ELO Threat*).
   - Structured encounter tags (`God-tier Clutch`, `Helpful Teammate`, `Sweaty Opponent`, `Tactical Trapper`, `Wholesome Teammate`, `Suspicious / Alert`).
   - "Helpful" review upvotes and moderation reporting.

5. **🖤 Sleek Minimalist Dark Aesthetic**
   - Deep obsidian background (`#06080d`) with layered glass surfaces (`#0b0f19`) and subtle borders (`#182236`).
   - Signature CubeCraft electric cyan accents (`#00e5ff`) with glowing micro-interactions.
   - Fully responsive for mobile, tablet, and desktop screens.
   - Interactive one-click copy for the server IP (`play.cubecraft.net:19132`).

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.9+ (Standard Python runtime, no extra installations needed)
- Flask (`pip install flask` if not already installed)

### 2. Start the Server
```bash
cd /Users/mundevanujtomar/.gemini/antigravity/scratch/cubecraft-bedrock-hub
python3 server.py
```

The application will start on:
👉 **`http://localhost:5055`**

### 3. Run Automated Tests
```bash
python3 -m unittest tests/test_api.py -v
```

---

## 📂 Project Structure

```
cubecraft-bedrock-hub/
├── database.py                     # SQLite database schema, sync engine & Bedrock seed data
├── bedrock_leaderboards_snapshot.json # 39 game modes & 800+ players offline snapshot
├── server.py                       # Flask REST API & static file web server
├── cubecraft.db                    # Embedded SQLite database
├── tests/
│   └── test_api.py                 # API automated test suite
├── static/
│   ├── index.html                  # Single-page application HTML5 layout
│   ├── css/
│   │   └── styles.css              # Minimalist dark theme design system
│   └── js/
│       └── app.js                  # Client router, sub-modes, Medal player & community submissions
└── README.md                       # Documentation & setup guide
```
