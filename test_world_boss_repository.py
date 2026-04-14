import shutil
import unittest
import uuid
from pathlib import Path

from astrbot_plugin_name_fight.database import FighterRepository


class WorldBossRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(r'D:\NFIGHTPLUS\.tmp_world_boss_tests')
        root.mkdir(parents=True, exist_ok=True)
        self.temp_dir = root / uuid.uuid4().hex
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.temp_dir / 'fighters.db'
        self.repo = FighterRepository(self.db_path)
        self.phase1 = {
            'name': 'phase1',
            'stats': {'hp': 1800, 'atk': 150, 'def': 90, 'spd': 100.0, 'crt': 10.0, 'eva': 8.0},
            'martial_art_id': 'sword_huashan',
            'neigong_id': 'shenzhao_jing',
            'qinggong_id': 'lightning_flash',
            'martial_art': self.repo.martial_arts_map['sword_huashan'],
            'neigong': self.repo.neigong_map['shenzhao_jing'],
            'qinggong': self.repo.qinggong_map['lightning_flash'],
        }
        self.phase2 = {
            'name': 'phase2',
            'stats': {'hp': 19000, 'atk': 170, 'def': 170, 'spd': 115.0, 'crt': 12.0, 'eva': 10.0},
            'martial_art_id': 'sword_huashan',
            'neigong_id': 'shenzhao_jing',
            'qinggong_id': 'lightning_flash',
            'martial_art': self.repo.martial_arts_map['sword_huashan'],
            'neigong': self.repo.neigong_map['shenzhao_jing'],
            'qinggong': self.repo.qinggong_map['lightning_flash'],
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_world_boss_lifecycle(self) -> None:
        activity = self.repo.open_group_boss('g1', 'Boss', self.phase1, self.phase2, 'admin')
        self.assertEqual(activity['phase2_current_hp'], 19000)
        self.assertIsNotNone(self.repo.get_active_group_boss('g1'))

        attempt_info = self.repo.consume_group_boss_attempt(activity['boss_id'], 'g1', 'u1', '2026-04-14', 3)
        self.assertEqual(attempt_info['used_attempts'], 1)
        self.assertEqual(self.repo.get_group_boss_attempt_usage(activity['boss_id'], 'g1', 'u1', '2026-04-14'), 1)

        damage_result = self.repo.apply_group_boss_phase2_damage(activity['boss_id'], 'g1', 1200)
        self.assertEqual(damage_result['before_hp'], 19000)
        self.assertEqual(damage_result['after_hp'], 17800)
        self.assertFalse(damage_result['is_killed'])

        contribution = self.repo.record_group_boss_damage(activity['boss_id'], 'g1', 'u1', 'User1', 1200)
        self.assertEqual(contribution['total_damage'], 1200)
        rank = self.repo.get_group_boss_rank('g1', activity['boss_id'])
        self.assertEqual(rank[0]['user_id'], 'u1')
        self.assertEqual(rank[0]['total_damage'], 1200)

    def test_world_boss_settlement_rewards(self) -> None:
        activity = self.repo.open_group_boss('g1', 'Boss', self.phase1, self.phase2, 'admin')
        self.repo.record_group_boss_damage(activity['boss_id'], 'g1', 'u1', 'User1', 5000)
        self.repo.record_group_boss_damage(activity['boss_id'], 'g1', 'u2', 'User2', 3000)
        kill = self.repo.apply_group_boss_phase2_damage(activity['boss_id'], 'g1', 19000)
        self.assertTrue(kill['is_killed'])

        settlement = self.repo.settle_group_boss('g1', activity['boss_id'])
        self.assertEqual(settlement['rewards'][0]['user_id'], 'u1')
        self.assertEqual(settlement['rewards'][0]['points'], 300)
        self.assertEqual(self.repo.get_user_points('u1'), 300)
        self.assertEqual(self.repo.get_user_points('u2'), 200)
        latest = self.repo.get_group_boss_by_id('g1', activity['boss_id'])
        self.assertEqual(latest['status'], 'settled')

    def test_world_boss_close_without_kill(self) -> None:
        activity = self.repo.open_group_boss('g1', 'Boss', self.phase1, self.phase2, 'admin')
        updated = self.repo.close_group_boss('g1', activity['boss_id'])
        self.assertEqual(updated['status'], 'closed')
        self.assertIsNone(self.repo.get_active_group_boss('g1'))


if __name__ == '__main__':
    unittest.main()
