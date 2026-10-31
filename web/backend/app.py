from __future__ import annotations

import logging
import json
import os
import sqlite3
import secrets
import sys
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote, urlsplit

ROOT_DIR = Path(__file__).resolve().parents[2]
LOCAL_PACKAGES = ROOT_DIR / "web" / ".python-packages"
if LOCAL_PACKAGES.exists() and str(LOCAL_PACKAGES) not in sys.path:
    sys.path.insert(0, str(LOCAL_PACKAGES))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import (  # noqa: E402
    MAX_FIGHTERS_PER_USER,
    STAR_EXP_REQUIREMENTS,
    FighterRepository,
)
from engine import CombatEngine  # noqa: E402
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pve import PveService  # noqa: E402
from world_boss import WorldBossService, reward_preview  # noqa: E402
from world_boss_config import WORLD_BOSS_DAILY_LIMIT  # noqa: E402
from pydantic import BaseModel, Field
from text_resources import compact_battle_logs  # noqa: E402
from web_auth import (  # noqa: E402
    CHALLENGE_TTL,
    SESSION_TTL,
    AuthRateLimited,
    WebAuthRepository,
    WebIdentity,
)

PUBLIC_ORIGIN = os.environ.get("NFIGHT_PUBLIC_ORIGIN", "https://nfight.trpg.fun").rstrip("/")
COOKIE_SECURE = PUBLIC_ORIGIN.startswith("https://")
SESSION_COOKIE = "__Host-nfight-session" if COOKIE_SECURE else "nfight-session"
DEVICE_COOKIE = "__Host-nfight-device" if COOKIE_SECURE else "nfight-device"
logger = logging.getLogger("name_fight.web")

