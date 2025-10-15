# bot/handlers/admin_wordly.py
from aiogram import Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import ADMIN_ID
from bot.utils.database import get_all_users
from bot.games.global_game_state import global_wordly_game

class AdminWordlyState(StatesGroup):
    get_word = State()
    get_description_decision = State()
    get_description = State()

async def start_wordly_game_setup(message: Message, state: FSMContext):
    """Starts the setup for the global word game."""
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.answer("📝 Введіть слово, яке хочете загадати для всіх:")
    await state.set_state(AdminWordlyState.get_word)

async def get_wordly_word(message: Message, state: FSMContext):
    """Gets the word and asks about the description."""
    await state.update_data(word=message.text.lower())
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Так", callback_data="add_desc"),
         InlineKeyboardButton(text="❌ Ні", callback_data="no_desc")]
    ])
    await message.answer("Хочете додати підказку до слова?", reply_markup=keyboard)
    await state.set_state(AdminWordlyState.get_description_decision)

async def get_description_decision(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Handles the admin's decision about the description."""
    if callback.data == "add_desc":
        await callback.message.edit_text("✏️ Введіть вашу підказку:")
        await state.set_state(AdminWordlyState.get_description)
    else:
        data = await state.get_data()
        word = data.get("word")
        await broadcast_wordly_game(bot, word)
        await callback.message.edit_text("✅ Розсилку гри запущено без підказки!")
        await state.clear()
    await callback.answer()

async def get_wordly_description(message: Message, state: FSMContext, bot: Bot):
    """Gets the description and starts the broadcast."""
    data = await state.get_data()
    word = data.get("word")
    description = message.text
    
    await broadcast_wordly_game(bot, word, description)
    await message.answer("✅ Розсилку гри з підказкою запущено!")
    await state.clear()

async def broadcast_wordly_game(bot: Bot, word: str, hint: str = None):
    """Broadcasts the game to all users and sets the global state."""
    # Set global game state
    global_wordly_game["is_active"] = True
    global_wordly_game["secret_word"] = word
    global_wordly_game["hint"] = hint

    user_ids = get_all_users()
    
    text = f"🔥 *Гра від Адміна: Вгадай Слово!* 🔥\n\nЗагадано слово з *{len(word)}* літер."
    if hint:
        text += f"\n\n*Підказка від адміністратора:*\n_{hint}_"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Грати", callback_data="join_global_wordly")]
    ])

    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to send global game to {user_id}: {e}")
