# bot/games/global_game_state.py

# This dictionary will hold the state of the global wordly game.
global_wordly_game = {
    "is_active": False,
    "secret_word": None,
    "hint": None,
    "winners": [] # List of user_ids who have already won
}
