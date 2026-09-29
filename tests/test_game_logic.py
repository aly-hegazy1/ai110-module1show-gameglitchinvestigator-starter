from logic_utils import check_guess

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


# ---------------------------------------------------------------------------
# Regression tests for the two bugs fixed in Step 2.
# Written with Claude Code (agent mode) after marking the bugs with # FIXME.
# ---------------------------------------------------------------------------

import pytest

from logic_utils import get_hint_message


# --- Bug 1: the hint message pointed the player the wrong way --------------

def test_too_high_hint_tells_player_to_go_lower():
    # Guess of 60 against a secret of 50 must tell the player to go LOWER.
    # Before the fix this returned "Go HIGHER!", which walked you away from 50.
    outcome = check_guess(60, 50)
    assert outcome == "Too High"
    assert get_hint_message(outcome) == "\U0001f4c9 Go LOWER!"


def test_too_low_hint_tells_player_to_go_higher():
    outcome = check_guess(40, 50)
    assert outcome == "Too Low"
    assert get_hint_message(outcome) == "\U0001f4c8 Go HIGHER!"


# --- Bug 2: numbers were compared as text on even-numbered attempts --------

def test_single_digit_guess_below_secret_is_too_low():
    # As strings "9" > "50" is True, so the old code called this "Too High".
    assert check_guess(9, 50) == "Too Low"


def test_three_digit_guess_above_secret_is_too_high():
    # As strings "100" > "50" is False, so the old code called this "Too Low".
    assert check_guess(100, 50) == "Too High"


def test_same_guess_always_gives_the_same_outcome():
    # The old code alternated between numeric and alphabetical comparison, so
    # repeating a guess could flip the answer. The result must be stable.
    assert check_guess(9, 50) == check_guess(9, 50) == check_guess(9, 50)


def test_string_secret_raises_instead_of_comparing_as_text():
    # The silent `except TypeError` fallback is gone: a bad type must fail loudly
    # rather than quietly comparing the two values alphabetically.
    with pytest.raises(TypeError):
        check_guess(9, "50")
