"""
Unit tests for CubeCraft Bedrock Community Hub API endpoints.
Tests leaderboards, store bundles, playable Medal clips, and player encounters.
"""
import unittest
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from database import init_db, seed_db

class TestCubeCraftBedrockAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        init_db()
        seed_db()

    def test_global_stats(self):
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(data['stats']['total_players'], 0)
        self.assertGreater(data['stats']['total_encounters'], 0)
        self.assertGreater(data['stats']['total_clips'], 0)
        self.assertGreater(data['stats']['active_bundles'], 0)

    def test_games_list(self):
        response = self.app.get('/api/games')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        game_names = [g['name'] for g in data['games']]
        self.assertIn('EggWars', game_names)
        self.assertIn('SkyWars', game_names)
        self.assertIn('BlockWars', game_names)

    def test_leaderboards_filtering_and_sorting(self):
        # EggWars by Wins
        response = self.app.get('/api/leaderboards?game=EggWars&sort_by=wins')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['leaderboard']), 0)
        self.assertEqual(data['podium'][0]['player_gamertag'], 'Vxrtical')

        # SkyWars by Kills
        response2 = self.app.get('/api/leaderboards?game=SkyWars&sort_by=kills')
        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.data)
        self.assertTrue(data2['success'])
        self.assertGreater(len(data2['leaderboard']), 0)

    def test_bundles_catalog(self):
        response = self.app.get('/api/bundles')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['bundles']), 0)
        first_bundle = data['bundles'][0]
        self.assertIn('items', first_bundle)
        self.assertGreater(len(first_bundle['items']), 0)
        self.assertIn('price_minecoins', first_bundle)

    def test_clips_and_submission(self):
        # Fetch clips
        response = self.app.get('/api/clips?game=all&sort=recent')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['clips']), 0)

        # Submit new clip
        new_clip = {
            "title": "Sub-20s Bridges Goal Clutch",
            "gamertag": "TestBedrocker",
            "game": "BlockWars",
            "medal_url": "https://medal.tv/clip/sample-test-clip",
            "duration": "0:25"
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

    def test_player_search_and_profile(self):
        # Search player
        res_search = self.app.get('/api/players/search?q=Vxrt')
        self.assertEqual(res_search.status_code, 200)
        search_data = json.loads(res_search.data)
        self.assertTrue(search_data['success'])
        self.assertTrue(any(p['gamertag'] == 'Vxrtical' for p in search_data['players']))

        # Profile fetch
        res_prof = self.app.get('/api/players/Vxrtical')
        self.assertEqual(res_prof.status_code, 200)
        prof_data = json.loads(res_prof.data)
        self.assertTrue(prof_data['success'])
        self.assertEqual(prof_data['player']['gamertag'], 'Vxrtical')
        self.assertIn('stats', prof_data)
        self.assertGreater(len(prof_data['encounters']), 0)

    def test_player_encounter_post_and_helpful(self):
        # Post encounter on a player
        encounter_payload = {
            "reviewer_name": "TestGamer",
            "game_played": "EggWars Duos",
            "encounter_type": "God-tier Clutch",
            "rating": 5,
            "comment": "Saved our egg twice against diamond-armored rushers. Masterclass in bridging and defense!"
        }
        res_post = self.app.post('/api/players/Vxrtical/encounters', data=json.dumps(encounter_payload), content_type='application/json')
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
        self.assertGreaterEqual(helpful_data['helpful_votes'], 1)

if __name__ == '__main__':
    unittest.main()
