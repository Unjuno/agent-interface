# Scorer endpoint readback type repair A03

## H/T/D/C/U

- **H:** Candidate `5b4a563b5c3f6a70a063a98c7281a8bd6ce71eb0` compares the post-snapshot `get_episode_time()` value to an acknowledged integer tic using equality alone. Python therefore lets `11.0 == 11` and `True == 1` qualify malformed readback values and retain scores. The API documents `get_episode_time()` as returning `int`; the strict check protects the candidate's endpoint contract against malformed or substituted values.
- **T:** Add one test with a valid integer control already covered by the suite, plus float and Boolean readback aliases. The fix must keep the integer case qualified and make both aliases fail closed with no score values.
- **D:** PASS requires the new regression to fail on the pinned parent for both aliases, then pass on the candidate; all existing endpoint-composition tests pass; no production API beyond the exact readback check changes.
- **C:** Real ViZDoom may always return integers. This is a defensive candidate-contract correction, not evidence of malformed values from ViZDoom.
- **U:** Stub-only construction evidence. No game, model, GUI, scorer, input, recovery, task effect, or live allocation was exercised.

## Source and test identity

- Defect reproduction head from PR #7685: `5b4a563b5c3f6a70a063a98c7281a8bd6ce71eb0`.
- Corrective branch base after refreshing PR #7685: `0f41da2e8f460477bf8d97733785547adb7b4a9d`; this force-updated parent retains the equality-only defect and was merged before reapplying the narrow correction.
- Parent `checkpoint_candidate.py` SHA-256: `c48c1a734ae32505d7adf000028e618b2d0cfe73a4aa969892b8aada6a6407f5`.
- Corrected `checkpoint_candidate.py` SHA-256: `37387861339edf94401068cb08b2ca48e922ddc16d8d373c8b3e504816549c96`.
- Corrected `test_candidate.py` SHA-256: `a4516ce54656e50c97f5610aacee5ef9cad0ee82e7bdde09776d83217016f8ff`.
- Runtime: bundled CPython 3.12.13.
- API reference: [ViZDoom `DoomGame.get_episode_time`](https://vizdoom.farama.org/api/python/doom_game/), documented return type `int`.

## Verification

The TDD regression first failed on the parent candidate for both `float` and `bool`: both returned `REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING` instead of `UNKNOWN`. After the production guard required `type(tic_after_read) is int` before equality comparison, the focused regression passed both cases. On the refreshed stacked head, the full scorer endpoint composition suite passed 16/16.

`py_compile` passed for the candidate and its test module; `git diff --check` passed. The existing positive one-tic and multi-tic controls remain green. This correction only prevents non-integer endpoint aliases; it does not establish scorer freshness, useful task feedback, or live controller behavior.
