# bot/games/word_game.py
import random
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.games.word_list import WORDS
from bot.utils.database import update_game_balance
from bot.games.global_game_state import global_wordly_game

class WordGameState(StatesGroup):
    in_game = State()
    in_global_game = State()

async def start_word_game(callback: CallbackQuery, state: FSMContext):
    """Starts the 'Guess the Word' game."""
    category = random.choice(list(WORDS.keys()))
    word = random.choice(WORDS[category])

    await state.update_data(secret_word=word, category=category)
    await state.set_state(WordGameState.in_game)

    await callback.message.edit_text(
        f"Я загадав слово з категорії: *{category}*.\n"
        f"У слові *{len(word)}* літер.\n\n"
        f"Напишіть ваш варіант:",
        parse_mode="Markdown"
    )
    await callback.answer()

async def process_word_guess(message: Message, state: FSMContext):
    """Processes the user's guess in the 'Guess the Word' game."""
    user_guess = message.text.lower()
    data = await state.get_data()
    secret_word = data.get("secret_word")

    if len(user_guess) != len(secret_word):
        await message.answer(f"Слово повинно складатися з {len(secret_word)} літер. Спробуйте ще раз.")
        return

    if user_guess == secret_word:
        update_game_balance(message.from_user.id, 50)
        await state.clear()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Зіграти ще раз", callback_data="word_game")],
            [InlineKeyboardButton(text="⬅️ Назад до ігор", callback_data="games")]
        ])

        await message.answer(
            f"🎉 Вітаю! Ви вгадали слово!\n\nВи отримуєте *50G* на ігровий баланс.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return

    result_squares = []
    secret_word_list = list(secret_word)

    # First pass for correct letters in the correct position (green)
    for i in range(len(secret_word)):
        if user_guess[i] == secret_word[i]:
            result_squares.append("🟩")
            secret_word_list.remove(user_guess[i])
        else:
            result_squares.append("❓") # Placeholder

    # Second pass for correct letters in the wrong position (orange)
    for i in range(len(secret_word)):
        if result_squares[i] == "❓":
            if user_guess[i] in secret_word_list:
                result_squares[i] = "🟧"
                secret_word_list.remove(user_guess[i])
            else:
                result_squares[i] = "🟥"

    await message.answer(" ".join(result_squares) + "\n\nСпробуйте ще раз.")

async def join_global_wordly(callback: CallbackQuery, state: FSMContext):
    """Handles a player joining the global wordly game."""
    if not global_wordly_game["is_active"]:
        await callback.answer("😔 Гра від адміна вже закінчилася.", show_alert=True)
        return

    if callback.from_user.id in global_wordly_game["winners"]:
        await callback.answer("🎉 Ви вже вгадали це слово!", show_alert=True)
        return

    await state.set_state(WordGameState.in_global_game)
    await callback.message.answer("Введіть ваш варіант слова:")
    await callback.answer()

async def process_global_word_guess(message: Message, state: FSMContext):
    """Processes the user's guess in the global word game."""
    user_guess = message.text.lower()
    secret_word = global_wordly_game["secret_word"]

    if not global_wordly_game["is_active"]:
        await message.answer("😔 Гра від адміна вже закінчилася.")
        await state.clear()
        return

    if len(user_guess) != len(secret_word):
        await message.answer(f"Слово повинно складатися з {len(secret_word)} літер. Спробуйте ще раз.")
        return

    if user_guess == secret_word:
        user_id = message.from_user.id
        if user_id not in global_wordly_game["winners"]:
            global_wordly_game["winners"].append(user_id)
            update_game_balance(user_id, 50) # Or a different reward for the global game
            await message.answer(f"🏆 Вітаю! Ви вгадали слово адміна!\n\nВи отримуєте *50G* на ігровий баланс.", parse_mode="Markdown")
        else:
            await message.answer("🎉 Ви вже вгадали це слово!")
        await state.clear()
        return

    # The same square logic as in the normal game
    result_squares = []
    secret_word_list = list(secret_word)
    for i in range(len(secret_word)):
        if user_guess[i] == secret_word[i]:
            result_squares.append("🟩")
            secret_word_list.remove(user_guess[i])
        else:
            result_squares.append("❓")
    for i in range(len(secret_word)):
        if result_squares[i] == "❓":
            if user_guess[i] in secret_word_list:
                result_squares[i] = "🟧"
                secret_word_list.remove(user_guess[i])
            else:
                result_squares[i] = "🟥"

    await message.answer(" ".join(result_squares) + "\n\nНевірно. Спробуйте ще раз.")
