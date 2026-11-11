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

    def test_bundles_catalog(self):
        response = self.app.get('/api/bundles')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['bundles']), 0)
        first_bundle = data['bundles'][0]
        self.assertIn('items', first_bundle)
        self.assertGreater(len(first_bundle['items']), 0)

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

if __name__ == '__main__':
    unittest.main()
