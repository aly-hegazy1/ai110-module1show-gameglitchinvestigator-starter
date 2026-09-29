# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

**What the game is for.** Glitchy Guesser is a Streamlit number-guessing game.
The app picks a secret number inside a range set by the difficulty, and the
player has a limited number of attempts to find it. After each guess the game
says whether the guess was too high or too low, adjusts a score, and ends the
round on a win or when the attempts run out. A Developer Debug Info panel shows
the secret, so the game can be tested without guessing blind.

**Bugs found.** Seven, documented in full with reproduction steps in
[reflection.md](reflection.md):

| # | Bug | Effect |
|---|-----|--------|
| 1 | Hint text inverted | `"Too High"` was paired with `"📈 Go HIGHER!"`, so following the hint walked you away from the secret |
| 2 | Secret cast to `str` on even attempts | `guess > secret` threw `TypeError`, a silent `except` retried it as a **string** compare, and `"9" > "50"` is `True` — the same guess flipped answers between turns |
| 3 | New Game never reset `status` | After a win `status` stayed `"won"`, `st.stop()` fired on every rerun, and the app was dead until restarted |
| 4 | Attempt counter off by one, and incremented before validation | Normal showed 7 attempts instead of 8, and a typo burned a turn |
| 5 | `update_score` rewarded wrong guesses | `"Too High"` **added** 5 points on even attempts; the win payout double-counted the current turn |
| 6 | Range was decorative | Banner always said "1 and 100"; bounds were never enforced; Hard (1-50, 5 attempts) was mathematically unwinnable |
| 7 | `logic_utils.py` was all stubs | Every test errored, and the tests compared a string against a 2-tuple |

**Fixes applied.**

- **Refactored** `get_range_for_difficulty`, `parse_guess`, `check_guess` and
  `update_score` out of `app.py` into [logic_utils.py](logic_utils.py).
  `app.py` is now UI and session state only, which is what makes the logic
  importable by tests.
- **Corrected the hint direction** and split the player-facing text into
  `get_hint_message()`, so `check_guess` returns just the outcome string that
  the starter tests assert on.
- **Deleted the `except TypeError` fallback** instead of porting it, and removed
  the `str()` cast in `app.py` that caused it. A bad type now raises loudly
  rather than silently comparing numbers alphabetically.
- **Added `start_new_round()`** as the single place a round begins, called by
  both first-time setup and the New Game button, so all five session keys are
  always reset together.
- **Moved the attempt increment** inside the branch that accepted a valid guess,
  and seeded the counter at 0.
- **Made both wrong directions cost the same**, and fixed the win payout to
  `100 - 10 * attempt_number`.
- **Enforced the range** in `parse_guess` via optional `low`/`high` bounds, made
  the banner report the real range, and retuned Hard so it is winnable.
- **Grew the suite from 3 to 19 tests.** Each bug-targeting test was run against
  the pre-fix code with `git show HEAD:app.py` and confirmed to fail there
  first — a test that passes on broken code proves nothing.

## 📸 Demo Walkthrough

A full round on **Normal** difficulty. The secret is **42** (visible because the
Developer Debug Info panel is expanded), the range is **1-100**, and the player
gets **8 attempts**.

1. **The game opens.** The banner reads *"Guess a number between 1 and 100.
   Attempts left: 8"* — the range matches the difficulty in the sidebar, and the
   full 8 attempts are available before anything has been guessed.
2. **The player types `abc` and clicks Submit.** The game shows
   *"That is not a number."* The attempt counter **stays at 8** and nothing is
   added to the history — a typo costs nothing.
3. **The player types `500` and clicks Submit.** The game shows
   *"Guess must be between 1 and 100."* Again **no attempt is consumed**,
   because an out-of-range number was never a real guess.
4. **Guess of 40 → "Too Low", hint "📈 Go HIGHER!"** Attempt 1 of 8 is used,
   attempts left drops to 7, and the score moves from 0 to **-5**.
5. **Guess of 70 → "Too High", hint "📉 Go LOWER!"** The hint points back down
   toward 42. Attempt 2, attempts left 6, score **-10**.
