from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
LOCAL_PACKAGES = ROOT_DIR / "web" / ".python-packages"
if LOCAL_PACKAGES.exists() and str(LOCAL_PACKAGES) not in sys.path:
    sys.path.insert(0, str(LOCAL_PACKAGES))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from database import MAX_FIGHTERS_PER_USER, FighterRepository  # noqa: E402
from engine import CombatEngine  # noqa: E402
from text_resources import compact_battle_logs  # noqa: E402

DEFAULT_USER_ID = "web-local-user"
DEFAULT_GROUP_ID = "web-local-group"

app = FastAPI(title="Name Fight Web", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repo = FighterRepository()
engine = CombatEngine()


class CreateFighterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    replaceSlot: int | None = None


class ActiveFighterRequest(BaseModel):
    name: str


class BuyItemRequest(BaseModel):
    itemId: str
    quantity: int = 1


class FeedRequest(BaseModel):
    itemId: str
    quantity: int = 1


class RerollRequest(BaseModel):
    category: str = "martial_art"
    itemId: str = "martial_token_basic"


class ChoiceRequest(BaseModel):
    category: str = "martial_art"
    choiceId: str


class DuelRequest(BaseModel):
    attackerName: str | None = None
    defenderName: str | None = None


def _fighter_payload(fighter: dict[str, Any] | None) -> dict[str, Any] | None:
    if fighter is None:
        return None
    return {
        "name": fighter["name"],
        "slotIndex": fighter.get("slot_index"),
        "isActive": bool(fighter.get("is_active")),
        "starRating": float(fighter.get("star_rating", 3.0)),
        "baseStarRating": float(fighter.get("base_star_rating", fighter.get("star_rating", 3.0))),
        "starExp": int(fighter.get("star_exp", 0) or 0),
        "breakthroughStage": int(fighter.get("breakthrough_stage", 0) or 0),
        "wins": int(fighter.get("wins", 0) or 0),
        "battles": int(fighter.get("battles", 0) or 0),
        "stats": dict(fighter["stats"]),
        "martialArt": _entry_payload(fighter["martial_art"]),
        "neigong": _entry_payload(fighter["neigong"]),
        "qinggong": _entry_payload(fighter["qinggong"]),
        "avatarPath": fighter.get("avatar_path"),
        "cardUrl": f"/api/fighters/{fighter['name']}/card",
    }


def _entry_payload(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry.get("id"),
        "name": entry.get("name"),
        "type": entry.get("type"),
        "description": entry.get("description", ""),
    }


def _state_payload() -> dict[str, Any]:
    fighters = repo.get_user_fighters(DEFAULT_USER_ID)
    active = repo.get_active_fighter(DEFAULT_USER_ID)
    active_name = active["name"] if active else None
    return {
        "session": {
            "userId": DEFAULT_USER_ID,
            "groupId": DEFAULT_GROUP_ID,
            "maxFighters": MAX_FIGHTERS_PER_USER,
        },
        "fighters": [_fighter_payload(fighter) for fighter in fighters],
        "activeFighter": _fighter_payload(active),
        "wallet": repo.get_user_wallet(DEFAULT_USER_ID),
        "items": repo.get_user_items(DEFAULT_USER_ID),
        "shop": repo.get_shop_items(),
        "leaderboard": repo.get_group_leaderboard(DEFAULT_GROUP_ID, limit=10),
        "worldBoss": _world_boss_payload(),
        "needsFirstFighter": active_name is None,
    }


def _world_boss_payload() -> dict[str, Any]:
    activity = repo.get_active_group_boss(DEFAULT_GROUP_ID) or repo.get_latest_group_boss(DEFAULT_GROUP_ID)
    if activity is None:
        return {"activity": None, "rank": [], "remainingAttempts": None, "dailyLimit": 3}
    used = repo.get_group_boss_attempt_usage(
        activity["boss_id"],
        DEFAULT_GROUP_ID,
        DEFAULT_USER_ID,
        date.today().isoformat(),
    )
    return {
        "activity": activity,
        "rank": repo.get_group_boss_rank(DEFAULT_GROUP_ID, activity["boss_id"], limit=10),
        "remainingAttempts": max(0, 3 - used),
        "dailyLimit": 3,
    }


def _api_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@app.get("/api/session/bootstrap")
def bootstrap() -> dict[str, Any]:
    return _state_payload()


@app.get("/api/fighters")
def list_fighters() -> dict[str, Any]:
    return {"fighters": [_fighter_payload(fighter) for fighter in repo.get_user_fighters(DEFAULT_USER_ID)]}


@app.post("/api/fighters")
def create_fighter(payload: CreateFighterRequest) -> dict[str, Any]:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="角色名不能为空")
    try:
        if payload.replaceSlot is not None:
            old_name, fighter = repo.replace_fighter_for_user(DEFAULT_USER_ID, payload.replaceSlot, fighter_name=name)
            return {"fighter": _fighter_payload(fighter), "replaced": old_name, "state": _state_payload()}
        fighter = repo.create_fighter_for_user(DEFAULT_USER_ID, name)
        return {"fighter": _fighter_payload(fighter), "state": _state_payload()}
    except ValueError as exc:
        status = 409 if "最多" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc))


