"""Track QQ battle-image acknowledgements without retrying uncertain sends."""

import logging
from enum import Enum

from aiocqhttp.exceptions import ActionFailed

QQ_GIF_TIMEOUT_MS = 120_000
BATTLE_SEND_TIMEOUT_SECONDS = 135
logger = logging.getLogger(__name__)


class BattleDeliveryState(Enum):
    CONFIRMED = "confirmed"
    FAILED = "failed"
    UNKNOWN = "unknown"


def delivery_error_state(error: Exception) -> BattleDeliveryState:
    if isinstance(error, ActionFailed):
        result = error.result
        detail = " ".join(str(result.get(key, "")) for key in ("message", "wording"))
        if any(
            word in detail.lower()
            for word in ("timeout", "timed out", "network", "disconnect")
        ):
            return BattleDeliveryState.UNKNOWN
        return BattleDeliveryState.FAILED
    # A lost reply cannot establish whether QQ accepted the submitted request.
    return BattleDeliveryState.UNKNOWN


async def send_qq_battle_image(
    bot, *, group_id: str, user_id: str, image_base64: str
) -> BattleDeliveryState:
    recipient = group_id or user_id
    if not recipient or not recipient.isascii() or not recipient.isdigit():
        raise ValueError("A numeric QQ recipient is required")
    action = "send_group_msg" if group_id else "send_private_msg"
    recipient_key = "group_id" if group_id else "user_id"
    payload = {
        recipient_key: int(recipient),
        "message": [{"type": "image", "data": {"file": "base64://" + image_base64}}],
        "timeout": QQ_GIF_TIMEOUT_MS,
    }
    try:
        response = await bot.call_action(action, **payload)
    except Exception as error:
        logger.exception("QQ battle image action failed")
        return delivery_error_state(error)
    message_id = response.get("message_id") if isinstance(response, dict) else None
    if (
        isinstance(message_id, (int, str))
        and not isinstance(message_id, bool)
        and str(message_id).lstrip("-").isdigit()
        and int(message_id) != 0
    ):
        return BattleDeliveryState.CONFIRMED
    return BattleDeliveryState.UNKNOWN
