# bot/games/slots_game.py
import random
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.utils.database import get_user_profile, update_game_balance

class SlotsState(StatesGroup):
    get_bet = State()

REELS = ["🍒", "🍋", "🍊", "🍉", "🍇", "🍓", "🔔", "💎", "7️⃣"]

async def start_slots_game(callback: CallbackQuery, state: FSMContext):
    """Starts the Slots game and asks for a bet."""
    user_id = callback.from_user.id
    profile_data = get_user_profile(user_id)
    balance = profile_data[1] if profile_data else 0

    await callback.message.edit_text(
        f"🎰 *Слоти*\n\n"
        f"Ваш ігровий баланс: *{balance}G*\n"
        f"Введіть вашу ставку:",
        parse_mode="Markdown"
    )
    await state.set_state(SlotsState.get_bet)
    await callback.answer()

async def process_slots_bet(message: Message, state: FSMContext):
    """Processes the bet and spins the reels."""
    try:
        bet = int(message.text)
    except ValueError:
        await message.answer("Будь ласка, введіть число.")
        return

    user_id = message.from_user.id
    profile_data = get_user_profile(user_id)
    balance = profile_data[1] if profile_data else 0

    if bet <= 0:
        await message.answer("Ставка повинна бути більшою за нуль.")
        return
    if bet > balance:
        await message.answer("У вас недостатньо коштів для такої ставки.")
        return

    await state.clear()
    update_game_balance(user_id, -bet)

    result = [random.choice(REELS) for _ in range(3)]

    winnings = 0
    if result[0] == result[1] == result[2]:
        if result[0] == "7️⃣":
            winnings = bet * 10
        elif result[0] == "💎":
            winnings = bet * 7
        else:
            winnings = bet * 5
        result_text = f"🎉 Джекпот! Ви виграли *{winnings}G*!"
    elif result[0] == result[1] or result[1] == result[2]:
        winnings = bet * 2
        result_text = f"👍 Непогано! Ви виграли *{winnings}G*!"
    else:
        result_text = f"😔 На жаль, ви програли *{bet}G*."

    if winnings > 0:
        update_game_balance(user_id, winnings)

    new_balance = get_user_profile(user_id)[1]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Зіграти ще раз", callback_data="slots")],
        [InlineKeyboardButton(text="⬅️ Назад до ігор", callback_data="games")]
    ])

    await message.answer(
        f"Результат: [{result[0]}] [{result[1]}] [{result[2]}]\n\n"
        f"{result_text}\n\nВаш новий баланс: *{new_balance}G*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
