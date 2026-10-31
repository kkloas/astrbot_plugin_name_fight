"""Verify browser binding, QQ event trust, and shared-account HTTP isolation."""

import ast
import asyncio
import importlib
import os
import tempfile
import time
import unittest
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from database import FighterRepository
from fastapi.testclient import TestClient
from PIL import Image
from pve import PveService
from web_auth import AuthRateLimited, WebAuthRepository, WebIdentity, qq_group_identity


def qq_event(user_id="10000001", group_id="20000001", platform="aiocqhttp"):
    event = Mock()
    event.get_platform_name.return_value = platform
    event.get_sender_id.return_value = user_id
    event.get_group_id.return_value = group_id
    event.get_sender_name.return_value = "QQ player"
    event.plain_result.side_effect = str
    event.send = AsyncMock()
    return event


class WebAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "fighters.db"
        self.repo = FighterRepository(self.path)
        self.auth = WebAuthRepository(self.path)
        self.identity = WebIdentity("10000001", "20000001", "Player A")

    def tearDown(self):
        self.temp.cleanup()

    def test_browser_binding_single_use_and_logout(self):
        device, code, _ = self.auth.create_challenge()
        self.assertIsNone(self.auth.exchange(device))
        self.auth.confirm(code.lower(), self.identity)
        with self.assertRaises(ValueError):
            self.auth.confirm(code, self.identity)
        with self.assertRaises(ValueError):
            self.auth.exchange(code)
        with self.assertRaises(ValueError):
            self.auth.exchange("other-browser")
        token = self.auth.exchange(device)
        self.assertEqual(self.auth.get_identity(token), self.identity)
        with self.assertRaises(ValueError):
            self.auth.exchange(device)
        self.auth.logout(token)
        self.assertIsNone(self.auth.get_identity(token))

    def test_expiry_and_regeneration(self):
        device, code, expires = self.auth.create_challenge()
        with patch("web_auth.time.time", return_value=expires + 1):
            with self.assertRaises(ValueError):
                self.auth.confirm(code, self.identity)
            with self.assertRaises(ValueError):
                self.auth.exchange(device)
        device, _, _ = self.auth.create_challenge()
        self.auth.create_challenge(device)
        with self.assertRaises(ValueError):
            self.auth.exchange(device)
        device, code, _ = self.auth.create_challenge()
        self.auth.confirm(code, self.identity)
        token = self.auth.exchange(device)
        with patch("web_auth.time.time", return_value=time.time() + 8 * 86400):
            self.assertIsNone(self.auth.get_identity(token))

    def test_rate_limit_and_credentials_are_hashed(self):
        device, code, _ = self.auth.create_challenge()
        self.auth.confirm(code, self.identity)
        token = self.auth.exchange(device)
        with self.repo._connect() as connection:
            rows = connection.execute(
                "SELECT token_hash FROM web_login_sessions"
            ).fetchall()
        self.assertNotIn(token, [row[0] for row in rows])
        for _ in range(5):
            self.auth.rate_limit("test", "subject", 5)
        with self.assertRaises(AuthRateLimited):
            self.auth.rate_limit("test", "subject", 5)

    def test_trusted_qq_event_and_actual_bot_command(self):
        self.assertEqual(qq_group_identity(qq_event()).user_id, "10000001")
        for event in [
            qq_event(group_id=""),
            qq_event(platform="discord"),
            qq_event(user_id=""),
            qq_event(user_id="１２３４５"),
        ]:
            with self.assertRaises(ValueError):
                qq_group_identity(event)
        tree = ast.parse(
            Path(__file__).with_name("main.py").read_text(encoding="utf-8-sig")
        )
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "nfweb"
        )
        method.decorator_list = []
        namespace = {
            "asyncio": asyncio,
            "qq_group_identity": qq_group_identity,
            "logger": Mock(),
            "AstrMessageEvent": object,
        }
        exec(
            compile(ast.Module(body=[method], type_ignores=[]), "main.py", "exec"),
            namespace,
        )
        bot = Mock(web_auth=self.auth)
        for event in [qq_event(group_id=""), qq_event(platform="discord")]:
            device, code, _ = self.auth.create_challenge()
            asyncio.run(namespace["nfweb"](bot, event, code))
            self.assertIsNone(self.auth.exchange(device))
        device, code, _ = self.auth.create_challenge()
        asyncio.run(namespace["nfweb"](bot, qq_event(), code))
        self.assertEqual(
            self.auth.get_identity(self.auth.exchange(device)).user_id, "10000001"
        )


class WebAccountHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = FighterRepository(Path(self.temp.name) / "fighters.db")
        with patch("database.FighterRepository", return_value=self.repo):
            self.api = importlib.import_module("web.backend.app")
        self.patches = [
            patch.object(self.api, "repo", self.repo),
            patch.object(self.api, "auth", WebAuthRepository(self.repo.db_path)),
            patch.object(self.api, "pve", PveService(self.repo, self.api.engine)),
        ]
        for item in self.patches:
            item.start()
        self.clients = []

    def tearDown(self):
        for client in self.clients:
            client.close()
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def client(self):
        client = TestClient(
            self.api.app,
            base_url=self.api.PUBLIC_ORIGIN,
            headers={"Origin": self.api.PUBLIC_ORIGIN},
        )
        self.clients.append(client)
        return client

    def login(self, client, user_id="10000001", group_id="20000001"):
        challenge = client.post("/api/auth/challenge")
        self.assertEqual(challenge.status_code, 200)
        self.api.auth.confirm(
            challenge.json()["code"],
            WebIdentity(user_id, group_id, "Player " + user_id),
        )
        result = client.post("/api/auth/challenge/exchange")
        self.assertEqual(result.json()["status"], "authenticated")
        self.assertIn("HttpOnly", result.headers["set-cookie"])
        self.assertIn("SameSite=strict", result.headers["set-cookie"])
        self.assertIn("Secure", result.headers["set-cookie"])

    def test_anonymous_and_cross_origin_access(self):
        client = self.client()
        for path in [
            "session/bootstrap",
            "fighters",
            "items",
            "wallet",
            "shop",
            "pve",
            "pve/attempt",
            "world-boss",
            "leaderboards/duel",
        ]:
            self.assertEqual(client.get("/api/" + path).status_code, 401)
        self.assertEqual(client.get("/api/health").json(), {"status": "ok"})
        for origin in ["https://evil.example", "null", ""]:
            self.assertEqual(
                client.post(
                    "/api/auth/challenge", headers={"Origin": origin}
                ).status_code,
                403,
            )
        game_routes = [
            route
            for route in self.api.app.routes
            if getattr(route, "path", "").startswith("/api/")
            and not route.path.startswith("/api/auth/")
            and route.path not in {"/api/health", "/api/{path:path}"}
        ]
        self.assertTrue(
            all(
                any(
                    dep.call == self.api.require_session
                    for dep in route.dependant.dependencies
                )
                for route in game_routes
            )
        )

    def test_http_entry_redirects_before_authentication(self):
        client = self.client()
        http_origin = self.api.PUBLIC_ORIGIN.replace("https://", "http://", 1)
        response = client.get(http_origin + "/?from=qq", follow_redirects=False)
        self.assertEqual(response.status_code, 307)

        self.assertEqual(
            response.headers["location"], self.api.PUBLIC_ORIGIN + "/?from=qq"
        )
        response = client.post(
            http_origin + "/api/auth/challenge",
            headers={"Origin": http_origin},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 307)
        self.assertNotIn("set-cookie", response.headers)
        self.assertEqual(
            client.post(
                response.headers["location"], headers={"Origin": http_origin}
            ).status_code,
            403,
        )
        self.assertEqual(
            client.get("http://127.0.0.1:8001/api/health").status_code, 200
        )

    def test_showcase_requires_login_and_uses_new_loadouts(self):
        client = self.client()
        self.assertEqual(client.post("/api/battles/showcase", json={}).status_code, 401)
        self.login(client)
        response = client.post("/api/battles/showcase", json={})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["attacker"]["martialArt"]["id"], "sword_xuanmo")
        self.assertEqual(result["defender"]["martialArt"]["id"], "blade_chixiao")
        self.assertTrue(result["events"])

    def test_same_qq_can_login_and_logout_in_independent_browsers(self):
        desktop, mobile = self.client(), self.client()
        self.repo.create_fighter_for_user("10000001", "Shared hero")
        self.login(desktop)
        self.login(mobile)
        desktop_token = desktop.cookies.get(self.api.SESSION_COOKIE)
        mobile_token = mobile.cookies.get(self.api.SESSION_COOKIE)
        self.assertNotEqual(desktop_token, mobile_token)
        for client in [desktop, mobile]:
            response = client.get("/api/session/bootstrap")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["session"]["userId"], "10000001")
            self.assertEqual(response.json()["fighters"][0]["name"], "Shared hero")
        self.assertEqual(desktop.post("/api/signin").status_code, 200)
        self.assertEqual(mobile.post("/api/signin").status_code, 400)
        self.assertEqual(mobile.get("/api/wallet").json()["wallet"]["points"], 50)
        self.login(desktop)
        self.assertIsNone(self.api.auth.get_identity(desktop_token))
        self.assertIsNotNone(self.api.auth.get_identity(mobile_token))
        self.assertEqual(desktop.post("/api/auth/logout").status_code, 200)
        self.assertEqual(desktop.get("/api/session/bootstrap").status_code, 401)
        self.assertEqual(mobile.get("/api/session/bootstrap").status_code, 200)

    def test_owned_bot_avatar_relocation_and_refresh(self):
        owner, other = self.client(), self.client()
        self.repo.create_fighter_for_user("10000001", "Alice")
        self.repo.create_fighter_for_user("10000002", "Bob")
        self.login(owner)
        self.login(other, "10000002")
        filename = sha256(b"alice").hexdigest()[:24] + ".img"
        path = self.repo.db_path.parent / "avatars" / filename
        path.parent.mkdir()
        Image.new("RGB", (16, 16), "red").save(path, format="PNG")
        legacy = "/AstrBot/data/name_fight_data/avatars/" + filename
        self.repo.set_fighter_avatar_path("10000001", "Alice", legacy)
        first_url = owner.get("/api/session/bootstrap").json()["fighters"][0][
            "avatarPath"
        ]
        response = owner.get(first_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.content, path.read_bytes())
        self.assertEqual(other.get(first_url).status_code, 404)
        self.assertEqual(
            self.repo.get_user_fighter_by_name("10000001", "Alice")["avatar_path"],
            legacy,
        )
        with self.repo._connect() as connection:
            connection.execute(
                "UPDATE fighters SET star_rating = 5.0 WHERE name = 'Alice'"
            )
        card_root = self.repo.db_path.parent / "card-test"
        (card_root / "data").mkdir(parents=True)
        Image.new("RGB", (1024, 1024), "white").save(
            card_root / "data/5star_template.jpg"
        )
        with patch.object(self.api, "ROOT_DIR", card_root):
            card = owner.get("/api/fighters/Alice/card")
        self.assertEqual(card.status_code, 200)
        with Image.open(BytesIO(card.content)) as image:
            red, green, blue = image.getpixel((229, 199))
            self.assertGreater(red, 200)
            self.assertLess(green, 50)
            self.assertLess(blue, 50)
        previous_time = path.stat().st_mtime_ns
        Image.new("RGB", (20, 20), "blue").save(path, format="PNG")
        os.utime(path, ns=(previous_time + 1_000_000, previous_time + 1_000_000))
        second_url = owner.get("/api/session/bootstrap").json()["fighters"][0][
            "avatarPath"
        ]
        self.assertNotEqual(first_url, second_url)
        self.assertEqual(owner.get(second_url).content, path.read_bytes())
        outside = self.repo.db_path.parent / "private.txt"
        outside.write_text("private file", encoding="utf-8")
        path.unlink()
        path.symlink_to(outside)
        self.assertEqual(owner.get(second_url).status_code, 404)
        self.assertIsNone(
            owner.get("/api/session/bootstrap").json()["fighters"][0]["avatarPath"]
        )

    def test_http_challenge_cannot_be_redeemed_elsewhere(self):
        a, b = self.client(), self.client()
        challenge = a.post("/api/auth/challenge").json()
        self.api.auth.confirm(
            challenge["code"], WebIdentity("10000001", "20000001", "A")
        )
        self.assertEqual(
            b.post(
                "/api/auth/challenge/exchange", json={"code": challenge["code"]}
            ).status_code,
            410,
        )
        self.assertEqual(a.post("/api/auth/challenge/exchange").status_code, 200)
        self.assertEqual(a.post("/api/auth/challenge/exchange").status_code, 410)

    def test_two_accounts_share_bot_data_without_cross_access(self):
        a, b = self.client(), self.client()
        self.repo.create_fighter_for_user("10000001", "Alice")
        self.repo.create_fighter_for_user("10000002", "Bob")
        self.login(a)
        self.login(b, "10000002", "20000002")
        first = a.get("/api/session/bootstrap?userId=10000002").json()
        second = b.get("/api/session/bootstrap").json()
        self.assertEqual([fighter["name"] for fighter in first["fighters"]], ["Alice"])
        self.assertEqual([fighter["name"] for fighter in second["fighters"]], ["Bob"])
        self.assertEqual(first["session"]["groupId"], "20000001")
        self.assertEqual(second["session"]["groupId"], "20000002")
        self.assertEqual(a.get("/api/fighters/Bob/card").status_code, 404)
        self.assertEqual(a.get("/api/fighters/Bob/avatar").status_code, 404)
        self.repo.grant_points("10000001", 200)
        self.assertEqual(a.get("/api/wallet").json()["wallet"]["points"], 200)
        self.assertEqual(
            a.post(
                "/api/shop/buy", json={"itemId": "star_exp_pill_s", "quantity": 1}
            ).status_code,
            200,
        )
        before = self.repo.get_user_items("10000001")
        self.assertEqual(
            a.post(
                "/api/fighters/Bob/feed", json={"itemId": "star_exp_pill_s"}
            ).status_code,
            400,
        )
        self.assertEqual(self.repo.get_user_items("10000001"), before)
        self.assertEqual(
            a.post("/api/fighters/active", json={"name": "Bob"}).status_code, 400
        )
        self.assertEqual(b.get("/api/items").json()["items"], [])
        self.assertEqual(
            a.post(
                "/api/pve/attempts/other-account/switch",
                json={"decisionCount": 0, "fighterIndex": 0},
            ).status_code,
            400,
        )
        self.assertEqual(a.post("/api/auth/logout").status_code, 200)
        self.assertEqual(a.get("/api/session/bootstrap").status_code, 401)
