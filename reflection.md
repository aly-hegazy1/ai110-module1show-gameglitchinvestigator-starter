# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

The first time I ran `python -m streamlit run app.py` the game *looked* finished — difficulty selector, attempt counter, score, balloons, a debug expander — but it was unplayable. I opened "Developer Debug Info" so I could see the secret, and even then I could not trust the game: the hints pointed the wrong direction, the same guess produced two different hints on two consecutive turns, my score went **up** for wrong answers, and once I finally hit the secret on purpose, the "New Game" button refused to start a new round. `pytest` didn't help either — all three tests errored out immediately because `logic_utils.py` was still a stub.

Here are the concrete bugs I found, with what I expected versus what actually happened.

**Bug 1 — The hint text is inverted** ([app.py:37-40](app.py#L37-L40))

*Expected:* if my guess is above the secret, the game tells me to go LOWER.
*Actual:* the outcome label and the message contradict each other. `guess > secret` returns `("Too High", "📈 Go HIGHER!")` and `guess < secret` returns `("Too Low", "📉 Go LOWER!")`. The label is right and the sentence the player actually reads is backwards, so following the hints walks you away from the answer every single time.

**Bug 2 — The secret is turned into a string on even-numbered attempts** ([app.py:158-161](app.py#L158-L161))

*Expected:* the secret is an `int` and every guess is compared numerically.
*Actual:* `if st.session_state.attempts % 2 == 0: secret = str(st.session_state.secret)`. Now `check_guess` compares `int` to `str`, `guess > secret` throws a `TypeError`, and the `except TypeError` block at [app.py:41-47](app.py#L41-L47) silently falls back to comparing the two values as **text**. String ordering is alphabetical, not numeric, so `"9" > "50"` is `True` and `"100" > "50"` is `False`. With the secret at 50 I guessed `9` twice in a row and got "Too High" on one attempt and "Too Low" on the next — the same guess, two opposite answers. This is what makes the game feel like the secret number "keeps changing" even though [app.py:92-93](app.py#L92-L93) stores it in session state correctly.

**Bug 3 — "New Game" doesn't actually start a new game** ([app.py:134-138](app.py#L134-L138))

*Expected:* clicking "New Game 🔁" clears everything and lets me play again.
*Actual:* it only resets `attempts` and `secret`. It never resets `status`, `score`, or `history`. So after a win, `st.session_state.status` is still `"won"`, and on the next rerun the guard at [app.py:140-145](app.py#L140-L145) prints "You already won. Start a new game to play again." and calls `st.stop()` — before the submit handler is ever reached. The game is permanently dead and the only escape is restarting the server. Two smaller problems ride along with this one: the new secret is drawn with `random.randint(1, 100)` regardless of difficulty (on Easy the range is 1-20, so the secret can be unreachable), and `attempts` is reset to `0` even though it is initialized to `1` at [app.py:96](app.py#L96), so a fresh game and a restarted game don't even use the same counter.

**Bug 4 — The attempt counter is off by one and charges you for typos** ([app.py:96](app.py#L96), [app.py:148](app.py#L148))

*Expected:* Normal difficulty gives me 8 attempts, and typing garbage costs me nothing.
*Actual:* `attempts` starts at `1` instead of `0`, so a brand-new Normal game already displays "Attempts left: 7" and I really do get one fewer turn. Worse, `st.session_state.attempts += 1` runs at [app.py:148](app.py#L148) *before* `parse_guess` validates the input, so submitting `abc` bumps the counter to 2, appends the raw string `"abc"` to the history list, and burns a turn on input the game already rejected.

**Bug 5 — Scoring rewards wrong guesses** ([app.py:50-65](app.py#L50-L65))

*Expected:* a wrong guess costs points; a win pays more for winning sooner.
*Actual:* `update_score` has an asymmetric branch — `"Too Low"` always subtracts 5, but `"Too High"` **adds** 5 whenever `attempt_number % 2 == 0`. Guessing too high on an even attempt is worth the same as being half-right. The win payout is also wrong: `points = 100 - 10 * (attempt_number + 1)`, and because the counter already started at 1 and was already incremented, winning on my very first real guess scored 70 instead of the 90 the formula was clearly meant to give.

**Bug 6 — The range shown to the player is hardcoded and never enforced** ([app.py:109-112](app.py#L109-L112), [app.py:9-10](app.py#L9-L10))

*Expected:* the prompt matches the selected difficulty, and guesses outside the range are rejected.
*Actual:* the info banner always says "Guess a number between 1 and 100" even on Easy, where `get_range_for_difficulty` returns `(1, 20)`. Nothing ever compares the guess to `low`/`high`, so `500` and `-7` are both accepted as valid guesses and consume attempts. Separately, "Hard" returns `(1, 50)` — a *narrower* range than "Normal" `(1, 100)` — so Hard is easier to guess than Normal while giving you the fewest attempts.

**Bug 7 — The test suite cannot run at all** ([logic_utils.py](logic_utils.py), [tests/test_game_logic.py](tests/test_game_logic.py))

*Expected:* `pytest` runs and tells me which behaviors are broken.
*Actual:* all four functions in `logic_utils.py` are still `raise NotImplementedError` stubs, and the real logic lives in `app.py`, so every test errors before it can assert anything: `3 failed in 0.02s`. On top of that, the tests assert `result == "Win"` while `check_guess` returns a **tuple** `("Win", "🎉 Correct!")` — so even after moving the code over, the tests would still fail until either the tests unpack the tuple or the function's return shape changes.

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
| Normal, secret = 50, guess `60` on attempt 1 | Hint reads "Go LOWER" | Outcome `Too High` but the message shown is `📈 Go HIGHER!` | none — no exception, the wrong text is just rendered |
| Normal, secret = 50, guess `9` on attempt 2 (even) | `Too Low` → "Go HIGHER" | `('Too High', '📈 Go HIGHER!')` — `"9" > "50"` compares as text | none — `TypeError: '>' not supported between instances of 'int' and 'str'` is raised at [app.py:37](app.py#L37) but swallowed by the `except TypeError` at [app.py:41](app.py#L41) |
| Normal, secret = 50, guess `9` again on attempt 3 (odd) | Same guess → same hint as attempt 2 | `('Too Low', '📉 Go LOWER!')` — identical input, opposite answer, because the secret is an `int` again this turn | none |
| Guess the secret correctly, then click **New Game 🔁** | Board clears, score resets, I can guess again | "You already won. Start a new game to play again." forever; `status='won'`, `score=70`, `history=[50]` all survive the reset and `st.stop()` fires | none |
| Fresh Normal game, no input yet | Banner reads "Attempts left: 8" | Banner reads "Attempts left: 7" — `attempts` is initialized to `1` at [app.py:96](app.py#L96) | none |
| Type `abc` and press **Submit Guess 🚀** | Error shown, attempt not counted | `ERROR: That is not a number.` but `attempts` went 1 → 2 and `history` became `['abc']` | none (the `except Exception` at [app.py:26](app.py#L26) converts the `ValueError` into a return value) |
| Easy difficulty (range 1-20), guess `500` | Rejected as out of range | Accepted as a valid guess, scored, and an attempt is consumed; banner still claims the range is "1 and 100" | none |
| `python3 -m pytest tests/` | 3 passed | 3 failed | `NotImplementedError: Refactor this function from app.py into logic_utils.py` — `logic_utils.py:21`; `=== 3 failed in 0.02s ===` |

-------|-------------------|-----------------|------------------------|
| | | | |
| | | | |
| | | | |

---

## 2. How did you use AI as a teammate?

I used **Claude Code (Opus) in agent mode** inside VS Code for this project — it could read `app.py`, `logic_utils.py`, and `tests/test_game_logic.py` together, which mattered a lot here because the bug I cared about most was split across two files. Before asking it for anything I played the game myself, opened the Developer Debug Info panel, and dropped `# FIXME: Logic breaks here` comments at the three spots I suspected, so my prompts could point at a specific line instead of saying "the hints are wrong."

**A suggestion that was correct**

I asked it why the same guess produced two different hints on consecutive turns. It told me the real cause was **not** in `check_guess` at all — it was [app.py:158-161](app.py#L158-L161), which cast `st.session_state.secret` to a `str` on every even-numbered attempt. That made `guess > secret` throw a `TypeError`, which the `except TypeError` block silently caught and retried as a **string** comparison, where `"9" > "50"` is `True` because ordering is alphabetical.

I verified it two ways before touching anything. First I pulled the pure functions into a scratch script and printed the actual returns: `check_guess(9, "50")` gave `('Too High', '📈 Go HIGHER!')` while `check_guess(9, 50)` gave `('Too Low', ...)` — the same guess, two different answers, exactly the symptom. Then after the fix I added `test_single_digit_guess_below_secret_is_too_low` and `test_same_guess_always_gives_the_same_outcome`, ran them against the **original** code from `git show HEAD:app.py`, and confirmed they failed there before passing on my version. A test that passes on the broken code would not have proven anything.

**A suggestion I did not accept as written**

When I asked it to fix the `TypeError`, its first instinct was the obvious one: make `check_guess` defensive by coercing both arguments at the top.

```python
guess = int(guess)
secret = int(secret)
```

That is not wrong exactly — the tests would go green — but I rejected it, because it fixes the *symptom* at the wrong layer. The caller in `app.py` would still be corrupting the secret's type on every even attempt, and `check_guess` would just be quietly cleaning up after it forever. The next person to read `logic_utils.py` would have no idea why the coercion was there. I wanted the mess deleted, not absorbed.

So I changed the approach: I removed the `str()` cast from the caller in `app.py` and deliberately left `check_guess` with **no** type handling at all, so a bad type now raises loudly instead of guessing. To prove that was a real decision and not just a preference, I wrote `test_string_secret_raises_instead_of_comparing_as_text`, which asserts `pytest.raises(TypeError)` on `check_guess(9, "50")`. If anyone reintroduces the coercion, that test goes red.

One smaller thing worth recording: the AI also wrote cross-file comments referencing `app.py:36` and `app.py:158`, but its own edits had already shifted those line numbers, so the references were wrong the moment they were written. It caught and corrected them, but it taught me not to trust line numbers in comments — they rot as soon as the file changes.

---

## 3. Debugging and testing your fixes

My rule was that I did not get to call a bug fixed until I could **show it failing first**. The trap with these two bugs is that the game never crashes — it just lies to you — so "it looks right when I play it" is weak evidence. Before changing any code I copied the pure functions into a throwaway script and replayed the app's exact control flow without Streamlit, which gave me printable evidence: with the secret at 50, guessing `9` returned `Too High` on attempt 2 and `Too Low` on attempt 3. That contradiction was the thing I needed to make go away.

The test I lean on most is `test_same_guess_always_gives_the_same_outcome`:

```python
def test_same_guess_always_gives_the_same_outcome():
    assert check_guess(9, 50) == check_guess(9, 50) == check_guess(9, 50)
```

It is almost embarrassingly simple and it does not even mention strings or types, but it captures the actual user-visible complaint — "the game keeps changing its mind" — rather than the implementation detail. `test_single_digit_guess_below_secret_is_too_low` and `test_three_digit_guess_above_secret_is_too_high` back it up by pinning the two specific numbers where alphabetical and numeric ordering disagree (`"9" > "50"` and `"100" < "50"`), since a test using 60 and 40 would pass on the broken code by luck.

The step that actually convinced me was running the new tests against the **old** code. I pulled the original `check_guess` out with `git show HEAD:app.py` and checked each new assertion against it: all five failed, which proved the tests were testing something real. Then on the fixed code the full suite went from `3 failed in 0.02s` (everything erroring on `NotImplementedError` because `logic_utils.py` was still stubs) to `9 passed in 0.02s`. Finally I ran `python -m streamlit run app.py`, confirmed the app boots with no exceptions in the log and serves normally, and played a round with the Developer Debug Info panel open so I could see the secret and watch each hint point toward it instead of away from it.

AI helped most with test *design*, not test *writing*. Writing these three assertions is easy; knowing that `9` and `100` are the interesting inputs required understanding why string comparison disagrees with numeric comparison, and that came out of the explanation I got when I asked why the same guess flipped. It also pushed me toward `pytest.raises(TypeError)` as a way to lock in a decision — the test exists specifically so that nobody "helpfully" adds `int()` coercion back into `check_guess` later.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
