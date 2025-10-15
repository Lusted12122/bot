# bot/handlers/menu.py
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from bot.config import CHANNEL_USERNAME
from bot.utils.database import get_user_profile, claim_daily_bonus

def get_profile_keyboard():
    """Creates the keyboard for the user profile."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Щоденний бонус", callback_data="daily_bonus")],
        [InlineKeyboardButton(text="🎮 Ігри", callback_data="games"),
         InlineKeyboardButton(text="💡 Підказки", callback_data="hints")],
        [InlineKeyboardButton(text="📢 Канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
    ])

async def get_profile_text(bot, user_id, user_name):
    """Generates the text for the user profile."""
    bot_user = await bot.get_me()
    profile_data = get_user_profile(user_id)
    bonus_balance, game_balance, purchases, referrals = profile_data if profile_data else (0, 500, 0, 0)
    return (
        f"👤 *Профіль: {user_name}*\n\n"
        f"- 💰 Бонусний баланс: *{bonus_balance}*\n"
        f"- 🎮 Ігровий баланс: *{game_balance}G*\n"
        f"- 🛒 Кількість покупок: *{purchases}*\n"
        f"- 👥 Запросив(ла): *{referrals}* осіб\n\n"
        f"🔗 *Ваше реферальне посилання:*\n"
        f"`https://t.me/{bot_user.username}?start={user_id}`\n\n"
        f"ℹ️ _Запрошуйте друзів та отримуйте від 2 до 5 грн на бонусний баланс за кожного!_"
    )

async def profile_callback(callback: CallbackQuery):
    """Handles the 'Profile' button press by showing the user's profile."""
    bot = callback.bot
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    profile_text = await get_profile_text(bot, user_id, user_name)
    await callback.message.edit_text(
        profile_text,
        reply_markup=get_profile_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

async def games_callback(callback: CallbackQuery):
    """Handles the 'Games' button press."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Блекджек", callback_data="blackjack"),
         InlineKeyboardButton(text="🎰 Слоти", callback_data="slots")],
        [InlineKeyboardButton(text="📝 Вгадай слово", callback_data="word_game")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")]
    ])
    await callback.message.edit_text("Оберіть гру:", reply_markup=keyboard)
    await callback.answer()

async def hints_callback(callback: CallbackQuery):
    """Handles the 'Hints' button press."""
    hints_text = (
        "*💡 Підказки та остання інформація:*\n\n"
        "*🆕 Що нового?*\n"
        "- ✨ Додано *щоденний бонус* у 100G!\n"
        "- 🎮 З'явилися нові ігри: *Блекджек*, *Слоти* та *Вгадай слово*.\n"
        "- 👥 Покращено реферальну систему.\n\n"
        "*🏆 Як заробити?*\n"
        "- 🤝 Запрошуйте друзів за своїм реферальним посиланням.\n"
        "- 🎁 Забирайте щоденний бонус.\n"
        "- 🎰 Випробовуйте удачу в іграх!\n\n"
        "*🔔 Залишайтеся на зв'язку:*\n"
        f"- Слідкуйте за новинами в нашому [каналі](https://t.me/{CHANNEL_USERNAME[1:]})."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")]
    ])
    await callback.message.edit_text(
        hints_text,
        reply_markup=keyboard,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await callback.answer()

async def daily_bonus_callback(callback: CallbackQuery):
    """Handles the 'Daily Bonus' button press."""
    user_id = callback.from_user.id
    if claim_daily_bonus(user_id):
        await callback.answer("✅ Ви успішно отримали 100G!", show_alert=True)
        # Update profile message to show new balance
        user_name = callback.from_user.first_name
        profile_text = await get_profile_text(callback.bot, user_id, user_name)
        await callback.message.edit_text(profile_text, reply_markup=get_profile_keyboard(), parse_mode="Markdown")
    else:
        await callback.answer("❌ Ви вже отримували бонус сьогодні.", show_alert=True)
