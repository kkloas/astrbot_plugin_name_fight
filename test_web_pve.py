from __future__ import annotations

import importlib
import json
import socket
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from database import FighterRepository
from pve import PveService

sys.path.insert(0, str(Path(__file__).parent / "web" / ".python-packages"))
import uvicorn


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


class WebPveApiTest(unittest.TestCase):
    def test_team_challenge_progress_and_non_ranked_contract(self):
        with tempfile.TemporaryDirectory(prefix="name-fight-web-pve-") as directory:
            repo = ClosingRepository(Path(directory) / "fighters.db")
            with patch("database.FighterRepository", return_value=repo):
                api = importlib.import_module("web.backend.app")
            with patch.object(api, "repo", repo):
                api.pve = PveService(repo, api.engine)
                sock = socket.socket()
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
                server = uvicorn.Server(uvicorn.Config(api.app, log_level="error", ws="none"))
                thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
                thread.start()
                try:
                    deadline = time.monotonic() + 5
                    while not server.started and time.monotonic() < deadline:
                        time.sleep(.01)
                    self.assertTrue(server.started)

                    def request(route, body=None):
                        data = None if body is None else json.dumps(body).encode("utf-8")
                        req = Request(
                            f"http://127.0.0.1:{port}/api/{route}",
                            data=data,
                            headers={"Content-Type": "application/json"},
                        )
                        with urlopen(req, timeout=10) as response:
                            return json.load(response)

                    for name in ("接口历练甲", "接口历练乙", "接口历练丙"):
                        request("fighters", {"name": name})
                    with repo._connect() as connection:
                        connection.execute("UPDATE fighters SET hp=900, atk=180, def=150, spd=120, crt=50, eva=45")
                        connection.commit()
                    team = request("pve/team", {"slots": [1, 2, 3]})
                    self.assertEqual(team["profile"]["team_slots"], [1, 2, 3])
                    before = request("pve")
                    self.assertTrue(before["chapters"][0]["stages"][0]["unlocked"])
                    self.assertFalse(before["chapters"][0]["stages"][1]["unlocked"])
                    result = request("pve/stages/1-1/challenge", {})
                    self.assertTrue(result["victory"])
                    self.assertEqual(result["profile"]["energy"], 90)
                    self.assertTrue(result["pve"]["chapters"][0]["stages"][1]["unlocked"])
                    self.assertGreaterEqual(len(result["duels"]), 3)
                    bootstrap = request("session/bootstrap")
                    self.assertEqual(bootstrap["pveSummary"]["profile"]["energy"], 90)
                    self.assertTrue(all(fighter["battles"] == 0 for fighter in bootstrap["fighters"]))
                    self.assertEqual(request("leaderboards/duel")["leaderboard"], [])
                    shop = request("shop")["shop"]
                    energy_item = next(item for item in shop if item["item_id"] == "energy_pill")
                    self.assertEqual(energy_item["price"], 80)
                    self.assertTrue(energy_item["description"])
                    with repo._connect() as connection:
                        connection.execute(
                            "UPDATE user_wallets SET points = 200 WHERE user_id = ?",
                            (api.DEFAULT_USER_ID,),
                        )
                        connection.commit()
                    request("shop/buy", {"itemId": "energy_pill", "quantity": 1})
                    used = request("items/use", {"itemId": "energy_pill"})
                    self.assertEqual(used["result"]["restored"], 10)
                    self.assertEqual(used["state"]["pveSummary"]["profile"]["energy"], 100)
                    self.assertFalse(any(item["item_id"] == "energy_pill" for item in used["state"]["items"]))
                    request("shop/buy", {"itemId": "energy_pill", "quantity": 1})
                    with self.assertRaises(HTTPError) as full_energy_error:
                        request("items/use", {"itemId": "energy_pill"})
                    self.assertEqual(full_energy_error.exception.code, 400)
                    full_energy_error.exception.close()
                    after_rejected_use = request("session/bootstrap")
                    energy_bag = next(item for item in after_rejected_use["items"] if item["item_id"] == "energy_pill")
                    self.assertEqual(energy_bag["quantity"], 1)
                    with self.assertRaises(HTTPError) as error:
                        request("pve/chapters/chapter_1/rewards/18/claim", {})
                    self.assertEqual(error.exception.code, 400)
                    error.exception.close()
                finally:
                    server.should_exit = True
                    thread.join(timeout=5)
                    sock.close()
                    self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
