"""
CubeCraft Bedrock 2D Top-Down Tactical Schematic Generator
Generates precise top-down vector layouts (SVG/Canvas coordinates)
for all iconic CubeCraft Bedrock maps (EggWars & SkyWars).
Includes exact island spatial coordinates, team positions, generator nodes,
and void bridging rush trajectories with Bedrock jump-bridge velocities (~5.6 bps).
"""
import math
import json

def _pt_on_circle(cx, cy, radius, angle_deg):
    """Calculates integer rounded (x, y) coordinates on a circle."""
    rad = math.radians(angle_deg)
    return int(round(cx + radius * math.cos(rad))), int(round(cy + radius * math.sin(rad)))

def get_map_schematic_2d(map_id):
    """
    Returns full top-down 2D schematic layout for the given map_id.
    Coordinate space is standardized to viewBox="0 0 800 800" with center at (400, 400).
    """
    cx, cy = 400, 400

    team_colors_8 = [
        {"name": "Red", "color": "#ef4444", "stroke": "#f87171"},
        {"name": "Orange", "color": "#f97316", "stroke": "#fb923c"},
        {"name": "Yellow", "color": "#eab308", "stroke": "#fde047"},
        {"name": "Green", "color": "#22c55e", "stroke": "#4ade80"},
        {"name": "Aqua", "color": "#06b6d4", "stroke": "#22d3ee"},
        {"name": "Blue", "color": "#3b82f6", "stroke": "#60a5fa"},
        {"name": "Pink", "color": "#ec4899", "stroke": "#f472b6"},
        {"name": "White", "color": "#e2e8f0", "stroke": "#ffffff"}
    ]

    team_colors_4 = [
        {"name": "Red", "color": "#ef4444", "stroke": "#f87171"},
        {"name": "Blue", "color": "#3b82f6", "stroke": "#60a5fa"},
        {"name": "Green", "color": "#22c55e", "stroke": "#4ade80"},
        {"name": "Yellow", "color": "#eab308", "stroke": "#fde047"}
    ]

    # ==========================================
    # 1. EggWars: Tea Party (8 Teams, Ring Layout)
    # ==========================================
    if map_id == "eggwars_tea_party":
        islands = []
        bridging_paths = []

        # Center Mid Island: Central Birthday Cake
        islands.append({
            "id": "mid",
            "name": "Central Birthday Cake (Mid)",
            "type": "mid",
            "x": cx,
            "y": cy,
            "radius": 54,
            "color": "#ec4899",
            "stroke": "#f472b6",
            "icon": "🎂",
            "generators": [{"type": "Diamond", "tier": 1, "count": 4, "rate_per_min": 8.0}],
            "description": "3-Tiered Birthday Cake: Houses 4 Diamond Gen Tier 1s producing 8 dia/min total. High vantage point for snipers."
        })

        # 4 Sub-Islands: Diamond Macarons
        sub_angles = [45, 135, 225, 315]
        for idx, ang in enumerate(sub_angles):
            sx, sy = _pt_on_circle(cx, cy, 165, ang)
            sub_id = f"sub_{idx + 1}"
            islands.append({
                "id": sub_id,
                "name": f"Macaron Sub-Island {idx + 1}",
                "type": "sub",
                "x": sx,
                "y": sy,
                "radius": 26,
                "color": "#10b981",
                "stroke": "#34d399",
                "icon": "💎",
                "generators": [{"type": "Diamond", "tier": 1, "count": 1, "rate_per_min": 2.0}],
                "description": f"Macaron Outpost {idx + 1}: 1 Diamond Gen Lv1. Key stepping stone for early 16-block diamond rush."
            })

            # Path from Sub to Mid
            bridging_paths.append({
                "id": f"path_{sub_id}_mid",
                "from_id": sub_id,
                "to_id": "mid",
                "from_name": f"Macaron {idx + 1}",
                "to_name": "Central Cake",
                "type": "sub_to_mid",
                "distance_blocks": 18,
                "jump_bridge_sec": 3.2,
                "sneak_bridge_sec": 11.3,
                "blocks_needed": 18,
                "danger_level": "Medium",
                "tactical_note": "Advance from Macaron to Central Cake under cover."
            })

        # 8 Starter Islands: Teapot Bases
        team_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        for idx, ang in enumerate(team_angles):
            tx, ty = _pt_on_circle(cx, cy, 285, ang)
            t_col = team_colors_8[idx]
            team_id = f"team_{idx + 1}"
            islands.append({
                "id": team_id,
                "name": f"Team {t_col['name']} Teapot",
                "type": "team",
                "team_name": t_col["name"],
                "x": tx,
                "y": ty,
                "radius": 34,
                "color": t_col["color"],
                "stroke": t_col["stroke"],
                "icon": "🛡️",
                "generators": [
                    {"type": "Iron", "tier": 1, "count": 1},
                    {"type": "Gold", "tier": 0, "count": 1, "note": "Locked (5 Dia)"}
                ],
                "egg": True,
                "description": f"Team {t_col['name']} Starter Teapot: 1 Iron Gen Lv1, 1 Gold Gen (locked), Egg placement in teapot bowl."
            })

            # Neighbor Rush Path (Ring)
            next_idx = (idx + 1) % 8
            next_team_id = f"team_{next_idx + 1}"
            bridging_paths.append({
                "id": f"path_{team_id}_{next_team_id}",
                "from_id": team_id,
                "to_id": next_team_id,
                "from_name": f"Team {t_col['name']}",
                "to_name": f"Team {team_colors_8[next_idx]['name']}",
                "type": "neighbor",
                "distance_blocks": 24,
                "jump_bridge_sec": 4.3,
                "sneak_bridge_sec": 15.0,
                "blocks_needed": 24,
                "danger_level": "Low",
                "tactical_note": "Fast 24-block neighbor rush across void in 4.3s before defense is reinforced."
            })

            # Direct Mid Bridge
            bridging_paths.append({
                "id": f"path_{team_id}_mid",
                "from_id": team_id,
                "to_id": "mid",
                "from_name": f"Team {t_col['name']}",
                "to_name": "Central Cake",
                "type": "mid",
                "distance_blocks": 32,
                "jump_bridge_sec": 5.7,
                "sneak_bridge_sec": 20.0,
                "blocks_needed": 32,
                "danger_level": "Medium",
                "tactical_note": "Direct bridge to center; exposed to crossfire from adjacent bases."
            })

            # Nearest Sub-Island Rush
            closest_sub_idx = (idx // 2) % 4 + 1
            sub_id = f"sub_{closest_sub_idx}"
            bridging_paths.append({
                "id": f"path_{team_id}_{sub_id}",
                "from_id": team_id,
                "to_id": sub_id,
                "from_name": f"Team {t_col['name']}",
                "to_name": f"Macaron {closest_sub_idx}",
                "type": "sub_rush",
                "distance_blocks": 16,
                "jump_bridge_sec": 2.9,
                "sneak_bridge_sec": 10.0,
                "blocks_needed": 16,
                "danger_level": "Low",
                "tactical_note": "Immediate diamond acquisition route: 16 blocks (2.9s jump-bridge)."
            })

        return {
            "view_box": "0 0 800 800",
            "center": {"x": cx, "y": cy},
            "rings": [
                {"radius": 165, "label": "Sub-Island Orbit (16 blk)"},
                {"radius": 285, "label": "Base Perimeter (24 blk neighbor)"}
            ],
            "islands": islands,
            "bridging_paths": bridging_paths
        }

    # ==========================================
    # 2. EggWars: Dwarven (4 Teams of 4, Quadrant)
    # ==========================================
    elif map_id == "eggwars_dwarven":
        islands = []
        bridging_paths = []

        # Center Mid Island: Great Central Forge
        islands.append({
            "id": "mid",
            "name": "Great Central Forge (Mid)",
            "type": "mid",
            "x": cx,
            "y": cy,
            "radius": 62,
            "color": "#f97316",
            "stroke": "#fb923c",
            "icon": "🌋",
            "generators": [{"type": "Diamond", "tier": 2, "count": 4, "rate_per_min": 16.0}],
            "description": "Massive fiery forge: Houses 4 Diamond Gen Tier 2s producing 16 dia/min total. Staircase ramps offer king-of-the-hill control."
        })

        # 4 Sub-Islands: Diamond Mine Shafts (Corners)
        sub_angles = [45, 135, 225, 315]
        sub_names = ["North-East Mine", "South-East Mine", "South-West Mine", "North-West Mine"]
        for idx, ang in enumerate(sub_angles):
            sx, sy = _pt_on_circle(cx, cy, 175, ang)
            sub_id = f"sub_{idx + 1}"
            islands.append({
                "id": sub_id,
                "name": f"Diamond Shaft {idx + 1} ({sub_names[idx]})",
                "type": "sub",
                "x": sx,
                "y": sy,
                "radius": 27,
                "color": "#00e5ff",
                "stroke": "#38bdf8",
                "icon": "💎",
                "generators": [{"type": "Diamond", "tier": 1, "count": 1, "rate_per_min": 2.0}],
                "description": f"Mine Shaft outpost with 1 Diamond Gen Lv1. Protected by stone crags."
            })

            # Sub to Mid Bridge
            bridging_paths.append({
                "id": f"path_{sub_id}_mid",
                "from_id": sub_id,
                "to_id": "mid",
                "from_name": f"Mine {idx + 1}",
                "to_name": "Central Forge",
                "type": "sub_to_mid",
                "distance_blocks": 24,
                "jump_bridge_sec": 4.3,
                "sneak_bridge_sec": 15.0,
                "blocks_needed": 24,
                "danger_level": "Medium",
                "tactical_note": "Advance into the forge under rafter arches."
            })

        # 4 Cardinal Starter Bastions (North, East, South, West)
        bastion_angles = [270, 0, 90, 180] # North, East, South, West
        for idx, ang in enumerate(bastion_angles):
            tx, ty = _pt_on_circle(cx, cy, 290, ang)
            t_col = team_colors_4[idx]
            team_id = f"team_{idx + 1}"
            islands.append({
                "id": team_id,
                "name": f"Team {t_col['name']} Dwarf Bastion",
                "type": "team",
                "team_name": t_col["name"],
                "x": tx,
                "y": ty,
                "radius": 42,
                "color": t_col["color"],
                "stroke": t_col["stroke"],
                "icon": "🏰",
                "generators": [
                    {"type": "Iron", "tier": 1, "count": 2},
                    {"type": "Gold", "tier": 1, "count": 1}
                ],
                "egg": True,
                "description": f"Team {t_col['name']} Bastion: 2 Iron Gens Lv1, 1 Gold Gen Lv1. Heavy starting iron economy."
            })

            # Bastion to Bastion neighbor rush
            next_idx = (idx + 1) % 4
            next_team_id = f"team_{next_idx + 1}"
            bridging_paths.append({
                "id": f"path_{team_id}_{next_team_id}",
                "from_id": team_id,
                "to_id": next_team_id,
                "from_name": f"Team {t_col['name']}",
                "to_name": f"Team {team_colors_4[next_idx]['name']}",
                "type": "neighbor",
                "distance_blocks": 28,
                "jump_bridge_sec": 5.0,
                "sneak_bridge_sec": 17.5,
                "blocks_needed": 28,
                "danger_level": "Medium",
                "tactical_note": "Bridge over fiery lava void; knockbacks are lethal."
            })

            # Direct Mid Bridge
            bridging_paths.append({
                "id": f"path_{team_id}_mid",
                "from_id": team_id,
                "to_id": "mid",
                "from_name": f"Team {t_col['name']}",
                "to_name": "Central Forge",
                "type": "mid",
                "distance_blocks": 42,
                "jump_bridge_sec": 7.5,
                "sneak_bridge_sec": 26.3,
                "blocks_needed": 42,
                "danger_level": "High",
                "tactical_note": "Long 42-block bridge exposed to high forge snipers."
            })

            # Bastion to nearest 2 Mine Shafts
            sub_1 = f"sub_{idx + 1}"
            sub_2 = f"sub_{((idx + 3) % 4) + 1}"
            bridging_paths.append({
                "id": f"path_{team_id}_{sub_1}",
                "from_id": team_id,
                "to_id": sub_1,
                "from_name": f"Team {t_col['name']}",
                "to_name": f"Mine {idx + 1}",
                "type": "sub_rush",
                "distance_blocks": 18,
                "jump_bridge_sec": 3.2,
                "sneak_bridge_sec": 11.3,
                "blocks_needed": 18,
                "danger_level": "Low",
                "tactical_note": "Safest route for solo miner gathering early upgrades."
            })

        return {
            "view_box": "0 0 800 800",
            "center": {"x": cx, "y": cy},
            "rings": [
                {"radius": 175, "label": "Mine Shaft Orbit (18 blk)"},
                {"radius": 290, "label": "Bastion Perimeter (28 blk neighbor)"}
            ],
            "islands": islands,
            "bridging_paths": bridging_paths
        }

    # ==========================================
    # 3. EggWars: Atlantis (8 Teams, Ring Layout)
    # ==========================================
    elif map_id == "eggwars_atlantis":
        islands = []
        bridging_paths = []

        islands.append({
            "id": "mid",
            "name": "Trident Sanctuary (Mid)",
            "type": "mid",
            "x": cx,
            "y": cy,
            "radius": 56,
            "color": "#06b6d4",
            "stroke": "#22d3ee",
            "icon": "🔱",
            "generators": [{"type": "Diamond", "tier": 1, "count": 4, "rate_per_min": 8.0}],
            "description": "Sunken ocean temple: 4 Diamond Gen Tier 1s. High arches allow ender-pearl drops and bow denial."
        })

        sub_angles = [45, 135, 225, 315]
        for idx, ang in enumerate(sub_angles):
            sx, sy = _pt_on_circle(cx, cy, 165, ang)
            sub_id = f"sub_{idx + 1}"
            islands.append({
                "id": sub_id,
                "name": f"Coral Reef Outpost {idx + 1}",
                "type": "sub",
                "x": sx,
                "y": sy,
                "radius": 26,
                "color": "#14b8a6",
                "stroke": "#2dd4bf",
                "icon": "💎",
                "generators": [{"type": "Diamond", "tier": 1, "count": 1, "rate_per_min": 2.0}],
                "description": f"Coral Reef {idx + 1}: 1 Diamond Gen Lv1. Natural pearl launch platform."
            })

            bridging_paths.append({
                "id": f"path_{sub_id}_mid",
                "from_id": sub_id,
                "to_id": "mid",
                "from_name": f"Coral {idx + 1}",
                "to_name": "Trident Sanctuary",
                "type": "sub_to_mid",
                "distance_blocks": 19,
                "jump_bridge_sec": 3.4,
                "sneak_bridge_sec": 11.9,
                "blocks_needed": 19,
                "danger_level": "Medium",
                "tactical_note": "Bridge under water arches to sanctuary."
            })

        team_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        for idx, ang in enumerate(team_angles):
            tx, ty = _pt_on_circle(cx, cy, 285, ang)
            t_col = team_colors_8[idx]
            team_id = f"team_{idx + 1}"
            islands.append({
                "id": team_id,
                "name": f"Team {t_col['name']} Temple",
                "type": "team",
                "team_name": t_col["name"],
                "x": tx,
                "y": ty,
                "radius": 34,
                "color": t_col["color"],
                "stroke": t_col["stroke"],
                "icon": "🛡️",
                "generators": [
                    {"type": "Iron", "tier": 1, "count": 1},
                    {"type": "Gold", "tier": 0, "count": 1, "note": "Locked (5 Dia)"}
                ],
                "egg": True,
                "description": f"Team {t_col['name']} Temple: 1 Iron Gen Lv1, 1 Gold Gen (locked)."
            })

            next_idx = (idx + 1) % 8
            next_team_id = f"team_{next_idx + 1}"
            bridging_paths.append({
                "id": f"path_{team_id}_{next_team_id}",
                "from_id": team_id,
                "to_id": next_team_id,
                "from_name": f"Team {t_col['name']}",
                "to_name": f"Team {team_colors_8[next_idx]['name']}",
                "type": "neighbor",
                "distance_blocks": 30,
                "jump_bridge_sec": 5.4,
                "sneak_bridge_sec": 18.8,
                "blocks_needed": 30,
                "danger_level": "Medium",
                "tactical_note": "Flank via sub-island rather than direct line."
            })

            bridging_paths.append({
                "id": f"path_{team_id}_mid",
                "from_id": team_id,
                "to_id": "mid",
                "from_name": f"Team {t_col['name']}",
                "to_name": "Trident Sanctuary",
                "type": "mid",
                "distance_blocks": 36,
                "jump_bridge_sec": 6.4,
                "sneak_bridge_sec": 22.5,
                "blocks_needed": 36,
                "danger_level": "High",
                "tactical_note": "Bridge under temple arches to shield against overhead arrows."
            })

            closest_sub_idx = (idx // 2) % 4 + 1
            sub_id = f"sub_{closest_sub_idx}"
            bridging_paths.append({
                "id": f"path_{team_id}_{sub_id}",
                "from_id": team_id,
                "to_id": sub_id,
                "from_name": f"Team {t_col['name']}",
                "to_name": f"Coral {closest_sub_idx}",
                "type": "sub_rush",
                "distance_blocks": 20,
                "jump_bridge_sec": 3.6,
                "sneak_bridge_sec": 12.5,
                "blocks_needed": 20,
                "danger_level": "Low",
                "tactical_note": "Primary opening move: 20 blocks for 2 dia/min."
            })

        return {
            "view_box": "0 0 800 800",
            "center": {"x": cx, "y": cy},
            "rings": [
                {"radius": 165, "label": "Coral Reef Orbit (20 blk)"},
                {"radius": 285, "label": "Temple Perimeter (30 blk neighbor)"}
            ],
            "islands": islands,
            "bridging_paths": bridging_paths
        }

    # ==========================================
    # 4. EggWars: Toys (4 Teams of 4, Quadrant)
    # ==========================================
    elif map_id == "eggwars_toys":
        islands = []
        bridging_paths = []

        islands.append({
            "id": "mid",
            "name": "Lego Fortress & Robot (Mid)",
            "type": "mid",
            "x": cx,
            "y": cy,
            "radius": 60,
            "color": "#a855f7",
            "stroke": "#c084fc",
            "icon": "🤖",
            "generators": [{"type": "Diamond", "tier": 1, "count": 4, "rate_per_min": 8.0}],
            "description": "Giant Lego Robot Center: 4 Diamond Gen Tier 1s. Multi-level plastic blocks offer cover."
        })

        sub_angles = [45, 135, 225, 315]
        for idx, ang in enumerate(sub_angles):
            sx, sy = _pt_on_circle(cx, cy, 170, ang)
            sub_id = f"sub_{idx + 1}"
            islands.append({
                "id": sub_id,
                "name": f"Wooden Train Station {idx + 1}",
                "type": "sub",
                "x": sx,
                "y": sy,
                "radius": 26,
                "color": "#10b981",
                "stroke": "#34d399",
                "icon": "💎",
                "generators": [{"type": "Diamond", "tier": 1, "count": 1, "rate_per_min": 2.0}],
                "description": f"Toy Train Station {idx + 1}: 1 Diamond Gen Lv1."
            })

            bridging_paths.append({
                "id": f"path_{sub_id}_mid",
                "from_id": sub_id,
                "to_id": "mid",
                "from_name": f"Train {idx + 1}",
                "to_name": "Lego Fortress",
                "type": "sub_to_mid",
                "distance_blocks": 21,
                "jump_bridge_sec": 3.8,
                "sneak_bridge_sec": 13.1,
                "blocks_needed": 21,
                "danger_level": "Medium",
                "tactical_note": "Bridge into robot legs for quick mid diamonds."
            })

        bastion_angles = [270, 0, 90, 180]
        for idx, ang in enumerate(bastion_angles):
            tx, ty = _pt_on_circle(cx, cy, 285, ang)
            t_col = team_colors_4[idx]
            team_id = f"team_{idx + 1}"
            islands.append({
                "id": team_id,
                "name": f"Team {t_col['name']} Toy Box",
                "type": "team",
                "team_name": t_col["name"],
                "x": tx,
                "y": ty,
                "radius": 40,
                "color": t_col["color"],
                "stroke": t_col["stroke"],
                "icon": "🧸",
                "generators": [
                    {"type": "Iron", "tier": 1, "count": 1},
                    {"type": "Gold", "tier": 1, "count": 1}
                ],
                "egg": True,
                "description": f"Team {t_col['name']} Toy Box: 1 Iron Lv1, 1 Gold Lv1. Fast initial block crafting."
            })

            next_idx = (idx + 1) % 4
            next_team_id = f"team_{next_idx + 1}"
            bridging_paths.append({
                "id": f"path_{team_id}_{next_team_id}",
                "from_id": team_id,
                "to_id": next_team_id,
                "from_name": f"Team {t_col['name']}",
                "to_name": f"Team {team_colors_4[next_idx]['name']}",
                "type": "neighbor",
                "distance_blocks": 26,
                "jump_bridge_sec": 4.6,
                "sneak_bridge_sec": 16.3,
                "blocks_needed": 26,
                "danger_level": "Medium",
                "tactical_note": "Rush neighboring toy box before they purchase obsidian."
            })

            bridging_paths.append({
                "id": f"path_{team_id}_mid",
                "from_id": team_id,
                "to_id": "mid",
                "from_name": f"Team {t_col['name']}",
                "to_name": "Lego Fortress",
                "type": "mid",
                "distance_blocks": 38,
                "jump_bridge_sec": 6.8,
                "sneak_bridge_sec": 23.8,
                "blocks_needed": 38,
                "danger_level": "High",
                "tactical_note": "Direct bridge to Lego fortress."
            })

            sub_1 = f"sub_{idx + 1}"
            bridging_paths.append({
                "id": f"path_{team_id}_{sub_1}",
                "from_id": team_id,
                "to_id": sub_1,
                "from_name": f"Team {t_col['name']}",
                "to_name": f"Train {idx + 1}",
                "type": "sub_rush",
                "distance_blocks": 17,
                "jump_bridge_sec": 3.0,
                "sneak_bridge_sec": 10.6,
                "blocks_needed": 17,
                "danger_level": "Low",
                "tactical_note": "Fast 17-block opening rush to secure diamonds."
            })

        return {
            "view_box": "0 0 800 800",
            "center": {"x": cx, "y": cy},
            "rings": [
                {"radius": 170, "label": "Train Station Orbit (17 blk)"},
                {"radius": 285, "label": "Toy Box Perimeter (26 blk neighbor)"}
            ],
            "islands": islands,
            "bridging_paths": bridging_paths
        }

    # ==========================================
    # 5. SkyWars: Trees (12 Players)
    # ==========================================
    elif map_id == "skywars_trees":
        islands = []
        bridging_paths = []

        islands.append({
            "id": "mid",
            "name": "Mother Tree Roots & Canopy (Mid)",
            "type": "mid",
            "x": cx,
            "y": cy,
            "radius": 64,
            "color": "#16a34a",
            "stroke": "#4ade80",
            "icon": "🌳",
            "generators": [{"type": "Chest Loot", "tier": "OP", "count": 6}],
            "description": "Massive redwood core: 6 Overpowered/Diamond chests. Heart of the match."
        })

        for i in range(12):
            ang = i * 30
            tx, ty = _pt_on_circle(cx, cy, 275, ang)
            tree_id = f"tree_{i + 1}"
            islands.append({
                "id": tree_id,
                "name": f"Redwood Tree #{i + 1}",
                "type": "team",
                "x": tx,
                "y": ty,
                "radius": 28,
                "color": "#0d9488",
                "stroke": "#2dd4bf",
                "icon": "🌲",
                "generators": [{"type": "Chest Loot", "tier": "Basic", "count": 3}],
                "description": f"Starter Tree #{i + 1}: 3 chests (1 canopy, 2 base)."
            })

            # Neighbor Rush Path
            next_tree_id = f"tree_{(i + 1) % 12 + 1}"
            bridging_paths.append({
                "id": f"path_{tree_id}_{next_tree_id}",
                "from_id": tree_id,
                "to_id": next_tree_id,
                "from_name": f"Tree #{i + 1}",
                "to_name": f"Tree #{(i + 1) % 12 + 1}",
                "type": "neighbor",
                "distance_blocks": 18,
                "jump_bridge_sec": 3.2,
                "sneak_bridge_sec": 11.3,
                "blocks_needed": 18,
                "danger_level": "High",
                "tactical_note": "Kill neighbor while they are in chest inventory (3.2s rush)."
            })

            # Mid Path
            bridging_paths.append({
                "id": f"path_{tree_id}_mid",
                "from_id": tree_id,
                "to_id": "mid",
                "from_name": f"Tree #{i + 1}",
                "to_name": "Mother Tree",
                "type": "mid",
                "distance_blocks": 26,
                "jump_bridge_sec": 4.6,
                "sneak_bridge_sec": 16.3,
                "blocks_needed": 26,
                "danger_level": "High",
                "tactical_note": "Bridge directly to Mother Tree roots for enchanted gear."
            })

        return {
            "view_box": "0 0 800 800",
            "center": {"x": cx, "y": cy},
            "rings": [
                {"radius": 150, "label": "Mid Canopy Buffer"},
                {"radius": 275, "label": "Redwood Ring (18 blk neighbor)"}
            ],
            "islands": islands,
            "bridging_paths": bridging_paths
        }

    # ==========================================
    # 6. SkyWars: Rainbow (12 Players)
    # ==========================================
    elif map_id == "skywars_rainbow":
        islands = []
        bridging_paths = []

        islands.append({
            "id": "mid",
            "name": "Pot of Gold Cloud (Mid)",
            "type": "mid",
            "x": cx,
            "y": cy,
            "radius": 54,
            "color": "#eab308",
            "stroke": "#fde047",
            "icon": "🍯",
            "generators": [{"type": "Chest Loot", "tier": "OP", "count": 8}],
            "description": "Glittering golden pot: 8 stacked chests containing Punch bows and pearls."
        })

        rainbow_colors = ["#f87171", "#fb923c", "#fde047", "#4ade80", "#22d3ee", "#818cf8",
                          "#c084fc", "#f472b6", "#fda4af", "#67e8f9", "#a7f3d0", "#fef08a"]

        for i in range(12):
            ang = i * 30
            cx_cloud, cy_cloud = _pt_on_circle(cx, cy, 260, ang)
            cloud_id = f"cloud_{i + 1}"
            islands.append({
                "id": cloud_id,
                "name": f"Cloud Isle #{i + 1}",
                "type": "team",
                "x": cx_cloud,
                "y": cy_cloud,
                "radius": 26,
                "color": rainbow_colors[i],
                "stroke": "#ffffff",
                "icon": "☁️",
                "generators": [{"type": "Chest Loot", "tier": "Basic", "count": 3}],
                "description": f"Fluffy Cloud #{i + 1}: 3 starter chests."
            })

            next_cloud_id = f"cloud_{(i + 1) % 12 + 1}"
            bridging_paths.append({
                "id": f"path_{cloud_id}_{next_cloud_id}",
                "from_id": cloud_id,
                "to_id": next_cloud_id,
                "from_name": f"Cloud #{i + 1}",
                "to_name": f"Cloud #{(i + 1) % 12 + 1}",
                "type": "neighbor",
                "distance_blocks": 16,
                "jump_bridge_sec": 2.9,
                "sneak_bridge_sec": 10.0,
                "blocks_needed": 16,
                "danger_level": "Extreme",
                "tactical_note": "Ultra-fast 16-block rush! Match often decided in first 5 seconds."
            })

            bridging_paths.append({
                "id": f"path_{cloud_id}_mid",
                "from_id": cloud_id,
                "to_id": "mid",
                "from_name": f"Cloud #{i + 1}",
                "to_name": "Pot of Gold",
                "type": "mid",
                "distance_blocks": 22,
                "jump_bridge_sec": 3.9,
                "sneak_bridge_sec": 13.8,
                "blocks_needed": 22,
                "danger_level": "High",
                "tactical_note": "Sprint to pot of gold to acquire Punch I bow."
            })

        return {
            "view_box": "0 0 800 800",
            "center": {"x": cx, "y": cy},
            "rings": [
                {"radius": 140, "label": "Golden Rainbow Track"},
                {"radius": 260, "label": "Cloud Isle Perimeter (16 blk rush)"}
            ],
            "islands": islands,
            "bridging_paths": bridging_paths
        }

    # ==========================================
    # 7. SkyWars: Magic (12 Players)
    # ==========================================
    elif map_id == "skywars_magic":
        islands = []
        bridging_paths = []

        islands.append({
            "id": "mid",
            "name": "Arcane Spire & Spellbook (Mid)",
            "type": "mid",
            "x": cx,
            "y": cy,
            "radius": 58,
            "color": "#8b5cf6",
            "stroke": "#a78bfa",
            "icon": "🔮",
            "generators": [{"type": "Chest Loot", "tier": "OP", "count": 6}],
            "description": "Floating Arcane Spire: 6 Overpowered chests with splash potions and enchanted bows."
        })

        for i in range(12):
            ang = i * 30
            tx, ty = _pt_on_circle(cx, cy, 270, ang)
            tower_id = f"tower_{i + 1}"
            islands.append({
                "id": tower_id,
                "name": f"Wizard Tower #{i + 1}",
                "type": "team",
                "x": tx,
                "y": ty,
                "radius": 27,
                "color": "#6366f1",
                "stroke": "#818cf8",
                "icon": "⚡",
                "generators": [{"type": "Chest Loot", "tier": "Basic", "count": 3}],
                "description": f"Wizard Spire #{i + 1}: 3 starter chests."
            })

            next_tower_id = f"tower_{(i + 1) % 12 + 1}"
            bridging_paths.append({
                "id": f"path_{tower_id}_{next_tower_id}",
                "from_id": tower_id,
                "to_id": next_tower_id,
                "from_name": f"Tower #{i + 1}",
                "to_name": f"Tower #{(i + 1) % 12 + 1}",
                "type": "neighbor",
                "distance_blocks": 19,
                "jump_bridge_sec": 3.4,
                "sneak_bridge_sec": 11.9,
                "blocks_needed": 19,
                "danger_level": "High",
                "tactical_note": "Fast 19-block tower flank with speed potion."
            })

            bridging_paths.append({
                "id": f"path_{tower_id}_mid",
                "from_id": tower_id,
                "to_id": "mid",
                "from_name": f"Tower #{i + 1}",
                "to_name": "Arcane Spire",
                "type": "mid",
                "distance_blocks": 28,
                "jump_bridge_sec": 5.0,
                "sneak_bridge_sec": 17.5,
                "blocks_needed": 28,
                "danger_level": "High",
                "tactical_note": "Direct bridge to arcane spellbook center."
            })

        return {
            "view_box": "0 0 800 800",
            "center": {"x": cx, "y": cy},
            "rings": [
                {"radius": 145, "label": "Astral Arc Buffer"},
                {"radius": 270, "label": "Tower Orbit (19 blk neighbor)"}
            ],
            "islands": islands,
            "bridging_paths": bridging_paths
        }

    return None
