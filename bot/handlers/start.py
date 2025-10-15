# bot/handlers/start.py
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from bot.config import CHANNEL_USERNAME
from bot.utils.check_sub import check_subscription
from bot.handlers.menu import get_profile_text, get_profile_keyboard
from bot.utils.database import add_user

def get_main_menu_keyboard():
    """Creates the main menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Щоденний бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton(text="👤 Профіль", callback_data="profile"),
         InlineKeyboardButton(text="🎮 Ігри", callback_data="games")],
        [InlineKeyboardButton(text="📢 Канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
         InlineKeyboardButton(text="💡 Підказки", callback_data="hints")]
    ])

async def start_handler(message: Message):
    """Handles the /start command by showing the profile directly."""
    bot = message.bot
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Check for referrer
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    # Add user to the database
    add_user(user_id, user_name, referrer_id)

    if await check_subscription(bot, user_id):
        profile_text = await get_profile_text(bot, user_id, user_name)
        await message.answer(profile_text, reply_markup=get_profile_keyboard(), parse_mode="Markdown")
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Підписатися", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton(text="✅ Я підписався", callback_data="check_sub")]
        ])
        await message.answer(
            f"👋 Привіт, {user_name}!\n\n"
            f"Для використання бота необхідно підписатися на наш канал.\n"
            f"Після підписки натисни кнопку нижче 👇",
            reply_markup=keyboard
        )

async def check_sub_callback(callback: CallbackQuery):
    """Handles the subscription check and shows the profile."""
    bot = callback.bot
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name

    if await check_subscription(bot, user_id):
        profile_text = await get_profile_text(bot, user_id, user_name)
        await callback.message.edit_text(
            f"✅ Чудово, {user_name}! Підписку підтверджено.\n\n{profile_text}",
            reply_markup=get_profile_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    else:
        await callback.answer("❌ Ви ще не підписані!", show_alert=True)
