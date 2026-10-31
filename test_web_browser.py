"""Exercise desktop/mobile login and PvE against a disposable Web server."""

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from hashlib import sha256
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from database import FighterRepository
from PIL import Image
from playwright.sync_api import sync_playwright
from web_auth import WebAuthRepository, WebIdentity

ROOT = Path(__file__).resolve().parent


class WebBrowserTests(unittest.TestCase):
    def test_desktop_mobile_login_pve_and_session_recovery(self):
        with tempfile.TemporaryDirectory(prefix="nfight-browser-") as directory:
            db_path = Path(directory) / "fighters.db"
            repo = FighterRepository(db_path)
            auth = WebAuthRepository(db_path)
            for user_id, prefix in [("10000011", "Desktop"), ("10000012", "Mobile")]:
                for index in range(1, 4):
                    repo.create_fighter_for_user(user_id, f"{prefix} hero {index}")
            avatar_dir = db_path.parent / "avatars"
            avatar_dir.mkdir()
            avatar_name = sha256(b"mobile hero 3").hexdigest()[:24] + ".img"
            avatar_path = avatar_dir / avatar_name
            Image.new("RGB", (16, 16), "red").save(avatar_path, format="PNG")
            repo.set_fighter_avatar_path(
                "10000012",
                "Mobile hero 3",
                "/AstrBot/data/name_fight_data/avatars/" + avatar_name,
            )
            with repo._connect() as connection:
                connection.execute(
                    "UPDATE fighters SET hp = 900, atk = 180, def = 150, spd = 120, crt = 50, eva = 45"
                )
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
            sock.close()
            origin = f"http://127.0.0.1:{port}"
            env = {
                **os.environ,
                "NFIGHT_DB_PATH": str(db_path),
                "NFIGHT_PUBLIC_ORIGIN": origin,
                "NFIGHT_WEB_PORT": str(port),
            }
            with (Path(directory) / "server.log").open("w") as log:
                server = subprocess.Popen(
                    [sys.executable, "run_web.py"],
                    cwd=ROOT / "web/backend",
                    env=env,
                    stdout=log,
                    stderr=log,
                )
                try:
                    opener = build_opener(ProxyHandler({}))
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        try:
                            with opener.open(origin + "/api/health", timeout=1):
                                break
                        except OSError:
                            time.sleep(0.1)
                    else:
                        self.fail("Disposable browser server did not start")
                    candidates = sorted(
                        (Path.home() / ".cache/ms-playwright").glob(
                            "chromium-*/chrome-linux*/chrome"
                        )
                    )
                    executable = os.environ.get("NFIGHT_TEST_BROWSER_EXECUTABLE") or (
                        str(candidates[-1]) if candidates else None
                    )
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(
                            executable_path=executable,
                            headless=True,
                            args=["--no-sandbox"],
                        )
                        try:
                            for user_id, prefix, viewport in [
                                (
                                    "10000011",
                                    "Desktop",
                                    {"width": 1440, "height": 1000},
                                ),
                                ("10000012", "Mobile", {"width": 390, "height": 844}),
                            ]:
                                context = browser.new_context(
                                    viewport=viewport,
                                    is_mobile=prefix == "Mobile",
                                    has_touch=prefix == "Mobile",
                                )
                                page = context.new_page()
                                errors = []
                                challenge_creations = []
                                page.on(
                                    "request",
                                    lambda request: (
                                        challenge_creations.append(request.url)
                                        if request.url.endswith("/api/auth/challenge")
                                        else None
                                    ),
                                )
                                page.on(
                                    "pageerror", lambda error: errors.append(str(error))
                                )
                                with page.expect_response(
                                    "**/api/auth/challenge"
                                ) as response:
                                    page.goto(origin)
                                challenge = response.value.json()
                                page.get_by_role(
                                    "heading", name="用你的 QQ 角色进入江湖"
                                ).wait_for()
                                screenshot_dir = os.environ.get(
                                    "NFIGHT_TEST_SCREENSHOT_DIR"
                                )
                                if screenshot_dir:
                                    Path(screenshot_dir).mkdir(
                                        parents=True, exist_ok=True
                                    )
                                    page.screenshot(
                                        path=str(
                                            Path(screenshot_dir)
                                            / (prefix.lower() + "-login.png")
                                        ),
                                        full_page=True,
                                    )
                                self.assertFalse(
                                    page.evaluate(
                                        "document.documentElement.scrollWidth > window.innerWidth"
                                    )
                                )
                                if prefix == "Mobile":
                                    # A pending code survives a page reload before group verification.
                                    with page.expect_response(
                                        "**/api/auth/challenge/exchange"
                                    ):
                                        page.reload()
                                    page.get_by_label("QQ 群验证指令").wait_for()
                                    self.assertEqual(
                                        page.get_by_label("QQ 群验证指令").inner_text(),
                                        challenge["command"],
                                    )
                                    self.assertEqual(len(challenge_creations), 1)
                                    # Simulate QQ destroying the old Web view while the player verifies.
                                    page.goto("about:blank")
                                auth.confirm(
                                    challenge["code"],
                                    WebIdentity(
                                        user_id,
                                        "20000011",
                                        prefix
                                        if prefix == "Desktop"
                                        else "Mobile玩家" * 8,
                                    ),
                                )
                                if prefix == "Mobile":
                                    page.goto(origin)
                                page.get_by_role(
                                    "button", name="退出登录", exact=True
                                ).wait_for(timeout=10000)
                                if prefix == "Mobile":
                                    self.assertEqual(len(challenge_creations), 1)
                                    page.wait_for_function(
                                        "Array.from(document.images).some(image => image.src.includes('/avatar') && image.complete && image.naturalWidth === 16)"
                                    )
                                    previous_time = avatar_path.stat().st_mtime_ns
                                    Image.new("RGB", (20, 20), "blue").save(
                                        avatar_path, format="PNG"
                                    )
                                    os.utime(
                                        avatar_path,
                                        ns=(
                                            previous_time + 1_000_000,
                                            previous_time + 1_000_000,
                                        ),
                                    )
                                    page.get_by_role(
                                        "button", name="刷新存档", exact=True
                                    ).click()
                                    page.wait_for_function(
                                        "Array.from(document.images).some(image => image.src.includes('/avatar') && image.complete && image.naturalWidth === 20)"
                                    )
                                self.assertIn(
                                    prefix + " hero 3",
                                    page.locator("body").inner_text(),
                                )
                                self.assertNotIn(
                                    ("Mobile" if prefix == "Desktop" else "Desktop")
                                    + " hero 1",
                                    page.locator("body").inner_text(),
                                )
                                page.get_by_role(
                                    "button", name="江湖历练", exact=True
                                ).click()
                                page.locator(".pve-roster button").first.wait_for()
                                self.assertFalse(
                                    page.evaluate(
                                        "document.documentElement.scrollWidth > window.innerWidth"
                                    )
                                )
                                self.assertTrue(
                                    page.locator(".account-label").evaluate(
                                        "node => node.scrollWidth <= node.clientWidth + 1"
                                    )
                                )
                                if screenshot_dir:
                                    page.screenshot(
                                        path=str(
                                            Path(screenshot_dir)
                                            / (prefix.lower() + "-pve.png")
                                        ),
                                        full_page=True,
                                    )
                                for index in range(3):
                                    page.locator(".pve-roster button").nth(
                                        index
                                    ).click()
                                with page.expect_response(
                                    "**/api/pve/stages/1-1/challenge"
                                ) as result:
                                    page.locator(".pve-challenge").click()
                                self.assertTrue(result.value.json()["victory"])
                                self.assertEqual(
                                    repo.get_pve_profile(user_id)["energy"], 90
                                )
                                page.reload()
                                page.get_by_role(
                                    "button", name="退出登录", exact=True
                                ).wait_for()
                                repo.grant_points(user_id, 7)
                                page.get_by_role(
                                    "button", name="刷新存档", exact=True
                                ).click()
                                page.wait_for_function(
                                    "expected => document.body.innerText.includes('积分 ' + expected)",
                                    arg=repo.get_user_points(user_id),
                                )
                                # Resume an interactive chapter after a full page reload.
                                if prefix == "Desktop":
                                    with repo._connect() as connection:
                                        connection.execute(
                                            "INSERT INTO pve_stage_progress VALUES (?, '2-6', 1, 1, 1, 1)",
                                            (user_id,),
                                        )
                                    pending = page.evaluate("""async () => {
                                        const response = await fetch('/api/pve/stages/3-1/challenge', {
                                            method: 'POST', headers: {'Content-Type': 'application/json'},
                                            body: JSON.stringify({tacticId: '3-1-rush'})
                                        });
                                        return response.json();
                                    }""")
                                    self.assertEqual(pending["status"], "pending")
                                    page.reload()
                                    with page.expect_response(
                                        "**/api/pve/attempt"
                                    ) as resumed:
                                        page.get_by_role(
                                            "button", name="江湖历练", exact=True
                                        ).click()
                                    self.assertEqual(
                                        resumed.value.json()["attemptId"],
                                        pending["attemptId"],
                                    )
                                page.get_by_role(
                                    "button", name="退出登录", exact=True
                                ).click()
                                page.get_by_role(
                                    "heading", name="用你的 QQ 角色进入江湖"
                                ).wait_for()
                                self.assertEqual(errors, [])
                                context.close()
                        finally:
                            browser.close()
                finally:
                    server.terminate()
                    server.wait(timeout=10)