6. **Guess of 50 → "Too High", hint "📉 Go LOWER!"** The player now knows the
   answer is between 40 and 50. Attempt 3, attempts left 5, score **-15**.
7. **Guess of 42 → "Win", 🎉 Correct!** Balloons fire and the game reports
   *"You won! The secret was 42."* Winning on attempt 4 pays
   `100 - 10 * 4 = 60` points, so the score goes from -15 to **45**.
8. **The round locks.** Submitting again shows *"You already won. Start a new
   game to play again."* — the finished round cannot be played past.
9. **The player clicks New Game 🔁.** A fresh secret is drawn *from the current
   difficulty's range*, and attempts, score, status and history all reset. The
   banner is back to *"Attempts left: 8"* and the game is immediately playable
   again.
10. **Losing works too.** If the 8 attempts run out without a correct guess, the
    game reports *"Out of attempts! The secret was ..."* and locks the same way,
    and New Game clears it.

**Scoring rules:** a wrong guess costs 5 points in either direction. A win pays
`100 - 10 * attempt_number`, with a floor of 10 — so winning on the first guess
is worth 90 and guessing sooner is always worth more.

**Difficulty:** Easy is 1-20 with 6 attempts, Normal is 1-100 with 8, and Hard
is 1-100 with 7. Every one of those is winnable with perfect play — Hard is
exactly `ceil(log2(100)) = 7` guesses, so it allows no wasted attempt.

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
$ python -m pytest tests/ -v
============================= test session starts ==============================
platform darwin -- Python 3.13.9, pytest-9.1.1, pluggy-1.5.0 -- /Users/alyhegazy/miniconda3/bin/python3
cachedir: .pytest_cache
rootdir: /Users/alyhegazy/Desktop/CodePath /ai110-module1show-gameglitchinvestigator-starter
plugins: anyio-4.15.1
collecting ... collected 19 items

tests/test_game_logic.py::test_winning_guess PASSED                      [  5%]
tests/test_game_logic.py::test_guess_too_high PASSED                     [ 10%]
tests/test_game_logic.py::test_guess_too_low PASSED                      [ 15%]
tests/test_game_logic.py::test_too_high_hint_tells_player_to_go_lower PASSED [ 21%]
tests/test_game_logic.py::test_too_low_hint_tells_player_to_go_higher PASSED [ 26%]
tests/test_game_logic.py::test_single_digit_guess_below_secret_is_too_low PASSED [ 31%]
tests/test_game_logic.py::test_three_digit_guess_above_secret_is_too_high PASSED [ 36%]
tests/test_game_logic.py::test_same_guess_always_gives_the_same_outcome PASSED [ 42%]
tests/test_game_logic.py::test_string_secret_raises_instead_of_comparing_as_text PASSED [ 47%]
tests/test_game_logic.py::test_too_high_costs_points_on_an_even_attempt PASSED [ 52%]
tests/test_game_logic.py::test_both_wrong_directions_cost_the_same PASSED [ 57%]
tests/test_game_logic.py::test_winning_sooner_scores_higher PASSED       [ 63%]
tests/test_game_logic.py::test_win_on_first_attempt_scores_90 PASSED     [ 68%]
tests/test_game_logic.py::test_win_score_never_drops_below_10 PASSED     [ 73%]
tests/test_game_logic.py::test_guess_above_the_range_is_rejected PASSED  [ 78%]
tests/test_game_logic.py::test_negative_guess_is_rejected PASSED         [ 84%]
tests/test_game_logic.py::test_guess_on_the_boundary_is_accepted PASSED  [ 89%]
tests/test_game_logic.py::test_parse_guess_still_works_without_bounds PASSED [ 94%]
tests/test_game_logic.py::test_every_difficulty_is_actually_winnable PASSED [100%]

============================== 19 passed in 0.01s ==============================
```

Before any fixes this suite reported `3 failed in 0.02s` — every starter test
errored on `NotImplementedError` because the logic still lived in `app.py` and
`logic_utils.py` was a set of stubs.

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
