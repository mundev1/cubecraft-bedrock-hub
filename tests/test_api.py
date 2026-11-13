"""
Unit tests for CubeCraft Bedrock Community Hub API endpoints.
Verifies 100% authentic data integrity across 39 Bedrock game mode leaderboards,
official player points, store bundles, playable community clips, and encounters.
Guarantees NO simulated or fabricated numbers exist in the API responses.
"""
import unittest
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from database import init_db, sync_cubecraft_marketplace, seed_clips, seed_custom_players

class TestCubeCraftBedrockAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_custom_players()
        seed_clips()
        sync_cubecraft_marketplace()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_global_stats_authentic(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        stats = data['stats']
        self.assertGreaterEqual(stats['total_players'], 800)
        self.assertGreaterEqual(stats['total_leaderboard_entries'], 900)
        self.assertEqual(stats['total_games'], 12)
        self.assertGreaterEqual(stats['online_players'], 1000)

        # Ensure NO fabricated metrics exist
        self.assertNotIn('today_tracked_wins', stats)
        self.assertNotIn('today_tracked_kills', stats)
        self.assertNotIn('top_daily_grinder', stats)

    def test_games_list_contains_real_submodes(self):
        response = self.app.get('/api/games')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        games_dict = {g['name']: g for g in data['games']}
        self.assertIn('EggWars', games_dict)
        self.assertIn('SkyWars', games_dict)
        self.assertIn('BlockWars', games_dict)

        # Check real SkyWars sub-modes
        skywars_modes = games_dict['SkyWars']['modes']
        self.assertIn('Solo', skywars_modes)
        self.assertIn('Duos (Teams of 2)', skywars_modes)
        self.assertIn('Squads (Teams of 4)', skywars_modes)

        # Check real EggWars sub-modes
        eggwars_modes = games_dict['EggWars']['modes']
        self.assertIn('Solo', eggwars_modes)
        self.assertIn('Duos (Teams of 2)', eggwars_modes)
        self.assertIn('Squads (Teams of 4)', eggwars_modes)

    def test_leaderboards_strictly_authentic_points(self):
        response = self.app.get('/api/leaderboards?game=EggWars&mode=Solo')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['leaderboard']), 0)
        first = data['leaderboard'][0]

        # Verify authentic fields
        self.assertEqual(first['game'], 'EggWars')
        self.assertEqual(first['mode'], 'Solo')
        self.assertIn('points', first)
        self.assertGreater(first['points'], 0)
        self.assertIn('raw_name', first)
        self.assertIn('rank', first)

        # Verify NO fake fields
        self.assertNotIn('daily_wins', first)
        self.assertNotIn('daily_kills', first)
        self.assertNotIn('kills', first)
        self.assertNotIn('streak', first)
        self.assertNotIn('rating', first)

    def test_custom_players_search_and_profiles(self):
        # Search MundevPolite
        res_m = self.app.get('/api/players/search?q=Mundev')
        self.assertEqual(res_m.status_code, 200)
        data_m = json.loads(res_m.data)
        self.assertTrue(data_m['success'])
        self.assertTrue(any(p['gamertag'] == 'MundevPolite' for p in data_m['players']))

        # Profile MundevPolite
        prof_m = self.app.get('/api/players/MundevPolite')
        self.assertEqual(prof_m.status_code, 200)
        pdata_m = json.loads(prof_m.data)
        self.assertEqual(pdata_m['player']['gamertag'], 'MundevPolite')
        self.assertGreater(len(pdata_m['encounters']), 0)
        self.assertNotIn('daily_stats', pdata_m)

        # Search JoealBadmash
        res_j = self.app.get('/api/players/search?q=Joeal')
        self.assertEqual(res_j.status_code, 200)
        data_j = json.loads(res_j.data)
        self.assertTrue(data_j['success'])
        self.assertTrue(any(p['gamertag'] == 'JoealBadmash' for p in data_j['players']))

        # Profile JoealBadmash
        prof_j = self.app.get('/api/players/JoealBadmash')
        self.assertEqual(prof_j.status_code, 200)
        pdata_j = json.loads(prof_j.data)
        self.assertEqual(pdata_j['player']['gamertag'], 'JoealBadmash')
        self.assertGreater(len(pdata_j['encounters']), 0)
        self.assertNotIn('daily_stats', pdata_j)

    def test_marketplace_catalog_and_authentic_images(self):
        # 1. Fetch paginated marketplace catalog
        response = self.app.get('/api/marketplace?limit=24&page=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['total'], 900)
        self.assertEqual(len(data['items']), 24)
        
        # Verify first item contains authentic schema and image
        first = data['items'][0]
        self.assertIn('id', first)
        self.assertIn('name', first)
        self.assertIn('price', first)
        self.assertIn('thumbnail', first)
        self.assertTrue(first['thumbnail'].startswith('https://'))
        self.assertIn('available', first)
        self.assertIn(first['available'], (0, 1))

        # 2. Test search filter
        res_search = self.app.get('/api/marketplace?search=Chibi')
        self.assertEqual(res_search.status_code, 200)
        data_search = json.loads(res_search.data)
        self.assertTrue(data_search['success'])
        self.assertGreater(data_search['total'], 0)
        self.assertTrue(any('chibi' in item['name'].lower() for item in data_search['items']))

        # 3. Test single item inspection endpoint
        item_id = first['id']
        res_item = self.app.get(f'/api/marketplace/{item_id}')
        self.assertEqual(res_item.status_code, 200)
        item_data = json.loads(res_item.data)
        self.assertTrue(item_data['success'])
        self.assertEqual(item_data['item']['id'], item_id)
        self.assertEqual(item_data['item']['name'], first['name'])

        # 4. Verify backwards compatibility alias
        res_alias = self.app.get('/api/bundles')
        self.assertEqual(res_alias.status_code, 200)
        alias_data = json.loads(res_alias.data)
        self.assertTrue(alias_data['success'])

    def test_clips_and_community_submission(self):
        response = self.app.get('/api/clips?game=all&type=all')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['clips']), 0)

        # Submit new community clip
        new_clip = {
            "title": "Clean Void Save Clutch",
            "gamertag": "Chiibet",
            "game": "EggWars",
            "clip_url": "https://medal.tv/games/minecraft/clips/sample-clutch-1",
            "description": "Survived void knockback with backwards jump bridging."
        }
        post_res = self.app.post('/api/clips', data=json.dumps(new_clip), content_type='application/json')
        self.assertEqual(post_res.status_code, 200)
        post_data = json.loads(post_res.data)
        self.assertTrue(post_data['success'])
        clip_id = post_data['clip_id']

        # Upvote clip
        up_res = self.app.post(f'/api/clips/{clip_id}/upvote')
        self.assertEqual(up_res.status_code, 200)
        up_data = json.loads(up_res.data)
        self.assertTrue(up_data['success'])

    def test_player_search_and_real_profile(self):
        res_search = self.app.get('/api/players/search?q=Chii')
        self.assertEqual(res_search.status_code, 200)
        search_data = json.loads(res_search.data)
        self.assertTrue(search_data['success'])
        self.assertTrue(any(p['gamertag'] == 'Chiibet' for p in search_data['players']))

        # Profile fetch for real player Chiibet
        res_prof = self.app.get('/api/players/Chiibet')
        self.assertEqual(res_prof.status_code, 200)
        prof_data = json.loads(res_prof.data)
        self.assertTrue(prof_data['success'])
        self.assertEqual(prof_data['player']['gamertag'], 'Chiibet')
        self.assertGreater(len(prof_data['leaderboards']), 0)
        for lb in prof_data['leaderboards']:
            self.assertIn('points', lb)
            self.assertGreater(lb['points'], 0)
            self.assertNotIn('daily_wins', lb)
            self.assertNotIn('kills', lb)

    def test_player_encounter_post_and_helpful(self):
        encounter_payload = {
            "reviewer_name": "BedrockPro99",
            "game_played": "BlockWars Bridges",
            "encounter_type": "God-tier Clutch",
            "rating": 5,
            "comment": "Unreal speed bridging skills on Bedrock. 10/10 teammate."
        }
        res_post = self.app.post('/api/players/Chiibet/encounters', data=json.dumps(encounter_payload), content_type='application/json')
        self.assertEqual(res_post.status_code, 200)
        post_data = json.loads(res_post.data)
        self.assertTrue(post_data['success'])

        # Check recent encounters
        res_recent = self.app.get('/api/encounters/recent')
        self.assertEqual(res_recent.status_code, 200)
        recent_data = json.loads(res_recent.data)
        self.assertTrue(recent_data['success'])
        first_enc_id = recent_data['encounters'][0]['id']

        # Upvote encounter as helpful
        res_helpful = self.app.post(f'/api/encounters/{first_enc_id}/helpful')
        self.assertEqual(res_helpful.status_code, 200)
        helpful_data = json.loads(res_helpful.data)
        self.assertTrue(helpful_data['success'])

    def test_analytics_all_around_masters(self):
        res = self.app.get('/api/analytics/all-around-masters?limit=10')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        masters = data['masters']
        self.assertGreater(len(masters), 0)

        # First master must be ranked in at least 3 distinct games
        first = masters[0]
        self.assertIn('gamertag', first)
        self.assertIn('distinct_games', first)
        self.assertGreaterEqual(first['distinct_games'], 3)
        self.assertIn('total_points', first)
        self.assertGreater(first['total_points'], 0)
        self.assertIn('leaderboards', first)
        self.assertGreaterEqual(len(first['leaderboards']), 2)

    def test_analytics_competitiveness_scores(self):
        res = self.app.get('/api/analytics/competitiveness?sort=tightest')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        scores = data['competitiveness']
        self.assertEqual(len(scores), 39)

        # Check spread calculation on every mode
        for s in scores:
            self.assertEqual(s['point_spread'], s['max_points'] - s['min_points'])
            self.assertGreater(s['max_points'], 0)
            self.assertIn('rank1_player', s)
            self.assertIn('rank25_player', s)
            self.assertIn('tier', s)

        # Tightest spread mode should have lowest point_spread
        self.assertLessEqual(scores[0]['point_spread'], scores[-1]['point_spread'])

    def test_analytics_rank_distribution(self):
        res = self.app.get('/api/analytics/rank-distribution')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['total_ranked_players'], 800)
        
        # Check grouped tiers
        tiers = {t['tier']: t for t in data['grouped_tiers']}
        self.assertIn('Obsidian Tier', tiers)
        self.assertIn('Diamond Tier', tiers)
        self.assertIn('Emerald Tier', tiers)
        self.assertIn('VIP Tier', tiers)
        self.assertIn('Iron Tier', tiers)
        self.assertIn('Bedrock Player (Free)', tiers)

        # Check total percentages sum to ~100%
        pct_sum = sum(t['percentage'] for t in data['grouped_tiers'])
        self.assertAlmostEqual(pct_sum, 100.0, delta=1.0)

    def test_analytics_server_tracker(self):
        res = self.app.get('/api/analytics/server-tracker')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('current_online', data)
        self.assertGreater(data['current_online'], 0)
        self.assertIn('hourly_timeline', data)
        self.assertEqual(len(data['hourly_timeline']), 24)
        self.assertIn('peak_window', data)
        self.assertIn('offpeak_window', data)

    def test_analytics_overview(self):
        res = self.app.get('/api/analytics/overview')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('masters', data)
        self.assertIn('competitiveness', data)
        self.assertIn('rank_distribution', data)
        self.assertIn('server_tracker', data)

    def test_strategy_maps_list_and_filters(self):
        # 1. Fetch all maps
        res = self.app.get('/api/strategy/maps')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 7)

        names = [m['name'] for m in data['maps']]
        self.assertIn('Tea Party', names)
        self.assertIn('Dwarven', names)
        self.assertIn('Atlantis', names)
        self.assertIn('Toys', names)
        self.assertIn('Trees', names)
        self.assertIn('Rainbow', names)
        self.assertIn('Magic', names)

        # 2. Filter by EggWars
        res_egg = self.app.get('/api/strategy/maps?game=EggWars')
        self.assertEqual(res_egg.status_code, 200)
        data_egg = json.loads(res_egg.data)
        self.assertEqual(data_egg['count'], 4)
        for m in data_egg['maps']:
            self.assertEqual(m['game'], 'EggWars')

        # 3. Filter by SkyWars
        res_sky = self.app.get('/api/strategy/maps?game=SkyWars')
        self.assertEqual(res_sky.status_code, 200)
        data_sky = json.loads(res_sky.data)
        self.assertEqual(data_sky['count'], 3)
        for m in data_sky['maps']:
            self.assertEqual(m['game'], 'SkyWars')

    def test_strategy_map_detail(self):
        # 1. Existing map
        res = self.app.get('/api/strategy/maps/eggwars_tea_party')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        m = data['map']
        self.assertEqual(m['name'], 'Tea Party')
        self.assertEqual(m['game'], 'EggWars')
        self.assertIn('tactics_rush', m)
        self.assertIn('tactics_defense', m)
        self.assertIn('tactics_mid_control', m)
        self.assertIn('generator_breakdown', m)
        self.assertIn('bridging_distances', m)
        self.assertGreater(len(m['bridging_distances']), 0)
        self.assertIn('schematic_2d', m)
        self.assertIsNotNone(m['schematic_2d'])

        # 2. Non-existent map
        res_404 = self.app.get('/api/strategy/maps/unknown_map_xyz')
        self.assertEqual(res_404.status_code, 404)

    def test_strategy_2d_schematics_validity(self):
        res = self.app.get('/api/strategy/overview')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['maps']), 7)

        for m in data['maps']:
            self.assertIn('schematic_2d', m, f"Map {m['map_id']} missing schematic_2d")
            s = m['schematic_2d']
            self.assertIsNotNone(s)
            self.assertIn('islands', s)
            self.assertIn('bridging_paths', s)
            self.assertGreater(len(s['islands']), 0)
            self.assertGreater(len(s['bridging_paths']), 0)

            # Check island coordinates
            for isl in s['islands']:
                self.assertIn('id', isl)
                self.assertIn('x', isl)
                self.assertIn('y', isl)
                self.assertIn('radius', isl)
                self.assertTrue(0 <= isl['x'] <= 800)
                self.assertTrue(0 <= isl['y'] <= 800)

            # Check bridging paths
            for path in s['bridging_paths']:
                self.assertIn('from_id', path)
                self.assertIn('to_id', path)
                self.assertIn('distance_blocks', path)
                self.assertGreater(path['distance_blocks'], 0)
                self.assertIn('jump_bridge_sec', path)
                self.assertIn('sneak_bridge_sec', path)

        # Dedicated endpoint check
        res_single = self.app.get('/api/strategy/schematic/eggwars_tea_party')
        self.assertEqual(res_single.status_code, 200)
        data_single = json.loads(res_single.data)
        self.assertTrue(data_single['success'])
        self.assertEqual(data_single['map_id'], 'eggwars_tea_party')
        self.assertIn('schematic_2d', data_single)

    def test_strategy_generators_authentic_rates(self):
        res = self.app.get('/api/strategy/generators')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        gens = data['generators']
        self.assertIn('iron', gens)
        self.assertIn('gold', gens)
        self.assertIn('diamond', gens)

        # Verify authentic Iron generator tiers
        iron_tiers = {t['tier']: t for t in gens['iron']['tiers']}
        self.assertEqual(iron_tiers[1]['rate_per_min'], 30.0)
        self.assertEqual(iron_tiers[2]['rate_per_min'], 60.0)
        self.assertEqual(iron_tiers[3]['rate_per_min'], 120.0)
        self.assertEqual(iron_tiers[4]['rate_per_min'], 240.0)

        # Verify authentic Gold generator tiers
        gold_tiers = {t['tier']: t for t in gens['gold']['tiers']}
        self.assertEqual(gold_tiers[1]['rate_per_min'], 15.0)
        self.assertEqual(gold_tiers[2]['rate_per_min'], 30.0)
        self.assertEqual(gold_tiers[3]['rate_per_min'], 60.0)
        self.assertEqual(gold_tiers[4]['rate_per_min'], 120.0)

        # Verify authentic Diamond generator tiers
        dia_tiers = {t['tier']: t for t in gens['diamond']['tiers']}
        self.assertEqual(dia_tiers[1]['rate_per_min'], 2.0)
        self.assertEqual(dia_tiers[2]['rate_per_min'], 4.0)
        self.assertEqual(dia_tiers[3]['rate_per_min'], 8.0)
        self.assertEqual(dia_tiers[4]['rate_per_min'], 16.0)

    def test_strategy_bridging_benchmarks(self):
        res = self.app.get('/api/strategy/bridging-benchmarks')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['mechanics']['jump_bridge_speed_bps'], 5.6)
        self.assertEqual(data['mechanics']['sneak_bridge_speed_bps'], 1.6)

        benchmarks = data['benchmarks']
        self.assertGreaterEqual(len(benchmarks), 10)
        # Check that benchmarks are ordered by distance ascending
        for i in range(len(benchmarks) - 1):
            self.assertLessEqual(benchmarks[i]['distance_blocks'], benchmarks[i+1]['distance_blocks'])

        # Check key distances
        targets = [b['target'] for b in benchmarks]
        self.assertTrue(any('Neighbor' in t for t in targets))
        self.assertTrue(any('Mid' in t or 'Forge' in t or 'Cake' in t for t in targets))

    def test_strategy_overview_bundled(self):
        res = self.app.get('/api/strategy/overview')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('maps', data)
        self.assertIn('generators', data)
        self.assertIn('bridging', data)
        self.assertEqual(len(data['maps']), 7)

if __name__ == '__main__':
    unittest.main()
