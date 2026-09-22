"""Seeded new-art matchups using real modifiers and combat, without player data."""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from database import FighterRepository
from engine import CombatEngine

ROOT = Path(__file__).parent
NEW_IDS = ("sword_danyu", "blade_jingchao")


def load(name):
    return json.loads((ROOT / "configs" / f"{name}.json").read_text(encoding="utf-8"))


def make_fighter(name, base, art, inner, light):
    # This method is stateless; no repository initialization or SQLite is needed.
    stats = FighterRepository._apply_modifiers(None, base, art, inner, light)
    return dict(name=name, stats=stats, martial_art=art, neigong=inner, qinggong=light)


def evaluate(seeds=32):
    arts, inners, lights = load("martial_arts"), load("neigong"), load("qinggong")
    panels = [dict(hp=180, atk=50, **{"def": 40}, spd=35, crt=12, eva=12),
              dict(hp=240, atk=80, **{"def": 60}, spd=50, crt=22, eva=22),
              dict(hp=300, atk=110, **{"def": 85}, spd=70, crt=32, eva=32)]
    result = {"seeds_per_pair": seeds, "panels": panels, "arts": {}}
    engine = CombatEngine()
    rng_state = random.getstate()
    try:
        for art in (a for a in arts if a["id"] in NEW_IDS):
            summary = {}
            for old in (a for a in arts if a["id"] not in NEW_IDS):
                counts = Counter()
                # Rotate opponents' loadouts; repeat with loadouts exchanged.
                for panel_index, base in enumerate(panels):
                    for n in range(max(len(inners), len(lights))):
                        a_inner, b_inner = inners[n % len(inners)], inners[(n + 1) % len(inners)]
                        a_light, b_light = lights[n % len(lights)], lights[(n + 2) % len(lights)]
                        for exchange in (False, True):
                            a = make_fighter("new", base, art, b_inner if exchange else a_inner, b_light if exchange else a_light)
                            b = make_fighter("old", base, old, a_inner if exchange else b_inner, a_light if exchange else b_light)
                            for seed in range(seeds):
                                for reverse in (False, True):
                                    random.seed(17000 + panel_index * 10000 + n * 1000 + seed)
                                    _, winner, state = engine.battle_with_state(b, a) if reverse else engine.battle_with_state(a, b)
                                    counts[winner or "draw"] += 1
                                    counts["games"] += 1
                                    counts["remaining_hp"] += state["fighter_b_hp" if reverse else "fighter_a_hp"]
                summary[old["id"]] = {"name": old["name"], "games": counts["games"],
                    "wins": counts["new"], "draws": counts["draw"],
                    "score_rate": round((counts["new"] + .5 * counts["draw"]) / counts["games"], 4),
                    "mean_remaining_hp": round(counts["remaining_hp"] / counts["games"], 2)}
            games = sum(row["games"] for row in summary.values())
            result["arts"][art["id"]] = {"name": art["name"], "games": games,
                "score_rate": round(sum(row["wins"] + .5 * row["draws"] for row in summary.values()) / games, 4),
                "matchups": summary}
    finally:
        random.setstate(rng_state)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    report = evaluate(args.seeds)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
