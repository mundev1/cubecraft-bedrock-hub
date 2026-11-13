"""
Unit Tests for CubeCraft Bedrock Official Discord Bot
====================================================
Tests bot data queries, embed generation, leaderboard lookups,
marketplace search, encounter reviews, and map blueprints.
"""
import unittest
import sqlite3
import os
import discord
from discord_bot import (
    fetch_player_full_data,
    fetch_top_leaderboard,
    MAP_CHOICES,
    POPULAR_GAMES,
    bot
)
from database import (
    search_marketplace_items,
    insert_encounter,
    get_player_encounters,
    get_cross_mode_masters,
    get_live_online_count,
    get_server_tracker_stats,
    get_map_strategy_detail
)
from discord_exporter import (
    build_player_discord_embed,
    build_leaderboard_champion_discord_embed,
    build_server_status_discord_embed,
    build_map_tactics_discord_embed
)

class TestDiscordBotEngine(unittest.TestCase):

    def test_fetch_player_embed_generation(self):
        """Test looking up a player and building a native discord.Embed."""
        player_data, encounters = fetch_player_full_data("MundevPolite")
        self.assertIsNotNone(player_data)
        self.assertEqual(player_data["gamertag"], "MundevPolite")

        res = build_player_discord_embed(player_data, encounters or [])
        embed = discord.Embed.from_dict(res["embed"])

        self.assertIn("MundevPolite", embed.title)
        self.assertTrue(len(embed.fields) >= 3)
        self.assertIn("mc-heads.net", embed.thumbnail.url)

    def test_fetch_top_leaderboard_embed(self):
        """Test retrieving leaderboard standings and champion embed."""
        rows = fetch_top_leaderboard("EggWars", "Solo", limit=10)
        self.assertGreater(len(rows), 0)
        self.assertEqual(rows[0]["rank"], 1)

        champ_dict = build_leaderboard_champion_discord_embed("EggWars", "Solo", rows[0], rows[1] if len(rows) > 1 else None)
        embed = discord.Embed.from_dict(champ_dict["embed"])

        self.assertIn("EggWars", embed.title)
        self.assertEqual(embed.fields[0].name, "👑 Reigning #1 Champion")
        self.assertIn(rows[0]["player_gamertag"], embed.fields[0].value)

    def test_server_status_embed(self):
        """Test server online count and grinding window embed."""
        online = get_live_online_count()
        self.assertIsInstance(online, int)
        self.assertGreater(online, 0)

        stats = get_server_tracker_stats()
        res = build_server_status_discord_embed(online, stats["peak_window"], stats["offpeak_window"])
        embed = discord.Embed.from_dict(res["embed"])

        self.assertIn("Server Status", embed.title)
        self.assertEqual(embed.color.value, 0x10B981)

    def test_map_tactics_embed(self):
        """Test map strategy blueprint embed generation for all 7 maps."""
        for choice in MAP_CHOICES:
            map_data = get_map_strategy_detail(choice.value)
            self.assertIsNotNone(map_data, f"Map data missing for {choice.value}")

            res = build_map_tactics_discord_embed(map_data)
            embed = discord.Embed.from_dict(res["embed"])

            self.assertIn(map_data["name"], embed.title)
            self.assertTrue(len(embed.fields) >= 3)

    def test_marketplace_search_items(self):
        """Test searching authentic Marketplace items with price and thumbnail."""
        items, total = search_marketplace_items(query="dragon", category="all", limit=3)
        self.assertIsInstance(items, list)
        self.assertGreater(total, 0)
        if items:
            self.assertIn("price_minecoins", items[0])
            self.assertIn("rating", items[0])
            self.assertIn("title", items[0])

    def test_encounter_review_flow(self):
        """Test inserting a Discord encounter review and reading it back."""
        test_gt = "TestDiscordBotPlayer"
        success, res = insert_encounter(
            player_gamertag=test_gt,
            reviewer_name="DiscordTester#0001",
            sentiment="Helpful",
            comment="Awesome teammate, shared diamond gens on Tea Party!",
            game="EggWars",
            mode="Solo"
        )
        self.assertTrue(success)
        self.assertIn("id", res)

        encs = get_player_encounters(test_gt, limit=5)
        self.assertGreaterEqual(len(encs), 1)
        self.assertEqual(encs[0]["reviewer_name"], "DiscordTester#0001")
        self.assertEqual(encs[0]["sentiment"], "positive")

    def test_cross_mode_masters(self):
        """Test Cross-Mode Dominance calculation."""
        masters = get_cross_mode_masters(limit=10)
        self.assertIsInstance(masters, list)
        self.assertGreater(len(masters), 0)
        self.assertGreaterEqual(masters[0]["distinct_games"], 1)

    def test_bot_commands_registered(self):
        """Verify that all commands and slash commands are registered on the bot."""
        command_names = [c.name for c in bot.commands]
        expected_cmds = ["player", "top", "server", "map", "market", "masters", "ping", "help"]
        for expected in expected_cmds:
            self.assertIn(expected, command_names, f"Missing prefix command: {expected}")

        tree_commands = [c.name for c in bot.tree.get_commands()]
        expected_slash = ["player", "leaderboard", "server", "map", "marketplace", "review", "masters", "ping", "help"]
        for expected in expected_slash:
            self.assertIn(expected, tree_commands, f"Missing slash command: {expected}")

    def test_autocomplete_handler(self):
        """Test autocomplete interaction handling for game, mode, and map_name."""
        import json
        import nacl.signing
        from discord_interactions_handler import handle_discord_interaction

        key = nacl.signing.SigningKey.generate()
        pub_hex = key.verify_key.encode().hex()
        old_key = os.environ.get("DISCORD_PUBLIC_KEY")
        os.environ["DISCORD_PUBLIC_KEY"] = pub_hex

        try:
            payload = {
                "type": 4,
                "data": {
                    "name": "leaderboard",
                    "options": [{"name": "game", "value": "egg", "focused": True}]
                }
            }
            raw_body = json.dumps(payload).encode("utf-8")
            ts = "12345678"
            msg = ts.encode("utf-8") + raw_body
            sig = key.sign(msg).signature.hex()

            headers = {"X-Signature-Ed25519": sig, "X-Signature-Timestamp": ts}
            res, status = handle_discord_interaction(raw_body, headers)
            self.assertEqual(status, 200)
            self.assertEqual(res["type"], 8)
            choices = res["data"]["choices"]
            self.assertTrue(any(c["name"] == "EggWars" for c in choices))
        finally:
            if old_key is not None:
                os.environ["DISCORD_PUBLIC_KEY"] = old_key
            else:
                os.environ.pop("DISCORD_PUBLIC_KEY", None)

if __name__ == "__main__":
    unittest.main()