@app.post("/api/fighters/active")
def set_active_fighter(payload: ActiveFighterRequest) -> dict[str, Any]:
    try:
        fighter = repo.set_active_fighter(DEFAULT_USER_ID, payload.name)
        return {"fighter": _fighter_payload(fighter), "state": _state_payload()}
    except ValueError as exc:
        raise _api_error(exc)


@app.get("/api/fighters/{name}/card")
def fighter_card(name: str):
    fighter = repo.get_fighter_by_name(name)
    if fighter is None:
        raise HTTPException(status_code=404, detail="未找到角色")
    try:
        from render_profile import render_star_card
    except ModuleNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Pillow is required to render fighter cards") from exc
    card_path = render_star_card(fighter, str(ROOT_DIR / "data"))
    if not card_path:
        raise HTTPException(status_code=404, detail="该角色尚未达到五星卡面")
    return FileResponse(card_path, media_type="image/jpeg")


@app.post("/api/signin")
def signin() -> dict[str, Any]:
    try:
        result = repo.claim_daily_signin(DEFAULT_USER_ID, date.today().isoformat())
        return {"result": result, "state": _state_payload()}
    except ValueError as exc:
        raise _api_error(exc)


@app.get("/api/wallet")
def wallet() -> dict[str, Any]:
    return {"wallet": repo.get_user_wallet(DEFAULT_USER_ID)}


@app.get("/api/items")
def items() -> dict[str, Any]:
    return {"items": repo.get_user_items(DEFAULT_USER_ID)}


@app.get("/api/shop")
def shop() -> dict[str, Any]:
    return {"shop": repo.get_shop_items()}


@app.post("/api/shop/buy")
def buy_item(payload: BuyItemRequest) -> dict[str, Any]:
    try:
        result = repo.buy_item(DEFAULT_USER_ID, payload.itemId, payload.quantity)
        return {"result": result, "state": _state_payload()}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/feed")
def feed_fighter(name: str, payload: FeedRequest) -> dict[str, Any]:
    try:
        result = repo.feed_fighter_star_exp(DEFAULT_USER_ID, name, payload.itemId, payload.quantity)
        return {"result": result, "state": _state_payload()}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/breakthrough")
def breakthrough_fighter(name: str) -> dict[str, Any]:
    try:
        result = repo.breakthrough_fighter(DEFAULT_USER_ID, name)
        return {"result": result, "state": _state_payload()}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/reroll")
def reroll_fighter(name: str, payload: RerollRequest) -> dict[str, Any]:
    try:
        result = repo.reroll_loadout_random(DEFAULT_USER_ID, name, payload.category, payload.itemId)
        return {"result": result, "state": _state_payload()}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/choices")
def create_choice_options(name: str, payload: RerollRequest) -> dict[str, Any]:
    try:
        result = repo.create_loadout_choice_options(DEFAULT_USER_ID, name, payload.category)
        return {"result": result, "state": _state_payload()}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/fighters/{name}/choices/apply")
def apply_choice(name: str, payload: ChoiceRequest) -> dict[str, Any]:
    try:
        result = repo.apply_loadout_choice(DEFAULT_USER_ID, name, payload.category, payload.choiceId)
        return {"result": result, "state": _state_payload()}
    except ValueError as exc:
        raise _api_error(exc)


@app.post("/api/battles/duel")
def duel(payload: DuelRequest) -> dict[str, Any]:
    attacker = repo.get_user_fighter_by_name(DEFAULT_USER_ID, payload.attackerName) if payload.attackerName else repo.get_active_fighter(DEFAULT_USER_ID)
    if attacker is None:
        raise HTTPException(status_code=400, detail="请先创建并选择出战角色")
    if payload.defenderName:
        defender = repo.get_fighter_by_name(payload.defenderName)
    else:
        defender = repo.generate_preview_fighter(f"试炼影身-{attacker['name']}")
    if defender is None:
        raise HTTPException(status_code=404, detail="未找到对手")
    result = engine.battle_with_events(attacker, defender)
    rating = repo.record_group_battle(DEFAULT_GROUP_ID, attacker["name"], defender["name"], result["winner"], elo_scale=0.4)
    return {
        "attacker": _fighter_payload(attacker),
        "defender": _fighter_payload(defender),
        "winner": result["winner"],
        "state": result["state"],
        "events": result["events"],
        "logs": result["logs"],
        "displayLogs": compact_battle_logs(result["logs"]),
        "rating": rating,
        "snapshot": _state_payload(),
    }


@app.get("/api/leaderboards/duel")
def duel_leaderboard() -> dict[str, Any]:
    return {"leaderboard": repo.get_group_leaderboard(DEFAULT_GROUP_ID, limit=20)}


@app.get("/api/world-boss")
def world_boss() -> dict[str, Any]:
    return _world_boss_payload()
