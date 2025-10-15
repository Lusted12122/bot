# bot/utils/check_sub.py
from aiogram import Bot
from bot.config import CHANNEL_USERNAME

async def check_subscription(bot: Bot, user_id: int) -> bool:
    """Return True if user_id is subscribed to CHANNEL_USERNAME."""
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False
