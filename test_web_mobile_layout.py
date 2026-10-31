"""Check usable phone layouts against a disposable account and Web server."""

import os
import socket
import subprocess
import tempfile
import time
import unittest
from io import BytesIO
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from database import FighterRepository
from PIL import Image
from playwright.sync_api import sync_playwright
from web_auth import WebAuthRepository, WebIdentity

ROOT = Path(__file__).resolve().parent


class WebMobileLayoutTests(unittest.TestCase):
    def assert_content_fits(self, page):
        # Root overflow alone misses children clipped by overflow:hidden panels.
        page.wait_for_timeout(600)
        problems = page.evaluate("""() => {
            const problems = [];
            const controls = document.querySelectorAll(
                'button, input, select, .fighter-card, .hero-card, .rank-row, .item-modal'
            );
            for (const node of controls) {
                if (!node.getClientRects().length) continue;
                const box = node.getBoundingClientRect();
                if (box.width && (box.left < -1 || box.right > innerWidth + 1)) {
                    problems.push([node.className || node.tagName, node.textContent.slice(0, 40), box.left, box.right]);
                }
            }
            const text = document.querySelectorAll(
                '.hero-meta h3, .hero-meta p, .stat-label, .stat-value, .chip-value, .chip-comment, ' +
                '.rank-row > *, .pve-roster strong, .pve-roster small, .pve-order > div > span, ' +
                '.team-rail strong, .team-rail small, .duel-name strong'
            );
            for (const node of text) {
                if (!node.getClientRects().length) continue;
                const box = node.getBoundingClientRect();
                const range = document.createRange();
                range.selectNodeContents(node);
                for (const rect of range.getClientRects()) {
                    if (rect.left < box.left - 1 || rect.right > box.right + 1 || rect.right > innerWidth + 1) {
                        problems.push(['clipped text', node.textContent.slice(0, 40), rect.left, rect.right]);
                        break;
                    }
                }
            }
            return problems;
        }""")
        self.assertEqual(problems, [], f"Clipped content at {page.viewport_size}")

    def assert_mobile_hud_rendering(self, page, battle):
        # Check rendered progress against the recorded HP and accessible gauge values.
        page.emulate_media(reduced_motion="no-preference")
        maximum = float(page.locator(".duel-scrubber").get_attribute("max"))
        for fraction in [0, 0.15, 0.3, 0.45, 0.6, 0.75]:
            replay_time = round(maximum * fraction)
            hp = [
                battle[side].get("currentHp", battle[side]["stats"]["hp"])
                for side in ["attacker", "defender"]
            ]
            for event in battle["events"]:
                if (
                    event["time"] <= replay_time
                    and event.get("target")
                    and "hpAfter" in event
                ):
                    hp[0 if event["target"] == "a" else 1] = event["hpAfter"]
            page.locator(".duel-scrubber").evaluate(
                """(node, value) => {
                Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(node, String(value));
                node.dispatchEvent(new Event('input', {bubbles: true}));
                node.dispatchEvent(new Event('change', {bubbles: true}));
            }""",
                replay_time,
            )
            page.wait_for_function(
                """expected => Array.from(document.querySelectorAll('.duel-hp-track')).every(
                (node, index) => Number(node.getAttribute('aria-valuenow')) === expected[index])
            """,
                arg=hp,
            )
            page.wait_for_timeout(50)
            progress = page.locator(".duel-hud [role=progressbar]").evaluate_all("""tracks => tracks.map(track => {
                const fill = track.querySelector('i');
                const css = getComputedStyle(track);
                const contentWidth = parseFloat(css.width) - parseFloat(css.borderLeftWidth) - parseFloat(css.borderRightWidth);
                const ratio = Math.max(0, Math.min(1, Number(track.getAttribute('aria-valuenow')) / Number(track.getAttribute('aria-valuemax'))));
                const skew = css.transform === 'none' ? 0 : Math.abs(new DOMMatrixReadOnly(css.transform).c);
                return {actual: fill.getBoundingClientRect().width, expected: contentWidth * ratio + skew * fill.offsetHeight};
            })""")
            self.assertEqual(len(progress), 4)
            for bar in progress:
                self.assertAlmostEqual(bar["actual"], bar["expected"], delta=2)
            # The empty center of the HUD must stay opaque while replay frames change.
            with Image.open(BytesIO(page.locator(".duel-hud").screenshot())) as image:
                pixel = image.convert("RGB").getpixel(
                    (image.width // 2, image.height // 2)
                )
            self.assertEqual(pixel, (248, 249, 242))
        self.assertTrue(
            page.locator(".duel-hud").evaluate("""node => {
            for (let parent = node; parent; parent = parent.parentElement) {
                if (getComputedStyle(parent).backdropFilter !== 'none') return false;
            }
            return true;
        }""")
        )
        for pseudo in ["::before", "::after"]:
            self.assertEqual(
                page.locator(".app-shell").evaluate(
                    "(node, pseudo) => getComputedStyle(node, pseudo).animationName",
                    pseudo,
                ),
                "none",
            )
        screenshot_dir = os.environ.get("NFIGHT_TEST_SCREENSHOT_DIR")
        if screenshot_dir:
            page.locator(".ink-duel").screenshot(
                path=str(Path(screenshot_dir) / "mobile-battle-hud.png")
            )
        page.set_viewport_size({"width": 1920, "height": 1080})
        self.assertEqual(
            page.locator(".app-shell").evaluate(
                "node => getComputedStyle(node).backdropFilter"
            ),
            "blur(1.5px)",
        )
        self.assertEqual(
            page.locator(".duel-hud").evaluate(
                "node => getComputedStyle(node).backgroundColor"
            ),
            "rgba(248, 249, 242, 0.72)",
        )
        page.set_viewport_size({"width": 390, "height": 844})

    def test_phone_pages_and_desktop_character_layout(self):
        with tempfile.TemporaryDirectory(prefix="nfight-mobile-layout-") as directory:
            db_path = Path(directory) / "fighters.db"
            repo = FighterRepository(db_path)
            auth = WebAuthRepository(db_path)
            user_id, group_id = "10000081", "20000081"
            names = [
                "Mobile portrait",
                "LongNameWithoutSpaces012345678901",
                "手机长角色名" * 5,
                "Five star hero",
                "Six star hero",
            ]
            for index, name in enumerate(names):
                repo.create_fighter_for_user(user_id, name)
                with repo._connect() as connection:
                    connection.execute(
                        "UPDATE fighters SET star_rating = ?, hp = 99999, atk = 930, def = 150, spd = 120, crt = 50, eva = 45 WHERE name = ?",
                        ([3, 4, 4, 5, 6][index], name),
                    )
                    connection.execute(
                        "INSERT INTO fighter_scores (group_id, fighter_name, wins, battles, elo_rating) VALUES (?, ?, 4, 8, 1200)",
                        (group_id, name),
                    )
            avatar = db_path.parent / "avatars" / "mobile.img"
            avatar.parent.mkdir()
            Image.new("RGB", (180, 224), "#556f78").save(avatar, format="PNG")
            repo.set_fighter_avatar_path(user_id, names[0], str(avatar))
            repo.grant_points(user_id, 1000)
            repo._grant_item_direct(user_id, "star_exp_pill_s", 5)
            repo.open_group_boss(
                group_id,
                "手机测试首领" * 5,
                {"stats": {"hp": 10000}},
                {"stats": {"hp": 999999}},
                user_id,
            )
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            origin = f"http://127.0.0.1:{port}"
            env = {
                **os.environ,
                "NFIGHT_DB_PATH": str(db_path),
                "NFIGHT_PUBLIC_ORIGIN": origin,
                "NFIGHT_WEB_PORT": str(port),
            }
            with (Path(directory) / "server.log").open("w") as log:
                command = [str(ROOT / "web/.venv/bin/python"), "run_web.py"]
                if os.environ.get("NFIGHT_TEST_DIST_DIR"):
                    command = [
                        command[0],
                        "-c",
                        """import os
import uvicorn
from app import app
from starlette.staticfiles import StaticFiles
app.router.routes = [route for route in app.router.routes if route.name != 'frontend']
app.mount('/', StaticFiles(directory=os.environ['NFIGHT_TEST_DIST_DIR'], html=True), name='frontend')
uvicorn.run(app, host='127.0.0.1', port=int(os.environ['NFIGHT_WEB_PORT']), log_level='warning', access_log=False)
""",
                    ]
                server = subprocess.Popen(
                    command,
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
                        self.fail("Disposable layout server did not start")
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
                            context = browser.new_context(
                                viewport={"width": 390, "height": 844},
                                is_mobile=True,
                                has_touch=True,
                                device_scale_factor=3,
                                reduced_motion="reduce",
                            )
                            page = context.new_page()
                            errors = []
                            page.on(
                                "pageerror", lambda error: errors.append(str(error))
                            )
                            with page.expect_response(
                                "**/api/auth/challenge"
                            ) as response:
                                page.goto(origin)
                            challenge = response.value.json()
                            auth.confirm(
                                challenge["code"],
                                WebIdentity(user_id, group_id, "手机测试玩家"),
                            )
                            page.get_by_role(
                                "button", name="退出登录", exact=True
                            ).wait_for(timeout=10000)
                            for width in [320, 360, 390, 430, 700]:
                                page.set_viewport_size({"width": width, "height": 844})
                                for tab in [
                                    "总览",
                                    "人物",
                                    "江湖历练",
                                    "背包",
                                    "排行",
                                    "世界BOSS",
                                ]:
                                    with self.subTest(width=width, tab=tab):
                                        page.locator(".topbar nav").get_by_role(
                                            "button", name=tab, exact=True
                                        ).click()
                                        if tab == "江湖历练":
                                            page.locator(
                                                ".pve-roster button"
                                            ).first.wait_for()
                                            for index in range(3):
                                                page.locator(".pve-roster button").nth(
                                                    index
                                                ).click()
                                        self.assert_content_fits(page)
                                        if tab == "人物":
                                            self.assertEqual(
                                                page.locator(
                                                    ".fighters-view .fighter-card"
                                                ).count(),
                                                5,
                                            )
                                            self.assertTrue(
                                                page.locator(
                                                    ".fighters-view .hero-card"
                                                ).evaluate_all("""cards => cards.every(card =>
                                                card.querySelector('.portrait').getBoundingClientRect().bottom <=
                                                card.querySelector('.hero-meta').getBoundingClientRect().top + 1)
                                            """)
                                            )
                                            page.get_by_role(
                                                "button", name="替换栏位", exact=True
                                            ).click()
                                            self.assert_content_fits(page)
                                            page.get_by_role(
                                                "button", name="替换栏位", exact=True
                                            ).click()
                                            self.assertLess(
                                                page.locator(
                                                    ".main-panel"
                                                ).bounding_box()["y"],
                                                page.locator(
                                                    ".side-panel"
                                                ).bounding_box()["y"],
                                            )
                                            self.assertNotIn(
                                                "battle-page",
                                                page.locator(
                                                    ".app-shell"
                                                ).get_attribute("class"),
                                            )
                                            screenshot_dir = os.environ.get(
                                                "NFIGHT_TEST_SCREENSHOT_DIR"
                                            )
                                            if screenshot_dir and width in [320, 390]:
                                                Path(screenshot_dir).mkdir(
                                                    parents=True, exist_ok=True
                                                )
                                                page.screenshot(
                                                    path=str(
                                                        Path(screenshot_dir)
                                                        / f"mobile-{width}-fighters.png"
                                                    ),
                                                    full_page=True,
                                                    animations="disabled",
                                                )
                                        if tab == "背包":
                                            page.locator(".bag-item").get_by_role(
                                                "button", name="使用", exact=True
                                            ).click()
                                            page.get_by_role("dialog").wait_for()
                                            self.assert_content_fits(page)
                                            page.set_viewport_size(
                                                {"width": width, "height": 300}
                                            )
                                            self.assert_content_fits(page)
                                            self.assertLessEqual(
                                                page.get_by_role(
                                                    "dialog"
                                                ).bounding_box()["height"],
                                                276,
                                            )
                                            page.get_by_role("dialog").get_by_role(
                                                "button", name="取消", exact=True
                                            ).click()
                                            page.set_viewport_size(
                                                {"width": width, "height": 844}
                                            )
                                            page.locator(".shop-tabs").get_by_role(
                                                "button", name="商店", exact=True
                                            ).click()
                                            self.assert_content_fits(page)
                            page.set_viewport_size({"width": 844, "height": 390})
                            page.locator(".topbar nav").get_by_role(
                                "button", name="人物", exact=True
                            ).click()
                            self.assert_content_fits(page)
                            # Desktop keeps the original portrait beside the character metadata.
                            page.set_viewport_size({"width": 1920, "height": 1080})
                            page.wait_for_timeout(600)
                            card = page.locator(".fighters-view .hero-card").first
                            portrait = card.locator(".portrait").bounding_box()
                            metadata = card.locator(".hero-meta").bounding_box()
                            self.assertEqual(round(portrait["width"]), 168)
                            self.assertGreater(
                                metadata["x"], portrait["x"] + portrait["width"]
                            )
                            self.assertEqual(errors, [])
                            self.assertEqual(repo.get_user_points(user_id), 1000)
                            self.assertEqual(
                                repo.get_user_items(user_id)[0]["quantity"], 5
                            )
                            page.set_viewport_size({"width": 390, "height": 844})
                            page.locator(".topbar nav").get_by_role(
                                "button", name="江湖历练", exact=True
                            ).click()
                            page.locator(".pve-roster button").first.wait_for()
                            for index in range(3):
                                fighter_button = page.locator(".pve-roster button").nth(
                                    index
                                )
                                if "chosen" not in (
                                    fighter_button.get_attribute("class") or ""
                                ):
                                    fighter_button.click()
                            with page.expect_response(
                                "**/api/pve/stages/1-1/challenge"
                            ) as result:
                                page.locator(".pve-challenge").click()
                            battle_result = result.value.json()
                            self.assertTrue(battle_result["victory"])
                            page.locator(".duel-controls").get_by_role(
                                "button", name="暂停", exact=True
                            ).click()
                            self.assert_mobile_hud_rendering(
                                page, battle_result["duels"][0]
                            )
                            for width, height in [(320, 844), (390, 844), (844, 390)]:
                                page.set_viewport_size(
                                    {"width": width, "height": height}
                                )
                                self.assert_content_fits(page)
                            page.get_by_role(
                                "button", name="跳至结算", exact=True
                            ).click()
                            page.locator(".pve-summary").wait_for()
                            for width in [320, 390]:
                                page.set_viewport_size({"width": width, "height": 844})
                                self.assert_content_fits(page)
                            self.assertEqual(errors, [])
                            context.close()
                        finally:
                            browser.close()
                finally:
                    server.terminate()
                    server.wait(timeout=10)
