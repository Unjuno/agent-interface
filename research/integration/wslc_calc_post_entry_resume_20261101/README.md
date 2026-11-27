# Fresh-owner continuation after Calc post-entry yield

This follows the [post-entry context-stop probe](../wslc_calc_post_entry_context_stop_20261101/README.md). The fixed Calc task enters 731/864, then the harness overlays the reviewed context after the entry program completed. The original compiled graph yields SAFE_YIELD with the entry effect pending. The harness removes its own overlay, closes the original owner, creates a distinct owner, checks a fresh capture against the fixed cell and context references, and permits at most one separately guarded Ctrl+S. It never replays entry or changes the original receipt into success.

| Allocation | Result after context removal | Recovery Save | Persisted document | Final X state |
|---|---|---|---|---|
| l01 | First fresh capture still showed black context pixels; failed closed before mint/input. | None | Not recorded | No keys/buttons down |
| l02 | A bounded two-second passive re-observation loop was added; its first capture already matched. | One guarded Save, verified release | Independent FODS parse: exactly 731/864 | No keys/buttons down |

l01 is retained as a failure, not retried under the same ID. Its original entry execution has a verified release, but its original close receipt and saved document were not retained; the fresh owner closed without attempting input and final X state was neutral. In l02 the original and fresh owner close releases were recorded as neutral and distinct session IDs were verified. The original compiled receipt still says SAFE_YIELD / effect_unavailable. A successful later Save and independent file parse are separate evidence, not retroactive graph success. The l02 first capture matched, so the result does not show that waiting caused recovery or that delayed repaint is handled reliably.

Each run used gpt-6.1-sol requested low, two calls, 25,779 input tokens (20,352 cached subset), 140 output tokens, private Xvfb/Calc, 1 CPU / 1 GiB and no container network. These are individual observations, not a performance comparison. Cached input is already included in input.

`public.zip` retains both frozen candidates, conditions, observations, usage, action receipts, saved bytes where present and cleanup evidence. `audit.py` checks the pinned archive and source/candidate hashes, the overlay and cell screenshots, distinct model sessions, one original entry per run, no fresh input on failure, one guarded Save without text on success, independent FODS parsing and final X state. Run without Python optimization and with Pillow. Private protocol journals and host path-bearing launcher commands are omitted and not independently audited.

This is a fixed known-value pixel fixture with test-controlled overlay removal and caller-scripted continuation. It does not establish recovery after mid-keystroke failure, arbitrary partial effects, persistent obstruction, general recognition, robust latency, MAP01 completion or project completion. Issue 57 remains open.
