import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart

# Import config and handlers
from bot.config import API_TOKEN
from bot.handlers.start import start_handler, check_sub_callback
from bot.handlers.menu import profile_callback, games_callback, hints_callback, daily_bonus_callback
from bot.handlers.admin import admin_panel, start_broadcast, dupe_game_balance, BroadcastState
from bot.handlers.admin_wordly import start_wordly_game_setup, get_wordly_word, get_description_decision, get_wordly_description, AdminWordlyState
from bot.games.word_game import start_word_game, process_word_guess, WordGameState
from bot.games.slots_game import start_slots_game, process_slots_bet, SlotsState
from bot.games.blackjack_game import start_blackjack_game, process_blackjack_bet, player_action, BlackjackState
from bot.utils.database import init_db

async def main():
    """Initializes and starts the bot."""
    logging.basicConfig(level=logging.INFO)

    # Initialize the database
    init_db()

    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    # Register message handlers
    dp.message.register(start_handler, CommandStart())
    dp.message.register(admin_panel, Command("admin"))
    dp.message.register(dupe_game_balance, Command("dupe"))
    dp.message.register(start_broadcast, BroadcastState.get_message)
    dp.message.register(start_wordly_game_setup, Command("gamewordly"))

    # Register callback query handlers
    dp.callback_query.register(check_sub_callback, F.data == "check_sub")
    dp.callback_query.register(profile_callback, F.data == "profile")
    dp.callback_query.register(games_callback, F.data == "games")
    dp.callback_query.register(hints_callback, F.data == "hints")
    dp.callback_query.register(daily_bonus_callback, F.data == "daily_bonus")

    # Word game handlers
    dp.callback_query.register(start_word_game, F.data == "word_game")
    dp.message.register(process_word_guess, WordGameState.in_game)

    # Slots game handlers
    dp.callback_query.register(start_slots_game, F.data == "slots")
    dp.message.register(process_slots_bet, SlotsState.get_bet)

    # Blackjack game handlers
    dp.callback_query.register(start_blackjack_game, F.data == "blackjack")
    dp.message.register(process_blackjack_bet, BlackjackState.get_bet)
    dp.callback_query.register(player_action, BlackjackState.player_turn, F.data.in_(['hit', 'stand']))

    print("Бот запущен... (Ctrl+C для остановки)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
