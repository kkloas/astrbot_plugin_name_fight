"""Exercise the real duel HTTP endpoint against a disposable SQLite database."""
import importlib
from contextlib import contextmanager
import json
import socket
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

from database import FighterRepository
from pve import PveService

sys.path.insert(0, str(Path(__file__).parent / "web" / ".python-packages"))
import uvicorn


class ClosingRepository(FighterRepository):
    @contextmanager
    def _connect(self):
        connection = super()._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()


class WebBattleEventsTest(unittest.TestCase):
    def test_duel_http_contract(self):
        with tempfile.TemporaryDirectory(prefix="name-fight-replay-") as directory:
            db_path = Path(directory) / "fighters.db"
            sqlite3.connect(db_path).close()
            repo = ClosingRepository(db_path)
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
                        req = Request(f"http://127.0.0.1:{port}/api/{route}", data=data,
                                      headers={"Content-Type": "application/json"})
                        with urlopen(req, timeout=5) as response:
                            return json.load(response)

                    request("fighters", {"name": "回放测试角色"})
                    result = request("battles/duel", {"attackerName": "回放测试角色"})
                    self.assertIn("snapshot", result)
                    self.assertIsNone(result["rating"])
                    self.assertEqual(result["events"][0]["type"], "battle_start")
                    self.assertEqual(result["events"][-1]["type"], "battle_end")
                    hp = {"a": result["attacker"]["stats"]["hp"], "b": result["defender"]["stats"]["hp"]}
                    for event in result["events"]:
                        if "hpAfter" in event:
                            self.assertEqual(hp[event["target"]], event["hpBefore"])
                            hp[event["target"]] = event["hpAfter"]
                    self.assertEqual(hp["a"], result["state"]["fighter_a_hp"])
                    self.assertEqual(hp["b"], result["state"]["fighter_b_hp"])
                    self.assertEqual(request("session/bootstrap")["fighters"][0]["battles"], 0)
                finally:
                    server.should_exit = True
                    thread.join(timeout=5)
                    sock.close()
                    self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
