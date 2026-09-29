import random

import streamlit as st

# FIX: Refactored all game logic out of this file and into logic_utils.py using
# Claude Code in agent mode. app.py is now UI + session state only, which is
# what makes tests/test_game_logic.py able to import the logic directly.
from logic_utils import (
    check_guess,
    get_hint_message,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

# FIX (Bug 6): Hard gave 5 attempts over a 1-50 range, but binary search needs
# 6 there -- it could not be won. Every difficulty is now solvable with perfect
# play: Easy needs 5 of 6, Normal needs 7 of 8, Hard needs 7 of 7.
attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 7,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# FIX (Bug 3): "New Game" used to reset only attempts and secret, so status
# stayed "won"/"lost" and the st.stop() guard below killed the app forever.
# Starting a round now happens in exactly one place, so the initial game and
# every restart are guaranteed to set the same five keys.
def start_new_round(low: int, high: int):
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []


if "status" not in st.session_state:
    start_new_round(low, high)

st.subheader("Make a guess")

# FIX (Bug 6): this said "between 1 and 100" no matter what, even on Easy
# where the range is 1-20. It now reports the difficulty's actual range.
st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    # FIX (Bug 3): was random.randint(1, 100) regardless of difficulty, so an
    # Easy round (1-20) could be handed an unreachable secret.
    start_new_round(low, high)
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        # FIX (Bug 4): the counter used to be incremented before this check, so
        # a typo burned a turn and pushed the raw text into the history list.
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # FIX (Bug 2, root cause): this used to cast the secret to str on every
        # even-numbered attempt, so the same guess was judged numerically one
        # turn and alphabetically the next. The AI first suggested patching
        # check_guess to tolerate both types; I pushed back and deleted the
        # cast here instead, because the caller was the actual bug.
        outcome = check_guess(guess_int, st.session_state.secret)
        message = get_hint_message(outcome)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
