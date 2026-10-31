"""Authenticated world boss API, ownership, replay and resource contracts."""

import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database import FighterRepository
from fastapi.testclient import TestClient
from web_auth import WebAuthRepository, WebIdentity
from world_boss import default_boss


class WorldBossApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = FighterRepository(Path(self.temp.name) / "test.db")
        for i in range(3):
            self.repo.create_fighter_for_user("u1", f"api-boss-{i}")
        name, a, b = default_boss(self.repo)
        self.activity = self.repo.open_group_boss("g1", name, a, b, "admin")
        with patch("database.FighterRepository", return_value=self.repo):
            self.api = importlib.import_module("web.backend.app")
        self.repo_patch = patch.object(self.api, "repo", self.repo)
        self.repo_patch.start()
        self.addCleanup(self.repo_patch.stop)
        auth = WebAuthRepository(self.repo.db_path)
        self.auth_patch = patch.object(self.api, "auth", auth)
        self.auth_patch.start()
        self.addCleanup(self.auth_patch.stop)
        device, code, _ = auth.create_challenge()
        auth.confirm(code, WebIdentity("u1", "g1", "Test player"))
        self.token = auth.exchange(device)
        self.client = TestClient(self.api.app, base_url=self.api.PUBLIC_ORIGIN)
        self.addCleanup(self.client.close)
        self.client.headers.update(
            {
                "Origin": self.api.PUBLIC_ORIGIN,
                "Cookie": f"{self.api.SESSION_COOKIE}={self.token}",
            }
        )

    def test_authenticated_challenge_retry_replay_and_practice(self):
        state = self.client.get("/api/world-boss").json()
        self.assertEqual(state["teamSlots"], [1, 2, 3])
        self.assertEqual(len(state["assets"]), 2)
        data = {
            "requestId": "test_request_0001",
            "bossId": self.activity["boss_id"],
            "slots": [1, 2, 3],
            "practice": True,
        }
        response = self.client.post("/api/world-boss/challenge", json=data)
        self.assertEqual(response.status_code, 200, response.text)
        practice = response.json()
        self.assertEqual(practice["remaining_attempts"], 3)
        self.assertEqual(practice["creditedDamage"], 0)
        self.assertEqual(
            self.client.post("/api/world-boss/challenge", json=data).json(), practice
        )
        self.assertEqual(self.client.get("/api/world-boss/replay").json(), practice)
        self.assertNotIn("fighter_a", practice["duels"][0])
        self.assertNotIn("result", practice["duels"][0])
        data.update(requestId="test_request_0002", practice=False)
        real = self.client.post("/api/world-boss/challenge", json=data)
        self.assertEqual(real.status_code, 200, real.text)
        self.assertEqual(real.json()["remaining_attempts"], 2)
        self.assertEqual(
            self.client.get("/api/world-boss").json()["remainingAttempts"], 2
        )
        self.assertEqual(
            self.client.post("/api/world-boss/challenge", json=data).json(), real.json()
        )

    def test_auth_origin_group_and_team_validation(self):
        data = {"requestId": "test_request_0001", "bossId": self.activity["boss_id"]}
        with TestClient(self.api.app, base_url=self.api.PUBLIC_ORIGIN) as anonymous:
            self.assertEqual(anonymous.get("/api/world-boss/replay").status_code, 401)
            self.assertEqual(
                anonymous.post(
                    "/api/world-boss/challenge",
                    json=data,
                    headers={"Origin": self.api.PUBLIC_ORIGIN},
                ).status_code,
                401,
            )
        self.assertEqual(
            self.client.post(
                "/api/world-boss/challenge",
                json=data,
                headers={"Origin": "https://untrusted.invalid"},
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                "/api/world-boss/challenge", json={**data, "slots": [1, 1, 2]}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/world-boss/challenge", json={**data, "phase": "phase2"}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/world-boss/challenge", json={**data, "requestId": "../../file"}
            ).status_code,
            422,
        )
        name, a, b = default_boss(self.repo)
        other = self.repo.open_group_boss("other-group", name, a, b, "admin")
        self.assertEqual(
            self.client.post(
                "/api/world-boss/challenge", json={**data, "bossId": other["boss_id"]}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get("/api/world-boss").json()["remainingAttempts"], 3
        )

    def test_assets_are_served_and_manifest_matches_bot(self):
        state = self.client.get("/api/world-boss").json()
        for asset in state["assets"].values():
            response = self.client.get(asset["portrait"])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["content-type"], "image/png")
            self.assertGreater(len(response.content), 1000)
        self.assertEqual(self.client.get("/boss-assets/missing.png").status_code, 404)


if __name__ == "__main__":
    unittest.main()
