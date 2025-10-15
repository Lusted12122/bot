# bot/handlers/admin.py
from aiogram import Bot, F
from aiogram.types import Message
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import ADMIN_ID
from bot.utils.database import get_all_users, update_game_balance, get_user_profile

class BroadcastState(StatesGroup):
    get_message = State()

async def admin_panel(message: Message, state: FSMContext):
    """Handles the /admin command and shows the admin panel."""
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("Ви увійшли до адмін-панелі. Введіть повідомлення для розсилки:")
    await state.set_state(BroadcastState.get_message)

async def start_broadcast(message: Message, state: FSMContext, bot: Bot):
    """Starts the broadcast process to all users."""
    if message.from_user.id != ADMIN_ID:
        return

    await state.clear()
    user_ids = get_all_users()
    sent_count = 0
    failed_count = 0

    await message.answer(f"Починаю розсилку... Всього користувачів: {len(user_ids)}")

    for user_id in user_ids:
        try:
            await bot.send_message(user_id, message.text)
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Failed to send message to {user_id}: {e}")

    await message.answer(f"✅ Розсилку завершено!\n\nУспішно надіслано: {sent_count}\nНе вдалося надіслати: {failed_count}")

async def dupe_game_balance(message: Message, command: CommandObject):
    """Handles the /dupe command for the admin."""
    if message.from_user.id != ADMIN_ID:
        return

    try:
        amount = int(command.args)
        if amount <= 0:
            await message.answer("Сума повинна бути додатнім числом.")
            return
    except (ValueError, TypeError):
        await message.answer("❌ Неправильний формат команди. Використовуйте /dupe <число>")
        return

    update_game_balance(ADMIN_ID, amount)
    new_balance = get_user_profile(ADMIN_ID)[1]
    await message.answer(f"✅ Успішно додано {amount}G.\nВаш новий ігровий баланс: *{new_balance}G*", parse_mode="Markdown")
