# 🧊 CubeCraft Bedrock Community Hub

A minimalist, dark-themed community web application designed specifically for the Minecraft Bedrock community playing on the CubeCraft network (`play.cubecraft.net`).

---

## 🌟 Key Features

1. **🏆 Multi-Game Leaderboards**
   - Live filters across Bedrock classics: **EggWars**, **SkyWars**, **Lucky Islands**, **BlockWars**, **Survival Games**, **MinerWare**, and **Duels**.
   - Sort by **Wins**, **Kills**, **Win Streaks**, and **ELO Rating**.
   - Podium showcases for Top 3 players (#1 Gold, #2 Silver, #3 Bronze) with custom avatars and rank titles.
   - Interactive search and direct navigation to any player's encounter profile.

2. **🎁 Bedrock Bundles & Cosmetics Showcase**
   - Catalog of official CubeCraft Bedrock store & Marketplace bundles (e.g. *Cyber Samurai Void Bundle*, *Frostbite Crystal Core*, *Solar Flare Celestial Pack*, *Retro Arcade*).
   - Real-time countdown clock tracking bundle availability.
   - Prices in Minecoins with discounts and rarity tier badges (*Mythic*, *Legendary*, *Epic*, *Rare*).
   - Interactive **Inspect Bundle** modal detailing cage skins, egg skins, arrow trails, kill effects, and gravestones.

3. **🎬 Playable Medal Clips Theatre**
   - Built-in video interface supporting **Medal.tv clip embeds** (`medal.tv/clip/...`) and HTML5 direct video playback.
   - Features in-modal theatre mode toggle, video controls, game tags, view counters, and community upvoting.
   - **Submit Clip Modal**: Allows Bedrock players to share and showcase their own clutching moments.

4. **💬 Player Encounters & Community Reputation System**
   - Dedicated gamertag search with instant autocomplete suggestions.
   - Player Profile view with community reputation percentage gauge (e.g., *98% Positive Reputation*).
   - Dynamic player badges earned through community reviews (⚡ *Clutch God*, 🛡️ *Team Anchor*, 🕸️ *Architect Trapper*, 🔥 *High ELO Threat*).
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
├── database.py           # SQLite database schema & Bedrock seed data
├── server.py             # Flask REST API & static file web server
├── cubecraft.db          # Embedded SQLite database
├── tests/
│   └── test_api.py       # API automated test suite
├── static/
│   ├── index.html        # Single-page application HTML5 layout
│   ├── css/
│   │   └── styles.css    # Minimalist dark theme design system
│   └── js/
│       └── app.js        # Client router, leaderboard filters, Medal player & encounters
└── README.md             # Documentation & setup guide
```

---

## 🛡️ Community Guidelines & Moderation

- Player encounter reviews can be tagged to recognize helpful teammates or give respectful props to skilled rivals.
- Any comment flagged via the **Flag** button is instantly marked for moderation and hidden from the public feed.
