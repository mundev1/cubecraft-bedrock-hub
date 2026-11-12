"""
Unit tests for CubeCraft Bedrock Community Hub API endpoints.
Tests 39 Bedrock game mode leaderboards, 800+ players, store bundles,
playable Medal & community clips, and player encounters.
"""
import unittest
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from database import init_db, seed_bundles_and_clips

class TestCubeCraftBedrockAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        init_db()
        seed_bundles_and_clips()

    def test_global_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['stats']['total_players'], 800)
        self.assertGreaterEqual(data['stats']['total_leaderboard_entries'], 900)
        self.assertGreater(data['stats']['total_games'], 5)

    def test_games_list_contains_submodes(self):
        response = self.app.get('/api/games')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        games_dict = {g['name']: g for g in data['games']}
        self.assertIn('EggWars', games_dict)
        self.assertIn('SkyWars', games_dict)
        self.assertIn('BlockWars', games_dict)

        # Check SkyWars sub-modes
        skywars_modes = games_dict['SkyWars']['modes']
        self.assertIn('Solo', skywars_modes)
        self.assertIn('Duos (Teams of 2)', skywars_modes)
        self.assertIn('Squads (Teams of 4)', skywars_modes)

        # Check EggWars sub-modes
        eggwars_modes = games_dict['EggWars']['modes']
        self.assertIn('Solo', eggwars_modes)
        self.assertIn('Duos (Teams of 2)', eggwars_modes)
        self.assertIn('Squads (Teams of 4)', eggwars_modes)

    def test_leaderboards_filtering_by_game_and_mode(self):
        # EggWars Solo
        response = self.app.get('/api/leaderboards?game=EggWars&mode=Solo&sort_by=points')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['leaderboard']), 0)
        first = data['leaderboard'][0]
        self.assertEqual(first['game'], 'EggWars')
        self.assertEqual(first['mode'], 'Solo')

        # SkyWars Duos
        res_sky = self.app.get('/api/leaderboards?game=SkyWars&mode=Duos%20(Teams%20of%202)&sort_by=points')
        self.assertEqual(res_sky.status_code, 200)
        data_sky = json.loads(res_sky.data)
        self.assertTrue(data_sky['success'])
        self.assertGreater(len(data_sky['leaderboard']), 0)

    def test_custom_players_mundev_and_joeal(self):
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
        self.assertGreater(len(pdata_m['leaderboards']), 0)
        self.assertGreater(len(pdata_m['encounters']), 0)

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
        self.assertGreater(len(pdata_j['leaderboards']), 0)
        self.assertGreater(len(pdata_j['encounters']), 0)

    def test_bundles_catalog_and_images(self):
        response = self.app.get('/api/bundles')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['bundles']), 0)
        for b in data['bundles']:
            self.assertIn('banner_img', b)
            self.assertTrue(b['banner_img'].startswith('http'))
            self.assertIn('items', b)

    def test_clips_and_community_submission(self):
        # Fetch clips
        response = self.app.get('/api/clips?game=all&type=all')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['clips']), 0)

        # Submit new community clip
        new_clip = {
            "title": "Insane 1v4 Tea Party Clutch",
            "gamertag": "Chiibet",
            "game": "EggWars",
            "clip_url": "https://medal.tv/games/minecraft/clips/test-1v4",
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
        self.assertGreaterEqual(up_data['upvotes'], 2)

    def test_player_search_across_800_players(self):
        res_search = self.app.get('/api/players/search?q=Chii')
        self.assertEqual(res_search.status_code, 200)
        search_data = json.loads(res_search.data)
        self.assertTrue(search_data['success'])
        self.assertTrue(any(p['gamertag'] == 'Chiibet' for p in search_data['players']))

        # Profile fetch for real player
        res_prof = self.app.get('/api/players/Chiibet')
        self.assertEqual(res_prof.status_code, 200)
        prof_data = json.loads(res_prof.data)
        self.assertTrue(prof_data['success'])
        self.assertEqual(prof_data['player']['gamertag'], 'Chiibet')
        self.assertIn('leaderboards', prof_data)

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

    def test_daily_wins_counters_and_stats(self):
        # Stats endpoint with daily tracked wins
        res = self.app.get('/api/stats')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('today_tracked_wins', data['stats'])
        self.assertGreater(data['stats']['today_tracked_wins'], 0)
        self.assertIn('online_players', data['stats'])
        self.assertGreater(data['stats']['online_players'], 1000)
        self.assertIn('top_daily_grinder', data['stats'])
        self.assertIsNotNone(data['stats']['top_daily_grinder'])

    def test_leaderboards_timeframe_daily(self):
        # Leaderboards with timeframe=daily
        res = self.app.get('/api/leaderboards?game=EggWars&mode=All%20Modes&timeframe=daily')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['timeframe'], 'daily')
        self.assertGreater(len(data['leaderboard']), 0)
        
        # Verify sorted by daily_wins descending
        rows = data['leaderboard']
        for i in range(len(rows) - 1):
            self.assertGreaterEqual(rows[i]['daily_wins'], rows[i + 1]['daily_wins'])

    def test_daily_leaders_endpoint(self):
        res = self.app.get('/api/leaderboards/daily-leaders')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['daily_leaders']), 0)
        top = data['daily_leaders'][0]
        self.assertIn('gamertag', top)
        self.assertIn('daily_wins', top)
        self.assertGreater(top['daily_wins'], 0)

    def test_player_profile_daily_stats(self):
        # MundevPolite
        res_m = self.app.get('/api/players/MundevPolite')
        self.assertEqual(res_m.status_code, 200)
        data_m = json.loads(res_m.data)
        self.assertIn('daily_stats', data_m)
        self.assertEqual(data_m['daily_stats']['daily_wins'], 24)
        self.assertEqual(data_m['daily_stats']['daily_streak'], 6)

        # JoealBadmash
        res_j = self.app.get('/api/players/JoealBadmash')
        self.assertEqual(res_j.status_code, 200)
        data_j = json.loads(res_j.data)
        self.assertIn('daily_stats', data_j)
        self.assertEqual(data_j['daily_stats']['daily_wins'], 31)
        self.assertEqual(data_j['daily_stats']['daily_streak'], 9)

if __name__ == '__main__':
    unittest.main()
