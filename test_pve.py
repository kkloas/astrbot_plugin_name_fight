from __future__ import annotations

import itertools
import random
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from database import FighterRepository
from engine import CombatEngine
from pve import PveService
from pve_late import LatePveBattle
from pve_switch import PendingSwitch, SwitchDecisions


class ClosingRepository(FighterRepository):
    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()


class ScriptedEngine:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def battle_with_events(self, fighter_a, fighter_b):
        self.calls.append((deepcopy(fighter_a), deepcopy(fighter_b)))
        outcome = self.outcomes.pop(0)
        a_hp = int(fighter_a.get("current_hp", fighter_a["stats"]["hp"]))
        b_hp = int(fighter_b.get("current_hp", fighter_b["stats"]["hp"]))
        fighter_a["temporary_status"] = "bleeding"
        fighter_b["temporary_status"] = "stunned"
        if outcome == "a":
            a_after, b_after, winner = max(1, a_hp - 10), 0, fighter_a["name"]
        elif outcome == "b":
            a_after, b_after, winner = 0, max(1, b_hp - 10), fighter_b["name"]
        else:
            a_after, b_after, winner = 0, 0, None
        return {
            "winner": winner,
            "state": {"fighter_a_hp": a_after, "fighter_b_hp": b_after},
            "events": [{"type": "battle_end", "time": 1}],
            "logs": [],
        }


class PveRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="name-fight-pve-")
        self.repo = ClosingRepository(Path(self.temp.name) / "fighters.db")
        self.user_id = "pve-user"

    def tearDown(self):
        self.temp.cleanup()

    def create_team(self):
        for name in ("历练甲", "历练乙", "历练丙"):
            self.repo.create_fighter_for_user(self.user_id, name)
        return self.repo.set_pve_team(self.user_id, [1, 2, 3], now=1000)

    def test_energy_recovery_and_team_validation(self):
        profile = self.repo.get_pve_profile(self.user_id, now=1000)
        self.assertEqual(profile["energy"], 100)
        with self.assertRaisesRegex(ValueError, "三个不重复"):
            self.repo.set_pve_team(self.user_id, [1, 1, 2], now=1000)
        self.create_team()
        with self.assertRaisesRegex(ValueError, "空位"):
            self.repo.set_pve_team(self.user_id, [1, 2, 4], now=1000)
        loss = self.repo.settle_pve_attempt(
            self.user_id, "1-1", 10, False, 0,
            {"points": 20, "items": []}, {"points": 5, "items": []}, now=1000,
        )
        self.assertEqual(loss["profile"]["energy"], 90)
        recovered = self.repo.get_pve_profile(self.user_id, now=1360)
        self.assertEqual(recovered["energy"], 91)
        capped = self.repo.get_pve_profile(self.user_id, now=100000)
        self.assertEqual(capped["energy"], 100)

    def test_energy_item_is_atomic_caps_at_maximum_and_preserves_recovery_progress(self):
        self.repo.get_pve_profile(self.user_id, now=1000)
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE pve_profiles SET energy = 50, energy_updated_at = 1000 WHERE user_id = ?",
                (self.user_id,),
            )
            connection.execute(
                "INSERT INTO user_items (user_id, item_id, quantity) VALUES (?, 'energy_pill', 2)",
                (self.user_id,),
            )
            connection.commit()

        first = self.repo.use_pve_energy_item(self.user_id, "energy_pill", now=1100)
        self.assertEqual(first["restored"], 30)
        self.assertEqual(first["profile"]["energy"], 80)
        self.assertEqual(first["remaining"], 1)
        self.assertEqual(self.repo.get_pve_profile(self.user_id, now=1360)["energy"], 81)

        second = self.repo.use_pve_energy_item(self.user_id, "energy_pill", now=1360)
        self.assertEqual(second["restored"], 19)
        self.assertEqual(second["profile"]["energy"], 100)
        self.assertEqual(second["remaining"], 0)
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE user_items SET quantity = 1 WHERE user_id = ? AND item_id = 'energy_pill'",
                (self.user_id,),
            )
            connection.commit()
        with self.assertRaisesRegex(ValueError, "体力已满"):
            self.repo.use_pve_energy_item(self.user_id, "energy_pill", now=1361)
        bag = {item["item_id"]: item for item in self.repo.get_user_items(self.user_id)}
        self.assertEqual(bag["energy_pill"]["quantity"], 1)

    def test_first_clear_best_stars_and_chapter_reward_are_unique(self):
        self.create_team()
        first = self.repo.settle_pve_attempt(
            self.user_id, "1-1", 10, True, 1,
            {"points": 20, "items": [{"item_id": "star_exp_pill_s", "quantity": 1}]},
            {"points": 5, "items": []}, now=1000,
        )
        self.assertTrue(first["first_clear"])
        self.assertEqual(first["reward"]["points"], 20)
        second = self.repo.settle_pve_attempt(
            self.user_id, "1-1", 10, True, 3,
            {"points": 20, "items": []}, {"points": 5, "items": []}, now=1001,
        )
        self.assertFalse(second["first_clear"])
        self.assertEqual(second["best_stars"], 3)
        self.assertEqual(second["clear_count"], 2)
        self.assertEqual(second["reward"]["points"], 5)
        claimed = self.repo.claim_pve_chapter_reward(
            self.user_id, "chapter_1", ["1-1"], 3,
            {"points": 50, "items": [{"item_id": "martial_token_basic", "quantity": 1}]}, now=1002,
        )
        self.assertEqual(claimed["reward"]["points"], 50)
        with self.assertRaisesRegex(ValueError, "已经领取"):
            self.repo.claim_pve_chapter_reward(
                self.user_id, "chapter_1", ["1-1"], 3,
                {"points": 50, "items": []}, now=1003,
            )

    def test_invalid_reward_rolls_back_energy_and_progress(self):
        self.create_team()
        with self.assertRaisesRegex(ValueError, "未知的 PVE 奖励道具"):
            self.repo.settle_pve_attempt(
                self.user_id, "1-1", 10, True, 3,
                {"points": 20, "items": [{"item_id": "missing_item", "quantity": 1}]},
                {"points": 5, "items": []}, now=1000,
            )
        self.assertEqual(self.repo.get_pve_profile(self.user_id, now=1000)["energy"], 100)
        self.assertEqual(self.repo.get_pve_stage_progress(self.user_id), [])


class PveServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="name-fight-pve-service-")
        self.repo = ClosingRepository(Path(self.temp.name) / "fighters.db")
        self.service = PveService(self.repo, CombatEngine())
        self.user_id = "web-local-user"
        for name in ("青锋客", "抱月人", "听雪生"):
            self.repo.create_fighter_for_user(self.user_id, name)
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE fighters SET hp = 900, atk = 180, def = 150, spd = 120, crt = 50, eva = 45"
            )
            connection.commit()
        self.service.set_team(self.user_id, [1, 2, 3])

    def tearDown(self):
        self.temp.cleanup()

    def test_config_unlocks_and_npcs_are_not_persisted(self):
        state = self.service.get_state(self.user_id)
        stages = [stage for chapter in state["chapters"] for stage in chapter["stages"]]
        self.assertEqual(len(stages), 30)
        self.assertTrue(stages[0]["unlocked"])
        self.assertFalse(stages[1]["unlocked"])
        with self.assertRaisesRegex(ValueError, "尚未解锁"):
            self.service.challenge(self.user_id, "1-2")
        self.assertEqual(self.service.get_state(self.user_id)["profile"]["energy"], 100)
        before_names = {fighter["name"] for fighter in self.repo.get_user_fighters(self.user_id)}
        with patch("random.random", return_value=0.99):
            result = self.service.challenge(self.user_id, "1-1")
        self.assertTrue(result["victory"])
        self.assertTrue(result["firstClear"])
        self.assertEqual(result["profile"]["energy"], 90)
        self.assertGreaterEqual(len(result["duels"]), 3)
        after = self.service.get_state(self.user_id)
        self.assertTrue(after["chapters"][0]["stages"][1]["unlocked"])
        with self.repo._connect() as connection:
            persisted_names = {str(row["name"]) for row in connection.execute("SELECT name FROM fighters").fetchall()}
            score_count = int(connection.execute("SELECT COUNT(*) FROM fighter_scores").fetchone()[0])
        self.assertEqual(persisted_names, before_names)
        self.assertEqual(score_count, 0)
        with self.repo._connect() as connection:
            connection.execute("UPDATE pve_profiles SET energy = 0 WHERE user_id = ?", (self.user_id,))
            connection.commit()
        with self.assertRaisesRegex(ValueError, "体力不足"):
            self.service.challenge(self.user_id, "1-2")

    def test_relay_carries_hp_resets_temporary_state_and_keeps_max_hp(self):
        scripted = ScriptedEngine(("a", "a", "a"))
        self.service.engine = scripted
        stage = self.service.stage_map["1-1"]
        team = self.repo.get_user_fighters(self.user_id)
        enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
        result = self.service._team_battle(team, enemies, stage)
        maximum_hp = int(team[0]["stats"]["hp"])
        self.assertTrue(result["victory"])
        self.assertEqual(len(result["duels"]), 3)
        self.assertEqual([call[0]["current_hp"] for call in scripted.calls], [maximum_hp, maximum_hp - 10, maximum_hp - 20])
        self.assertTrue(all(call[0]["stats"]["hp"] == maximum_hp for call in scripted.calls))
        self.assertTrue(all("temporary_status" not in fighter for call in scripted.calls for fighter in call))

    def test_relay_draws_eliminate_both_sides_and_five_duels_is_the_maximum(self):
        stage = self.service.stage_map["1-1"]
        team = self.repo.get_user_fighters(self.user_id)
        enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
        draw_engine = ScriptedEngine(("draw", "draw", "draw"))
        self.service.engine = draw_engine
        draw = self.service._team_battle(team, enemies, stage)
        self.assertFalse(draw["victory"])
        self.assertEqual(draw["stars"], 0)
        self.assertEqual(len(draw["duels"]), 3)
        relay_engine = ScriptedEngine(("a", "b", "a", "b", "a"))
        self.service.engine = relay_engine
        relay = self.service._team_battle(team, enemies, stage)
        self.assertTrue(relay["victory"])
        self.assertEqual(relay["stars"], 1)
        self.assertEqual(len(relay["duels"]), 5)

    def test_main_2229cda_accepted_fixed_seed_win_rates(self):
        allowed_ratings = (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0)
        templates = [self.repo.generate_preview_fighter(name) for name in ("平衡甲", "平衡乙", "平衡丙")]
        # Snapshot after the low-HP extra action was limited to one added turn.
        # This is deterministic regression data, not population-wide balance.
        expected_wins = {
            "1-1": 36, "1-2": 35, "1-3": 75, "1-4": 61, "1-5": 58, "1-6": 25,
            "2-1": 57, "2-2": 49, "2-3": 61, "2-4": 87, "2-5": 42, "2-6": 64,
        }

        for stage_index, stage_id in enumerate(self.service.stage_order[:12]):
            stage = self.service.stage_map[stage_id]
            recommended = float(stage["recommended_stars"])
            ratings = min(
                itertools.combinations_with_replacement(allowed_ratings, 3),
                key=lambda values: (abs(sum(values) / 3 - recommended), max(values) - min(values)),
            )
            team = []
            for template, rating in zip(templates, ratings):
                fighter = dict(template)
                fighter["stats"] = self.repo._recalculate_final_stats(
                    dict(template["raw_stats"]),
                    rating,
                    1 if rating >= 6.0 else 0,
                    template["martial_art"],
                    template["neigong"],
                    template["qinggong"],
                )
                fighter["star_rating"] = rating
                team.append(fighter)
            enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
            wins = 0
            trials = 100
            for trial in range(trials):
                random.seed(20260921 + stage_index * 1000 + trial)
                wins += int(self.service._team_battle(team, enemies, stage)["victory"])
            self.assertEqual(wins, expected_wins[stage_id], stage_id)

    def test_chapter_three_encounters_and_star_objectives(self):
        expected_counts = {"3-1": 7, "3-2": 5, "3-3": 5, "3-4": 6, "3-5": 3, "3-6": 1}
        for stage_id, count in expected_counts.items():
            stage = self.service.stage_map[stage_id]
            self.assertEqual(len(stage["enemies"]), count)
            self.assertEqual(len(stage["tactics"]), 2)
            self.assertEqual(len(stage["star_objectives"]), 3)
        with self.assertRaisesRegex(ValueError, "有效战术"):
            self.service.challenge(self.user_id, "3-1", "invalid")
        stage = self.service.stage_map["3-1"]
        team = self.repo.get_user_fighters(self.user_id)
        enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
        self.service.engine = ScriptedEngine(("a",) * 7)
        result = self.service._chapter_three_battle(team, enemies, stage, stage["tactics"][0])
        self.assertTrue(result["victory"])
        self.assertEqual(result["stars"], 3)
        self.assertEqual([duel["attacker"]["name"] for duel in result["duels"]],
                         [team[0]["name"]] * 2 + [team[1]["name"]] * 2 + [team[2]["name"]] * 3)
        self.assertEqual(result["playerTeam"][0]["currentHp"], team[0]["stats"]["hp"] - 20)

    def test_manual_switch_can_keep_current_or_choose_a_living_teammate(self):
        stage = self.service.stage_map["3-1"]
        team = self.repo.get_user_fighters(self.user_id)
        enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
        with self.assertRaises(PendingSwitch) as pending:
            self.service._chapter_three_battle(team, enemies, stage, stage["tactics"][0],
                                               decider=SwitchDecisions([]), engine=ScriptedEngine(("a",) * 7))
        self.assertEqual(len(pending.exception.duels), 2)
        self.assertEqual(pending.exception.current, 0)
        continued = self.service._chapter_three_battle(team, enemies, stage, stage["tactics"][0],
                                                       decider=SwitchDecisions([0, 2]),
                                                       engine=ScriptedEngine(("a",) * 7))
        self.assertEqual([duel["attacker"]["name"] for duel in continued["duels"]],
                         [team[0]["name"]] * 4 + [team[2]["name"]] * 3)
        self.assertEqual(continued["stars"], 2)
        switched = self.service._chapter_three_battle(team, enemies, stage, stage["tactics"][0],
                                                      decider=SwitchDecisions([1, 2]),
                                                      engine=ScriptedEngine(("a",) * 7))
        self.assertEqual(switched["stars"], 3)

    def test_interactive_attempt_resumes_and_settles_only_once(self):
        with self.repo._connect() as connection:
            connection.execute(
                "INSERT INTO pve_stage_progress (user_id, stage_id, best_stars, clear_count, first_cleared_at, last_cleared_at) "
                "VALUES (?, '2-6', 1, 1, 1, 1)", (self.user_id,),
            )
            connection.commit()
        start = self.service.start_interactive(self.user_id, "3-1", "3-1-rush")
        self.assertEqual(start["status"], "pending")
        self.assertEqual(len(start["duels"]), 2)
        energy = start["profile"]["energy"]
        self.assertEqual(self.service.get_interactive(self.user_id)["attemptId"], start["attemptId"])
        with self.assertRaisesRegex(ValueError, "存活"):
            self.service.continue_interactive(self.user_id, start["attemptId"], 0, 9)
        with self.assertRaisesRegex(ValueError, "完成或放弃"):
            self.service.start_interactive(self.user_id, "3-1", "3-1-rush")
        current = start
        while current["status"] == "pending":
            prompt = current["switchPrompt"]
            current = self.service.continue_interactive(
                self.user_id, current["attemptId"], prompt["decisionCount"],
                prompt["availableIndexes"][-1],
            )
        self.assertEqual(current["status"], "complete")
        self.assertEqual(current["profile"]["energy"], energy)
        self.assertEqual(current["clearCount"], 1)
        self.assertIsNone(self.service.get_interactive(self.user_id))
        with self.assertRaisesRegex(ValueError, "不存在"):
            self.service.continue_interactive(self.user_id, start["attemptId"], 0, 0)
        abandoned = self.service.start_interactive(self.user_id, "3-1", "3-1-rush")
        self.service.abandon_interactive(self.user_id, abandoned["attemptId"])
        self.assertEqual(self.service.get_state(self.user_id)["profile"]["energy"], energy - 10)
        self.assertEqual(self.service.get_state(self.user_id)["chapters"][2]["stages"][0]["clearCount"], 1)

    def test_manual_boss_phase_keeps_one_health_pool_when_fighter_stays(self):
        stage = self.service.stage_map["5-6"]
        team = self.repo.get_user_fighters(self.user_id)
        enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
        def simulate(choices):
            return LatePveBattle(self.service, team, enemies, stage, stage["tactics"][0], set(),
                                 decider=SwitchDecisions(choices), engine=CombatEngine(rng=random.Random(1506))).run()
        with self.assertRaises(PendingSwitch) as first:
            simulate([])
        with self.assertRaises(PendingSwitch) as second:
            simulate([0])
        maximum = int(enemies[0]["stats"]["hp"])
        self.assertEqual(len(first.exception.enemies), 1)
        self.assertEqual(first.exception.enemies[0]["hp"], round(maximum * 0.75))
        self.assertEqual(second.exception.duels[-1]["defender"]["currentHp"], first.exception.enemies[0]["hp"])
        self.assertEqual(second.exception.current, 0)

    def test_chapter_three_recommended_team_can_clear_and_earn_three_stars(self):
        templates = [self.repo.generate_preview_fighter(name) for name in ("平衡甲", "平衡乙", "平衡丙")]
        allowed_ratings = (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0)
        for offset, stage_id in enumerate(self.service.stage_order[12:18]):
            stage = self.service.stage_map[stage_id]
            recommended = float(stage["recommended_stars"])
            ratings = min(itertools.combinations_with_replacement(allowed_ratings, 3),
                          key=lambda values: (abs(sum(values) / 3 - recommended), max(values) - min(values)))
            team = []
            for template, rating in zip(templates, ratings):
                fighter = dict(template)
                fighter["stats"] = self.repo._recalculate_final_stats(
                    dict(template["raw_stats"]), rating, 1 if rating >= 6.0 else 0,
                    template["martial_art"], template["neigong"], template["qinggong"])
                team.append(fighter)
            enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
            for tactic in stage["tactics"]:
                wins = three_stars = 0
                for trial in range(30):
                    random.seed(20260921 + offset * 1000 + trial)
                    result = self.service._chapter_three_battle(team, enemies, stage, tactic)
                    wins += int(result["victory"])
                    three_stars += int(result["stars"] == 3)
                self.assertGreaterEqual(wins, 4, (stage_id, tactic["id"]))
                self.assertGreaterEqual(three_stars, 1, (stage_id, tactic["id"]))

    def test_boss_keeps_one_health_pool_across_three_fighters(self):
        class PhaseEngine:
            def __init__(self, second_actions=1):
                self.calls = []
                self.second_actions = second_actions

            def battle_with_events(self, fighter_a, fighter_b):
                self.calls.append((deepcopy(fighter_a), deepcopy(fighter_b)))
                floor = int(fighter_b.get("phase_hp_floor", 0))
                boundary = floor > 0
                return {
                    "winner": None if boundary else fighter_a["name"],
                    "state": {"fighter_a_hp": fighter_a["current_hp"] - 10,
                              "fighter_b_hp": floor,
                              "actions": self.second_actions if len(self.calls) == 2 else 1,
                              "phase_boundary": boundary},
                    "events": [{"type": "battle_end", "time": 1}],
                    "logs": ["阶段切换"],
                }

        engine = PhaseEngine()
        self.service.engine = engine
        stage = self.service.stage_map["3-6"]
        team = self.repo.get_user_fighters(self.user_id)
        boss = self.service._stage_enemy(stage, stage["enemies"][0])
        result = self.service._chapter_three_battle(team, [boss], stage, stage["tactics"][0])
        maximum = boss["stats"]["hp"]
        self.assertTrue(result["victory"])
        self.assertEqual(result["stars"], 3)
        self.assertEqual([call[1]["current_hp"] for call in engine.calls],
                         [maximum, round(maximum * 0.70), round(maximum * 0.35)])
        self.assertEqual([duel["attacker"]["name"] for duel in result["duels"]],
                         [fighter["name"] for fighter in team])
        self.assertEqual(len({call[1]["name"] for call in engine.calls}), 1)
        self.service.engine = PhaseEngine(second_actions=17)
        unbroken = self.service._chapter_three_battle(team, [boss], stage, stage["tactics"][0])
        self.assertEqual(unbroken["stars"], 2)
        self.assertIn("终式蓄力爆发", unbroken["duels"][-1]["opening"])

    def test_chapter_three_special_events_and_distinct_kills(self):
        team = self.repo.get_user_fighters(self.user_id)

        def battle(stage_id, outcomes, engine_class=ScriptedEngine):
            stage = self.service.stage_map[stage_id]
            enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
            self.service.engine = engine_class(outcomes)
            return self.service._chapter_three_battle(team, enemies, stage, stage["tactics"][0])

        rain = battle("3-2", ("a", "a", "b", "a", "a", "a"))
        self.assertTrue(rain["victory"])
        self.assertEqual(sum("暗器齐射" in duel["opening"] for duel in rain["duels"]), 2)

        class SlowEngine(ScriptedEngine):
            def battle_with_events(self, fighter_a, fighter_b):
                result = super().battle_with_events(fighter_a, fighter_b)
                result["state"]["actions"] = 12
                return result

        mirror = battle("3-3", ("a",) * 5, SlowEngine)
        self.assertTrue(mirror["victory"])
        self.assertEqual(mirror["stars"], 2)
        self.assertEqual(sum("镜阵强化" in duel["transition"] for duel in mirror["duels"]), 4)

        armory = battle("3-4", ("a",) * 6)
        self.assertEqual(armory["stars"], 3)
        self.assertEqual(["刀阵", "枪阵", "剑阵"],
                         [armory["duels"][index]["opening"].split("生效")[0].strip().split()[-1]
                          for index in (0, 2, 4)])

        envoys = battle("3-5", ("a", "b", "a", "a"))
        self.assertEqual(envoys["stars"], 2)
        self.assertTrue(envoys["objectiveResults"][1]["met"])
        self.assertFalse(envoys["objectiveResults"][2]["met"])

    def test_engine_stops_at_boss_phase_floor_without_false_victory(self):
        attacker = self.repo.get_user_fighters(self.user_id)[0]
        attacker["stats"] = {**attacker["stats"], "atk": 5000, "spd": 1000}
        stage = self.service.stage_map["3-6"]
        boss = self.service._stage_enemy(stage, stage["enemies"][0])
        boss["stats"]["hp"] = 200
        boss["current_hp"] = 200
        boss["phase_hp_floor"] = 140
        random.seed(111)
        result = CombatEngine().battle_with_events(attacker, boss)
        self.assertEqual(result["state"]["fighter_b_hp"], 140)
        self.assertTrue(result["state"]["phase_boundary"])
        self.assertIsNone(result["winner"])
        self.assertFalse(any(event["type"] == "victory_start" for event in result["events"]))

    def test_chapters_four_and_five_encounters_and_clue_progress(self):
        counts = {
            "4-1": 6, "4-2": 7, "4-3": 5, "4-4": 6, "4-5": 5, "4-6": 5,
            "5-1": 8, "5-2": 6, "5-3": 6, "5-4": 5, "5-5": 2, "5-6": 1,
        }
        state = self.service.get_state(self.user_id)
        self.assertEqual(len(state["chapters"]), 5)
        self.assertEqual(state["intel"], [])
        self.assertEqual(state["nextStageId"], "1-1")
        for stage_id, count in counts.items():
            stage = self.service.stage_map[stage_id]
            self.assertEqual(len(stage["enemies"]), count)
            self.assertEqual(len(stage["tactics"]), 2)
            self.assertEqual(len(stage["star_objectives"]), 3)
        with self.assertRaisesRegex(ValueError, "有效战术"):
            self.service.challenge(self.user_id, "4-1", "invalid")
        self.assertEqual(self.service.get_state(self.user_id)["profile"]["energy"], 100)
        with self.repo._connect() as connection:
            connection.execute(
                "INSERT INTO pve_stage_progress (user_id, stage_id, best_stars, clear_count, first_cleared_at, last_cleared_at) "
                "VALUES (?, '3-6', 1, 1, 1, 1)", (self.user_id,),
            )
            connection.commit()
        self.assertTrue(self.service.get_state(self.user_id)["chapters"][3]["stages"][0]["unlocked"])
        class SlowEngine(ScriptedEngine):
            def battle_with_events(self, fighter_a, fighter_b):
                result = super().battle_with_events(fighter_a, fighter_b)
                result["state"]["actions"] = 20
                return result
        self.service.engine = SlowEngine(("a",) * 6)
        clear = self.service.challenge(self.user_id, "4-1", "4-1-guard")
        self.assertTrue(clear["firstClear"])
        self.assertEqual(clear["stars"], 2)
        self.assertEqual([entry["met"] for entry in clear["objectiveResults"]], [True, True, False])
        self.assertEqual(clear["pve"]["intel"][0]["id"], "silver_rubbing")
        self.assertTrue(clear["pve"]["chapters"][3]["stages"][2]["encounter"]["clue_active"])

    def test_late_relay_keeps_hp_and_resets_duel_status(self):
        stage = self.service.stage_map["4-1"]
        team = self.repo.get_user_fighters(self.user_id)
        enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
        scripted = ScriptedEngine(("a",) * 6)
        self.service.engine = scripted
        result = LatePveBattle(self.service, team, enemies, stage, stage["tactics"][0], set()).run()
        self.assertEqual(result["stars"], 3)
        self.assertEqual([call[0]["name"] for call in scripted.calls],
                         [team[0]["name"]] * 2 + [team[1]["name"]] * 2 + [team[2]["name"]] * 2)
        self.assertEqual(scripted.calls[1][0]["current_hp"], team[0]["stats"]["hp"] - 10)
        self.assertTrue(all("temporary_status" not in fighter for call in scripted.calls for fighter in call))
        defeated = ScriptedEngine(("b", "a", "a", "a", "a", "a", "a"))
        self.service.engine = defeated
        relay = LatePveBattle(self.service, team, enemies, stage, stage["tactics"][0], set()).run()
        self.assertTrue(relay["victory"])
        self.assertEqual(defeated.calls[1][0]["name"], team[1]["name"])

    def test_twin_bosses_keep_independent_health_and_chief_keeps_one_pool(self):
        class PhaseEngine:
            def __init__(self):
                self.calls = []

            def battle_with_events(self, fighter_a, fighter_b):
                self.calls.append((deepcopy(fighter_a), deepcopy(fighter_b)))
                floor = int(fighter_b.get("phase_hp_floor", 0))
                return {
                    "winner": None if floor else fighter_a["name"],
                    "state": {"fighter_a_hp": fighter_a["current_hp"] - 10,
                              "fighter_b_hp": floor, "actions": 1, "phase_boundary": floor > 0},
                    "events": [{"type": "battle_end", "time": 1}], "logs": [],
                }

        team = self.repo.get_user_fighters(self.user_id)
        twin = self.service.stage_map["5-5"]
        twin_enemies = [self.service._stage_enemy(twin, enemy) for enemy in twin["enemies"]]
        engine = PhaseEngine()
        self.service.engine = engine
        result = LatePveBattle(self.service, team, twin_enemies, twin, twin["tactics"][0], {"alliance_ledger"}).run()
        self.assertTrue(result["victory"])
        self.assertEqual(result["stars"], 3)
        self.assertEqual(len(engine.calls), 6)
        self.assertEqual([call[1]["name"] for call in engine.calls],
                         [twin_enemies[0]["name"], twin_enemies[1]["name"]] * 3)
        self.assertEqual(engine.calls[2][1]["current_hp"], round(twin_enemies[0]["stats"]["hp"] * .65))
        self.assertEqual(engine.calls[3][1]["current_hp"], round(twin_enemies[1]["stats"]["hp"] * .65))
        self.assertEqual(len(result["duels"][0]["enemyTeam"]), 2)

        chief = self.service.stage_map["5-6"]
        chief_enemy = self.service._stage_enemy(chief, chief["enemies"][0])
        engine = PhaseEngine()
        self.service.engine = engine
        result = LatePveBattle(self.service, team, [chief_enemy], chief, chief["tactics"][0], {"alliance_ledger"}).run()
        maximum = chief_enemy["stats"]["hp"]
        self.assertEqual([call[1]["current_hp"] for call in engine.calls],
                         [maximum, round(maximum * .75), round(maximum * .45), round(maximum * .15)])
        self.assertEqual(result["stars"], 3)
        self.assertEqual(result["mechanicResults"]["distinct_seal_breakers"], 3)

    def test_late_recommended_team_has_two_viable_tactics(self):
        templates = [self.repo.generate_preview_fighter(name) for name in ("平衡甲", "平衡乙", "平衡丙")]
        team = []
        for template in templates:
            fighter = dict(template)
            fighter["stats"] = self.repo._recalculate_final_stats(
                dict(template["raw_stats"]), 6.0, 1,
                template["martial_art"], template["neigong"], template["qinggong"],
            )
            team.append(fighter)
        clues = {"silver_rubbing", "boat_manifest", "vault_route", "gear_map", "passphrase", "alliance_ledger"}
        for stage_id in self.service.stage_order[18:]:
            stage = self.service.stage_map[stage_id]
            enemies = [self.service._stage_enemy(stage, enemy) for enemy in stage["enemies"]]
            for tactic in stage["tactics"]:
                wins = three_stars = 0
                for trial in range(30):
                    random.seed(20260927 + int(stage_id[0]) * 10000 + int(stage_id[-1]) * 1000 + trial)
                    result = LatePveBattle(self.service, team, enemies, stage, tactic, clues).run()
                    wins += int(result["victory"])
                    three_stars += int(result["stars"] == 3)
                self.assertGreaterEqual(wins, 4, (stage_id, tactic["id"]))
                self.assertGreaterEqual(three_stars, 1, (stage_id, tactic["id"]))


if __name__ == "__main__":
    unittest.main()