app = FastAPI(title="Name Fight Web", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[PUBLIC_ORIGIN] + ([] if COOKIE_SECURE else ["http://localhost:5173", "http://127.0.0.1:5173"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_setting = os.environ.get("NFIGHT_DB_PATH")
repo = FighterRepository(Path(db_setting) if db_setting else None)
auth = WebAuthRepository(repo.db_path)
engine = CombatEngine()
pve = PveService(repo, engine)


@app.middleware("http")
async def protect_api(request: Request, call_next):
    if request.url.path == "/motion-preview.html":
        identity = auth.get_identity(request.cookies.get(SESSION_COOKIE))
        if identity is None or not is_web_admin(identity):
            return JSONResponse({"detail": "仅管理员可使用特效拆解台"}, status_code=403)
    if (
        COOKIE_SECURE
        and request.url.scheme == "http"
        and request.url.netloc == urlsplit(PUBLIC_ORIGIN).netloc
    ):
        return RedirectResponse(str(request.url.replace(scheme="https")), status_code=307)
    if request.url.path.startswith("/api/"):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            allowed = {PUBLIC_ORIGIN} if COOKIE_SECURE else {PUBLIC_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"}
            if request.headers.get("origin") not in allowed:
                return JSONResponse({"detail": "Request origin rejected"}, status_code=403)
        try:
            response = await call_next(request)
        except sqlite3.OperationalError:
            logger.exception("Database operation failed")
            return JSONResponse({"detail": "存档暂时忙碌, 请稍后刷新"}, status_code=503, headers={"Cache-Control": "no-store"})
        response.headers["Cache-Control"] = "no-store"
        if response.status_code >= 400:
            logger.warning("API request failed: %s %s %s", request.method,
                           getattr(request.scope.get("route"), "path", "unmatched"), response.status_code)
        return response
    return await call_next(request)


def require_session(request: Request) -> WebIdentity:
    identity = auth.get_identity(request.cookies.get(SESSION_COOKIE))
    if identity is None:
        raise HTTPException(status_code=401, detail="请先在 QQ 群验证登录")
    return identity


def is_web_admin(identity: WebIdentity) -> bool:
    admins = {value.strip() for value in os.environ.get("NFIGHT_WEB_ADMIN_IDS", "").split(",") if value.strip()}
    return identity.user_id in admins


def require_web_admin(identity: WebIdentity = Depends(require_session)) -> WebIdentity:
    if not is_web_admin(identity):
        raise HTTPException(status_code=403, detail="仅管理员可使用演武堂")
    return identity


def _set_cookie(response: Response, name: str, value: str, maximum_age: int):
    response.set_cookie(name, value, max_age=maximum_age, secure=COOKIE_SECURE,
                        httponly=True, samesite="strict", path="/")


def _clear_cookie(response: Response, name: str):
    response.delete_cookie(name, path="/", secure=COOKIE_SECURE, httponly=True, samesite="strict")


@app.post("/api/auth/challenge")
def create_login_challenge(request: Request, response: Response):
    try:
        # The origin is loopback-only; cloudflared supplies the visitor address.
        visitor = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "unknown")
        auth.rate_limit("challenge", visitor, 5)
        device, code, expires_at = auth.create_challenge(request.cookies.get(DEVICE_COOKIE))
    except AuthRateLimited as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    _set_cookie(response, DEVICE_COOKIE, device, CHALLENGE_TTL)
    return {"code": code, "expiresAt": expires_at, "command": f"/nfweb {code}"}


@app.post("/api/auth/challenge/exchange")
def exchange_login_challenge(request: Request, response: Response):
    device = request.cookies.get(DEVICE_COOKIE)
    if not device:
        raise HTTPException(status_code=410, detail="验证码已失效, 请重新获取")
    try:
        auth.rate_limit("exchange", device, 40)
        token = auth.exchange(device, request.cookies.get(SESSION_COOKIE))
    except AuthRateLimited as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    if token is None:
        return {"status": "pending"}
    _set_cookie(response, SESSION_COOKIE, token, SESSION_TTL)
    _clear_cookie(response, DEVICE_COOKIE)
    logger.info("Browser login succeeded")
    return {"status": "authenticated"}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    auth.logout(request.cookies.get(SESSION_COOKIE), request.cookies.get(DEVICE_COOKIE))
    _clear_cookie(response, SESSION_COOKIE)
    _clear_cookie(response, DEVICE_COOKIE)
    return {"status": "logged_out"}


@app.get("/api/health")
def health():
    with repo._connect() as connection:
        connection.execute("SELECT 1 FROM fighters LIMIT 1").fetchone()
    return {"status": "ok"}


class CreateFighterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    replaceSlot: int | None = None


class ActiveFighterRequest(BaseModel):
    name: str


class BuyItemRequest(BaseModel):
    itemId: str
    quantity: int = 1


class UseItemRequest(BaseModel):
    itemId: str


class FeedRequest(BaseModel):
    itemId: str
    quantity: int = 1


class RerollRequest(BaseModel):
    category: str = "martial_art"
    itemId: str = "martial_token_basic"


class ChoiceRequest(BaseModel):
    category: str = "martial_art"
    choiceId: str


class SummonPreviewRequest(BaseModel):
    name: str = Field(min_length=1, max_length=32)


class SummonConfirmRequest(BaseModel):
    replaceSlot: int | None = None


class DuelRequest(BaseModel):
    attackerName: str | None = None
    defenderName: str | None = None


class WorldBossRequest(BaseModel):
    bossId: int = Field(gt=0)
    requestId: str = Field(min_length=8, max_length=96, pattern=r"^[A-Za-z0-9_-]+$")
    slots: list[int] | None = Field(default=None, min_length=3, max_length=3)
    practice: bool = False
    phase: Literal["full", "phase1", "phase2"] = "full"


class ShowcaseRequest(BaseModel):
    swap: bool = False


class PracticeStats(BaseModel):
    hp: int = Field(ge=1, le=1000000)
    atk: int = Field(ge=0, le=100000)
    def_: int = Field(alias="def", ge=0, le=100000)
    spd: float = Field(ge=1, le=100000)
    crt: float = Field(ge=0, le=100)
    eva: float = Field(ge=0, le=100)


class PracticeFighter(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    stats: PracticeStats
    martialArtId: str
    neigongId: str
    qinggongId: str


class PracticeBattle(BaseModel):
    attacker: PracticeFighter
    defender: PracticeFighter


class PveTeamRequest(BaseModel):
    slots: list[int]


class PveChallengeRequest(BaseModel):
    tacticId: str | None = None


class PveSwitchRequest(BaseModel):
    decisionCount: int
    fighterIndex: int


def _avatar_file(fighter: dict[str, Any]) -> Path | None:
    stored = fighter.get("avatar_path")
    if not stored:
        return None
    avatar_dir = (repo.db_path.parent / "avatars").resolve()
    path = Path(str(stored)).resolve()
    if not path.is_relative_to(avatar_dir) or not path.is_file():
        # Relocate only the Bot-generated filename from an old installation path.
        digest = sha256(str(fighter["name"]).strip().casefold().encode("utf-8")).hexdigest()[:24]
        filename = f"{digest}.img"
        if Path(str(stored)).name != filename:
            return None
        path = (avatar_dir / filename).resolve()
    return path if path.is_relative_to(avatar_dir) and path.is_file() else None


def _fighter_payload(fighter: dict[str, Any] | None) -> dict[str, Any] | None:
    if fighter is None:
        return None
    avatar = _avatar_file(fighter)
    try:
        avatar_version = avatar.stat().st_mtime_ns if avatar else None
    except OSError:
        avatar_version = None
    avatar_url = (
        f"/api/fighters/{quote(fighter['name'], safe='')}/avatar?v={avatar_version}"
        if avatar_version is not None else None
    )
    return {
        "name": fighter["name"],
        "slotIndex": fighter.get("slot_index"),
        "isActive": bool(fighter.get("is_active")),
        "starRating": float(fighter.get("star_rating", 3.0)),
        "baseStarRating": float(fighter.get("base_star_rating", fighter.get("star_rating", 3.0))),
        "starExp": int(fighter.get("star_exp", 0) or 0),
        "breakthroughStage": int(fighter.get("breakthrough_stage", 0) or 0),
        "nextStarExp": STAR_EXP_REQUIREMENTS.get(float(fighter.get("star_rating", 3.0))),
        "wins": int(fighter.get("wins", 0) or 0),
        "battles": int(fighter.get("battles", 0) or 0),
        "stats": dict(fighter["stats"]),
        "martialArt": _entry_payload(fighter["martial_art"]),
        "neigong": _entry_payload(fighter["neigong"]),
        "qinggong": _entry_payload(fighter["qinggong"]),
        "avatarPath": avatar_url,
        "cardUrl": f"/api/fighters/{quote(fighter['name'], safe='')}/card",
    }


def _entry_payload(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry.get("id"),
        "name": entry.get("name"),
        "type": entry.get("type"),
        "description": entry.get("description", ""),
        "combat_summary": entry.get("combat_summary", ""),
        "stat_modifiers": entry.get("stat_modifiers", {}),
        "hp_multiplier": entry.get("hp_multiplier"),
        "def_multiplier": entry.get("def_multiplier"),
        "spd_multiplier": entry.get("spd_multiplier"),
        "eva_bonus": entry.get("eva_bonus"),
        "moves": [{"name": move.get("name", "")} for move in entry.get("moves", [])],
    }


def _state_payload(identity: WebIdentity) -> dict[str, Any]:
    fighters = repo.get_user_fighters(identity.user_id)
    active = repo.get_active_fighter(identity.user_id)
    active_name = active["name"] if active else None
    pve_state = pve.get_state(identity.user_id)
    return {
        "session": {
            "userId": identity.user_id,
            "groupId": identity.group_id,
            "maxFighters": MAX_FIGHTERS_PER_USER,
            "displayName": identity.display_name,
            "isAdmin": is_web_admin(identity),
        },
        "fighters": [_fighter_payload(fighter) for fighter in fighters],
        "activeFighter": _fighter_payload(active),
        "wallet": repo.get_user_wallet(identity.user_id),
        "items": repo.get_user_items(identity.user_id),
        "pendingChoice": repo.get_web_loadout_choice(identity.user_id),
        "pendingSummon": _fighter_payload(repo.get_web_summon_preview(identity.user_id)),
        "shop": repo.get_shop_items(),
        "leaderboard": repo.get_group_leaderboard(identity.group_id, limit=10),
        "worldBoss": _world_boss_payload(identity),
        "pveSummary": {
            "profile": pve_state["profile"],
            "nextStageId": pve_state["nextStageId"],
            "hasRequiredRoster": pve_state["hasRequiredRoster"],
            "chapterStars": {chapter["id"]: chapter["stars"] for chapter in pve_state["chapters"]},
        },
        "needsFirstFighter": active_name is None,
    }


def _world_boss_payload(identity: WebIdentity) -> dict[str, Any]:
    activity = repo.get_active_group_boss(
        identity.group_id
    ) or repo.get_latest_group_boss(identity.group_id)
    manifest = json.loads(
        (ROOT_DIR / "web_animation" / "boss_assets" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assets = {
        key: {**value, "portrait": f"/boss-assets/{value['portrait']}"}
        for key, value in manifest.items()
        if isinstance(value, dict)
    }
    base = {
        "activity": activity,
        "rank": [],
        "remainingAttempts": None,
        "dailyLimit": WORLD_BOSS_DAILY_LIMIT,
        "teamSlots": repo.get_user_team3_order(identity.user_id),
        "assets": assets,
        "rewardPreview": reward_preview(),
    }
    if activity is None:
        return base
    used = repo.get_group_boss_attempt_usage(
        activity["boss_id"],
        identity.group_id,
        identity.user_id,
        date.today().isoformat(),
    )
    base.update(
        rank=repo.get_group_boss_rank(identity.group_id, activity["boss_id"], limit=10),
        remainingAttempts=max(0, WORLD_BOSS_DAILY_LIMIT - used),
    )
    return base


def _public_boss_replay(result, identity):
    if result is None:
        return None
    payload = {
        key: value
        for key, value in result.items()
        if key not in ("duels", "settlement")
    }
    payload["duels"] = [
        {
            key: value
            for key, value in duel.items()
            if key not in ("fighter_a", "fighter_b", "result")
        }
        for duel in result["duels"]
    ]
    settlement = result.get("settlement")
    if settlement:
        payload["settlement"] = {
            "settlement_type": settlement["settlement_type"],
            "rewards": [
                entry
                for category in ("participant_rewards", "rank_rewards")
                for entry in settlement[category]
                if entry["user_id"] == identity.user_id
            ],
        }
    return payload


def _api_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@app.get("/api/session/bootstrap")
def bootstrap(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    return _state_payload(identity)


@app.get("/api/fighters")
def list_fighters(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    return {"fighters": [_fighter_payload(fighter) for fighter in repo.get_user_fighters(identity.user_id)]}


@app.post("/api/fighters")
def create_fighter(payload: CreateFighterRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="角色名不能为空")
    try:
        if payload.replaceSlot is not None:
            old_name, fighter = repo.replace_fighter_for_user(identity.user_id, payload.replaceSlot, fighter_name=name)
            return {"fighter": _fighter_payload(fighter), "replaced": old_name, "state": _state_payload(identity)}
        fighter = repo.create_fighter_for_user(identity.user_id, name)
        return {"fighter": _fighter_payload(fighter), "state": _state_payload(identity)}
    except ValueError as exc:
        status = 409 if "最多" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc))


@app.post("/api/fighters/active")
def set_active_fighter(payload: ActiveFighterRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        fighter = repo.set_active_fighter(identity.user_id, payload.name)
        return {"fighter": _fighter_payload(fighter), "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.get("/api/fighters/{name}/card")
def fighter_card(name: str, identity: WebIdentity = Depends(require_session)):
    fighter = repo.get_user_fighter_by_name(identity.user_id, name)
    if fighter is None:
        raise HTTPException(status_code=404, detail="未找到角色")
    try:
        from render_profile import render_star_card
    except ModuleNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Pillow is required to render fighter cards") from exc
    avatar = _avatar_file(fighter)
    fighter = dict(fighter)
    fighter["avatar_path"] = str(avatar) if avatar else None
    card_path = render_star_card(fighter, str(ROOT_DIR / "data"))
    if not card_path:
        raise HTTPException(status_code=404, detail="该角色尚未达到五星卡面")
    return FileResponse(card_path, media_type="image/jpeg")


@app.post("/api/signin")
def signin(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        result = repo.claim_daily_signin(identity.user_id, date.today().isoformat())
        return {"result": result, "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.get("/api/wallet")
def wallet(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    return {"wallet": repo.get_user_wallet(identity.user_id)}


@app.get("/api/items")
def items(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    return {"items": repo.get_user_items(identity.user_id)}


@app.get("/api/shop")
def shop(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    return {"shop": repo.get_shop_items()}


@app.post("/api/shop/buy")
def buy_item(payload: BuyItemRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        result = repo.buy_item(identity.user_id, payload.itemId, payload.quantity)
        return {"result": result, "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/summon/preview")
def create_summon_preview(payload: SummonPreviewRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        fighter = repo.create_web_summon_preview(identity.user_id, payload.name)
        return {"fighter": _fighter_payload(fighter), "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/summon/confirm")
def confirm_summon(payload: SummonConfirmRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        replaced, fighter = repo.commit_web_summon_preview(identity.user_id, payload.replaceSlot)
        return {"fighter": _fighter_payload(fighter), "replaced": replaced, "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/items/use")
def use_item(payload: UseItemRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        result = repo.use_pve_energy_item(
            identity.user_id,
            payload.itemId,
            maximum_energy=pve.maximum_energy,
            recovery_seconds=pve.recovery_seconds,
        )
        return {"result": result, "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/feed")
def feed_fighter(name: str, payload: FeedRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        result = repo.feed_fighter_star_exp(identity.user_id, name, payload.itemId, payload.quantity)
        return {"result": result, "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/breakthrough")
def breakthrough_fighter(name: str, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        result = repo.breakthrough_fighter(identity.user_id, name)
        return {"result": result, "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/reroll")
def reroll_fighter(name: str, payload: RerollRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        if payload.itemId == "martial_token_basic" and payload.category != "martial_art":
            raise ValueError("洗髓符只能更换武功")
        if payload.itemId == "martial_token_type" and payload.category not in ("neigong", "qinggong"):
            raise ValueError("换宗令只能更换内功或轻功")
        result = repo.reroll_loadout_random(identity.user_id, name, payload.category, payload.itemId)
        return {"result": result, "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/choices")
def create_choice_options(name: str, payload: RerollRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        if payload.itemId != "martial_token_choice":
            raise ValueError("该道具不能生成天机候选")
        result = repo.create_web_loadout_choice(identity.user_id, name, payload.category)
        return {"result": result, "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/choices/apply")
def apply_choice(name: str, payload: ChoiceRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        result = repo.apply_web_loadout_choice(identity.user_id, name, payload.category, payload.choiceId)
        return {"result": result, "state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/choices/abandon")
def abandon_choice(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        repo.abandon_web_loadout_choice(identity.user_id)
        return {"state": _state_payload(identity)}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/battles/duel")
def duel(payload: DuelRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    attacker = repo.get_user_fighter_by_name(identity.user_id, payload.attackerName) if payload.attackerName else repo.get_active_fighter(identity.user_id)
    if attacker is None:
        raise HTTPException(status_code=400, detail="请先创建并选择出战角色")
    if payload.defenderName:
        defender = repo.get_fighter_by_name(payload.defenderName)
    else:
        defender = repo.generate_preview_fighter(f"试炼影身-{attacker['name']}")
    if defender is None:
        raise HTTPException(status_code=404, detail="未找到对手")
    result = engine.battle_with_events(attacker, defender)
    return {
        "attacker": _fighter_payload(attacker),
        "defender": _fighter_payload(defender),
        "winner": result["winner"],
        "state": result["state"],
        "events": result["events"],
        "logs": result["logs"],
        "displayLogs": compact_battle_logs(result["logs"]),
        "rating": None,
        "snapshot": _state_payload(identity),
    }


SHOWCASE_LOADOUTS = {
    "ink": ("sword_xuanmo", "taiji_xuanmo_gong", "taxue_wuhen", "玄墨·无名"),
    "crimson": ("blade_chixiao", "chixiao_shaxin_jue", "zongyun_ti", "赤霄·断魂"),
}


def _showcase_fighter(key: str) -> dict[str, Any]:
    art_id, inner_id, light_id, name = SHOWCASE_LOADOUTS[key]
    fighter = repo._build_generated_fighter(f"演武-{name}", forced_base_star=4.0)
    fighter["name"] = name
    fighter["martial_art"] = next(item for item in repo.martial_arts if item["id"] == art_id)
    fighter["neigong"] = next(item for item in repo.neigong if item["id"] == inner_id)
    fighter["qinggong"] = next(item for item in repo.qinggong if item["id"] == light_id)
    fighter["martial_art_id"], fighter["neigong_id"], fighter["qinggong_id"] = art_id, inner_id, light_id
    fighter["stats"] = repo._recalculate_final_stats(
        dict(fighter["raw_stats"]), 4.0, 0, fighter["martial_art"], fighter["neigong"], fighter["qinggong"],
    )
    return fighter


@app.post("/api/battles/showcase")
def showcase_duel(payload: ShowcaseRequest | None = None, identity: WebIdentity = Depends(require_web_admin)) -> dict[str, Any]:
    """Read-only demo duel between the two new loadouts; never touches player data."""
    attacker, defender = _showcase_fighter("ink"), _showcase_fighter("crimson")
    if payload and payload.swap:
        attacker, defender = defender, attacker
    result = engine.battle_with_events(attacker, defender)
    return {
        "attacker": _fighter_payload(attacker),
        "defender": _fighter_payload(defender),
        "winner": result["winner"],
        "state": result["state"],
        "events": result["events"],
        "logs": result["logs"],
        "displayLogs": compact_battle_logs(result["logs"]),
        "rating": None,
    }


@app.get("/api/admin/practice/config")
def practice_config(identity: WebIdentity = Depends(require_web_admin)) -> dict[str, Any]:
    return {
        "martialArts": [_entry_payload(item) for item in repo.martial_arts],
        "neigong": [{**_entry_payload(item), "passives": item.get("passives", [])} for item in repo.neigong],
        "qinggong": [{**_entry_payload(item), "special_effect_data": item.get("special_effect_data")} for item in repo.qinggong],
    }


@app.post("/api/admin/practice/random")
def practice_random(identity: WebIdentity = Depends(require_web_admin)) -> dict[str, Any]:
    fighter = repo._build_generated_fighter("Practice-" + secrets.token_hex(8))
    return _fighter_payload(fighter)


def _practice_fighter(value: PracticeFighter) -> dict[str, Any]:
    fighter = repo._build_generated_fighter(value.name)
    for key, entry_id, entries in (
        ("martial_art", value.martialArtId, repo.martial_arts),
        ("neigong", value.neigongId, repo.neigong),
        ("qinggong", value.qinggongId, repo.qinggong),
    ):
        entry = next((item for item in entries if item["id"] == entry_id), None)
        if entry is None:
            raise HTTPException(status_code=422, detail=f"Unknown {key}: {entry_id}")
        fighter[key] = entry
        fighter[key + "_id"] = entry_id
    fighter["stats"] = value.stats.model_dump(by_alias=True)
    return fighter


@app.post("/api/admin/practice/battle")
def practice_battle(payload: PracticeBattle, identity: WebIdentity = Depends(require_web_admin)) -> dict[str, Any]:
    attacker = _practice_fighter(payload.attacker)
    defender = _practice_fighter(payload.defender)
    if attacker["name"] == defender["name"]:
        raise HTTPException(status_code=422, detail="双方角色名不能相同")
    result = engine.battle_with_events(attacker, defender)
    return {
        "attacker": _fighter_payload(attacker), "defender": _fighter_payload(defender),
        "winner": result["winner"], "state": result["state"], "events": result["events"],
        "logs": result["logs"], "displayLogs": compact_battle_logs(result["logs"]), "rating": None,
    }


@app.get("/api/pve")
def pve_state(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    return pve.get_state(identity.user_id)


@app.post("/api/pve/team")
def set_pve_team(payload: PveTeamRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        return pve.set_team(identity.user_id, payload.slots)
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/pve/stages/{stage_id}/challenge")
def challenge_pve_stage(stage_id: str, payload: PveChallengeRequest | None = None, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        return pve.start_interactive(identity.user_id, stage_id, payload.tacticId if payload else None)
    except ValueError as exc:
        raise _api_error(exc)


@app.get("/api/pve/attempt")
def get_pve_attempt(identity: WebIdentity = Depends(require_session)) -> dict[str, Any] | None:
    return pve.get_interactive(identity.user_id)


@app.post("/api/pve/attempts/{attempt_id}/switch")
def switch_pve_fighter(attempt_id: str, payload: PveSwitchRequest, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        return pve.continue_interactive(identity.user_id, attempt_id, payload.decisionCount, payload.fighterIndex)
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/pve/attempts/{attempt_id}/abandon")
def abandon_pve_attempt(attempt_id: str, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        return pve.abandon_interactive(identity.user_id, attempt_id)
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/pve/chapters/{chapter_id}/rewards/{threshold}/claim")
def claim_pve_chapter_reward(chapter_id: str, threshold: int, identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    try:
        return pve.claim_chapter_reward(identity.user_id, chapter_id, threshold)
    except ValueError as exc:
        raise _api_error(exc)


@app.get("/api/leaderboards/duel")
def duel_leaderboard(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    return {"leaderboard": repo.get_group_leaderboard(identity.group_id, limit=20)}


@app.get("/api/world-boss")
def world_boss(identity: WebIdentity = Depends(require_session)) -> dict[str, Any]:
    return _world_boss_payload(identity)


@app.post("/api/world-boss/challenge")
def challenge_world_boss(
    payload: WorldBossRequest, identity: WebIdentity = Depends(require_session)
) -> dict[str, Any]:
    try:
        result = WorldBossService(repo).challenge(
            identity.group_id,
            identity.user_id,
            identity.display_name,
            payload.requestId,
            payload.bossId,
            slots=payload.slots,
            practice=payload.practice,
            phase=payload.phase,
        )
        return _public_boss_replay(result, identity)
    except ValueError as exc:
        raise _api_error(exc)


@app.get("/api/world-boss/replay")
def latest_world_boss_replay(
    identity: WebIdentity = Depends(require_session),
) -> dict[str, Any] | None:
    return _public_boss_replay(
        WorldBossService(repo).latest(identity.group_id, identity.user_id), identity
    )


@app.get("/api/fighters/{name}/avatar")
def fighter_avatar(name: str, identity: WebIdentity = Depends(require_session)):
    fighter = repo.get_user_fighter_by_name(identity.user_id, name)
    path = _avatar_file(fighter) if fighter else None
    if path is None:
        raise HTTPException(status_code=404, detail="未找到角色头像")
    try:
        with Image.open(path) as image:
            media_type = Image.MIME.get(image.format, "application/octet-stream")
    except OSError as exc:
        raise HTTPException(status_code=404, detail="未找到角色头像") from exc
    return FileResponse(path, media_type=media_type)


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def unknown_api(path: str):
    raise HTTPException(status_code=404, detail="Unknown API endpoint")


DIST_DIR = ROOT_DIR / "web" / "frontend" / "dist"
app.mount("/boss-assets", StaticFiles(directory=ROOT_DIR / "web_animation" / "boss_assets"), name="boss-assets")

if DIST_DIR.is_dir():
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="frontend")
