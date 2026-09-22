"""Opt-in smoke test of the actual Bot renderer; no AstrBot or player data."""
import json
import random
from copy import deepcopy
from pathlib import Path

from PIL import Image
from engine import CombatEngine
from web_battle_renderer import render_battle_sequence
from test_battle_effects import fighter

ROOT = Path(__file__).parent


def main():
    arts = json.loads((ROOT / "configs/martial_arts.json").read_text(encoding="utf-8"))
    internals = json.loads((ROOT / "configs/neigong.json").read_text(encoding="utf-8"))
    steps = json.loads((ROOT / "configs/qinggong.json").read_text(encoding="utf-8"))
    ids = ["staff_bainiaochaofeng", "short_shenghuoling", "sword_xuantie", "fist_qishang", "whip_baimang"]
    segments = []
    for index, identifier in enumerate(ids):
        a, b = fighter("shared-gif-actor"), fighter("shared-gif-target")
        a["martial_art"] = deepcopy(next(art for art in arts if art["id"] == identifier))
        a["martial_art"]["moves"] = [a["martial_art"]["moves"][-1]]
        a["neigong"] = deepcopy(internals[-5 + index])
        a["qinggong"] = deepcopy(steps[-2 + index % 2])
        b["neigong"] = deepcopy(internals[-5 + (index + 1) % 5])
        b["stats"]["spd"] = 1
        random.seed(index)
        result = CombatEngine(max_actions=1).battle_with_events(a, b)
        segments.append({"fighter_a": a, "fighter_b": b, "result": result})
    output = render_battle_sequence(segments, str(ROOT / "output" / "bot-smoke"))
    assert output
    with Image.open(output) as gif:
        frames = gif.n_frames
        assert frames > 50
        for index in (0, frames // 2, frames - 1):
            gif.seek(index)
            assert gif.convert("RGB").getextrema() != ((255, 255),) * 3
        print(json.dumps({"file": output, "frames": frames, "size": gif.size, "segments": len(segments)}))


if __name__ == "__main__":
    main()
