# bot/games/blackjack_game.py
import random
import asyncio
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.utils.database import get_user_profile, update_game_balance

class BlackjackState(StatesGroup):
    get_bet = State()
    player_turn = State()

SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = {"A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10}

def create_deck():
    return [(suit, rank) for suit in SUITS for rank in RANKS]

def get_hand_value(hand):
    value = sum(RANKS[card[1]] for card in hand)
    num_aces = sum(1 for card in hand if card[1] == 'A')
    while value > 21 and num_aces:
        value -= 10
        num_aces -= 1
    return value

def hand_to_string(hand):
    return " ".join([f"{card[1]}{card[0]}" for card in hand])

async def start_blackjack_game(callback: CallbackQuery, state: FSMContext):
    """Starts the Blackjack game and asks for a bet."""
    user_id = callback.from_user.id
    profile_data = get_user_profile(user_id)
    balance = profile_data[1] if profile_data else 0

    await callback.message.edit_text(
        f"🃏 *Блекджек*\n\n"
        f"Ваш ігровий баланс: *{balance}G*\n"
        f"Введіть вашу ставку:",
        parse_mode="Markdown"
    )
    await state.set_state(BlackjackState.get_bet)
    await callback.answer()

async def process_blackjack_bet(message: Message, state: FSMContext):
    """Processes the bet and starts the game."""
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

    update_game_balance(user_id, -bet)
    deck = create_deck()
    random.shuffle(deck)

    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    await state.update_data(deck=deck, player_hand=player_hand, dealer_hand=dealer_hand, bet=bet)
    await state.set_state(BlackjackState.player_turn)

    player_value = get_hand_value(player_hand)
    dealer_value = get_hand_value([dealer_hand[0]]) # Show only one dealer card

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Ще", callback_data="hit"),
         InlineKeyboardButton(text="✋ Досить", callback_data="stand")]
    ])

    await message.answer(
        f"""Карти дилера: {dealer_hand[0][1]}{dealer_hand[0][0]} [?]
Ваші карти: {hand_to_string(player_hand)} (Очки: {player_value})

Ваш хід:""",
        reply_markup=keyboard
    )

async def player_action(callback: CallbackQuery, state: FSMContext):
    """Handles player's action (hit or stand)."""
    action = callback.data
    data = await state.get_data()
    deck, player_hand, dealer_hand, bet = data['deck'], data['player_hand'], data['dealer_hand'], data['bet']

    if action == "hit":
        player_hand.append(deck.pop())
        await state.update_data(player_hand=player_hand, deck=deck)
        player_value = get_hand_value(player_hand)

        if player_value > 21:
            await end_game(callback, state, "bust")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Ще", callback_data="hit"),
             InlineKeyboardButton(text="✋ Досить", callback_data="stand")]
        ])
        await callback.message.edit_text(
            f"""Карти дилера: {dealer_hand[0][1]}{dealer_hand[0][0]} [?]
Ваші карти: {hand_to_string(player_hand)} (Очки: {player_value})

Ваш хід:""",
            reply_markup=keyboard
        )
    elif action == "stand":
        await dealer_turn(callback, state)

    await callback.answer()

async def dealer_turn(callback: CallbackQuery, state: FSMContext):
    """Handles the dealer's turn."""
    data = await state.get_data()
    deck, player_hand, dealer_hand = data['deck'], data['player_hand'], data['dealer_hand']

    await callback.message.edit_text(
        f"""Карти дилера: {hand_to_string(dealer_hand)} (Очки: {get_hand_value(dealer_hand)})
Ваші карти: {hand_to_string(player_hand)} (Очки: {get_hand_value(player_hand)})

Хід дилера..."""
    )
    await asyncio.sleep(1)

    while get_hand_value(dealer_hand) < 17:
        dealer_hand.append(deck.pop())
        await callback.message.edit_text(
            f"""Карти дилера: {hand_to_string(dealer_hand)} (Очки: {get_hand_value(dealer_hand)})
Ваші карти: {hand_to_string(player_hand)} (Очки: {get_hand_value(player_hand)})

Дилер бере карту..."""
        )
        await asyncio.sleep(1)

    player_value = get_hand_value(player_hand)
    dealer_value = get_hand_value(dealer_hand)

    if dealer_value > 21 or player_value > dealer_value:
        await end_game(callback, state, "win")
    elif player_value < dealer_value:
        await end_game(callback, state, "lose")
    else:
        await end_game(callback, state, "push")

async def end_game(callback: CallbackQuery, state: FSMContext, result: str):
    """Ends the game and shows the result."""
    data = await state.get_data()
    bet, player_hand, dealer_hand = data['bet'], data['player_hand'], data['dealer_hand']
    user_id = callback.from_user.id

    player_score = get_hand_value(player_hand)
    dealer_score = get_hand_value(dealer_hand)

    if result == "bust":
        result_text = f"😔 Перебір! У вас {player_score}. Ви програли *{bet}G*."
    elif result == "win":
        winnings = bet * 2
        update_game_balance(user_id, winnings)
        result_text = f"🎉 Ви виграли! У вас {player_score}, у дилера {dealer_score}. Ваш виграш: *{winnings}G*."
    elif result == "lose":
        result_text = f"😔 Ви програли. У вас {player_score}, у дилера {dealer_score}. Втрачено *{bet}G*."
    elif result == "push":
        update_game_balance(user_id, bet)  # Return bet
        result_text = f"🤝 Нічия. У вас і у дилера по {player_score}. Вашу ставку повернуто."

    await state.clear()
    new_balance = get_user_profile(user_id)[1]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🃏 Зіграти ще раз", callback_data="blackjack")],
        [InlineKeyboardButton(text="⬅️ Назад до ігор", callback_data="games")]
    ])

    final_text = (
        f"Дилер: {hand_to_string(dealer_hand)} ({dealer_score})\n"
        f"Ви: {hand_to_string(player_hand)} ({player_score})\n\n"
        f"{result_text}\n\n"
        f"Ваш новий баланс: *{new_balance}G*"
    )

    await callback.message.edit_text(
        final_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
