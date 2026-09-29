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


# --- Bug 5: scoring rewarded wrong guesses --------------------------------

from logic_utils import update_score


def test_too_high_costs_points_on_an_even_attempt():
    # The old code returned 105 here: "Too High" on an even attempt ADDED 5.
    assert update_score(100, "Too High", 2) == 95


def test_both_wrong_directions_cost_the_same():
    assert update_score(100, "Too High", 4) == update_score(100, "Too Low", 4)


def test_winning_sooner_scores_higher():
    assert update_score(0, "Win", 1) > update_score(0, "Win", 5)


def test_win_on_first_attempt_scores_90():
    assert update_score(0, "Win", 1) == 90


def test_win_score_never_drops_below_10():
    assert update_score(0, "Win", 50) == 10


# --- Bug 6: range was cosmetic, never enforced, and Hard was unwinnable ----

import math

from logic_utils import get_range_for_difficulty, parse_guess


def test_guess_above_the_range_is_rejected():
    # Easy is 1-20, so 500 must not be accepted as a playable guess.
    ok, value, err = parse_guess("500", 1, 20)
    assert ok is False
    assert value is None
    assert "between 1 and 20" in err


def test_negative_guess_is_rejected():
    ok, _, err = parse_guess("-7", 1, 100)
    assert ok is False
    assert "between 1 and 100" in err


def test_guess_on_the_boundary_is_accepted():
    assert parse_guess("1", 1, 20) == (True, 1, None)
    assert parse_guess("20", 1, 20) == (True, 20, None)


def test_parse_guess_still_works_without_bounds():
    # Bounds are optional so the starter behaviour is unchanged.
    assert parse_guess("42") == (True, 42, None)


def test_every_difficulty_is_actually_winnable():
    # Hard used to be 1-50 with 5 attempts, but binary search needs 6 there.
    limits = {"Easy": 6, "Normal": 8, "Hard": 7}
    for difficulty, allowed in limits.items():
        low, high = get_range_for_difficulty(difficulty)
        needed = math.ceil(math.log2(high - low + 1))
        assert allowed >= needed, f"{difficulty} needs {needed} but allows {allowed}"
