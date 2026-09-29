"""Pure game logic for Glitchy Guesser.

Nothing in this module imports Streamlit or touches session state, so every
function here can be called directly from tests.
"""


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


# FIX: Moved here from app.py with Claude Code (agent mode). I marked the two
# bugs with # FIXME first, then asked it to move the function AND fix the
# high/low bug in one step. I did NOT accept its first instinct of coercing
# with int(guess)/int(secret) - that hides the caller's type bug instead of
# fixing it. See reflection.md section 2.
def check_guess(guess, secret):
    """
    Compare guess to secret and return the outcome.

    Returns one of: "Win", "Too High", "Too Low"

    Both arguments must be ints. There is deliberately no str fallback here:
    if a caller passes the secret as a string, the comparison raises TypeError
    instead of silently comparing the numbers alphabetically.
    """
    if guess == secret:
        return "Win"

    if guess > secret:
        return "Too High"

    return "Too Low"


# FIX (Bug 1): The hint text used to be bundled into check_guess and pointed
# the wrong way ("Too High" -> "Go HIGHER!"). Splitting the player-facing copy
# out of the comparison was my change, not the AI's - it also let the starter
# tests assert on a plain string. Covered by the hint tests in tests/.
def get_hint_message(outcome: str):
    """Player-facing hint text for an outcome returned by check_guess()."""
    if outcome == "Win":
        return "\U0001f389 Correct!"

    if outcome == "Too High":
        return "\U0001f4c9 Go LOWER!"

    if outcome == "Too Low":
        return "\U0001f4c8 Go HIGHER!"

    return ""


# FIX (Bug 5): "Too High" used to ADD 5 points whenever attempt_number was
# even, so guessing too high on an even turn scored the same as being right.
# Both wrong outcomes now cost the same 5 points. The win payout also used
# (attempt_number + 1), which double-counted the turn you are currently on.
def update_score(current_score: int, outcome: str, attempt_number: int):
    """
    Update score based on outcome and attempt number.

    attempt_number is 1 for the first guess. Winning on the first guess is
    worth 90 points and each further attempt costs 10, with a floor of 10.
    A wrong guess costs 5 points regardless of which direction it missed.
    """
    if outcome == "Win":
        points = 100 - 10 * attempt_number
        if points < 10:
            points = 10
        return current_score + points

    if outcome in ("Too High", "Too Low"):
        return current_score - 5

    return current_score
