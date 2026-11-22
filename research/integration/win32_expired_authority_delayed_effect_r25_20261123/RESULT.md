# R25 — Native expiry, delayed effect and orphan recovery cohort

## Scope and frozen conditions

R25 froze three independent Win32 fixture attempts against main
`490d7bcb4d84927116112e5ff348cdeadfc489d6`. Each attempt allowed one standard
public action, with a 2 s authority lease, a fixture effect scheduled 6 s after
key-down, and (for a recovered UNKNOWN action) one fresh-session orphan
recovery with a 2 s late-input horizon. Retries and action replay were forbidden.
The frozen conditions and all attempt IDs are in `conditions.json`.

## All attempts

| Attempt | Outcome | Evidence |
|---|---|---|
| R25-01 | One action dispatched; source remained UNKNOWN/release-unconfirmed/replay-denied. The fixture recorded factual text `a` after lease expiry. A single fresh-session public recovery verified key-up, neutral readback, 2 s horizon, and exact fence clearing. Fixture closed. | `raw/trial-01/`, `raw/cohort-progress.json` |
| R25-02 | Stopped before dispatch because the exact fixture window was not foreground. The durable fence was clear; no source action response or dispatch exists. Fixture was closed using Computer Use and process absence checked. | `raw/trial-02/`, `raw/trial-02/setup-stop-disposition.json` |
| R25-03 | Not attempted after the frozen stop condition. | Frozen conditions; `raw/cohort-summary.json` |

The first R25 runner also raised an `AttributeError` in local scorer loading
after R25-01 had already dispatched. It did not replay the action or call
recovery. That defect and its retained failure are recorded in
`raw/runner-failure-r01.json`; the one permitted recovery was later performed
once by `recover_trial01_once.py` and its raw receipts are retained. The
cohort is therefore **stopped / mixed**, not a three-trial repeatability pass.
No success rate or reliability estimate is claimed. The R25-01 fact is useful
as one repeat of the R24 boundary; it does not erase the R25-02 setup failure.

## Interpretation and next work

R24/R25-01 show that the current public standard caller can leave an action
UNKNOWN while a delayed fixture effect occurs after lease expiry, and a
separate one-shot orphan recovery can later establish release, neutrality and
a bounded late-input horizon without promoting the old action or permitting
replay. R25-02 identifies a fragile setup requirement: the runner assumes the
target is foreground without raising the exact owned fixture first. This
pre-dispatch failure is preserved and was cleaned up without input.

Do not resume R25. A distinct prospective cohort may test whether explicit
Computer Use activation of each unique fixture makes the same protocol
repeatable; it must preserve any activation/preflight failure and stop before
dispatch if foreground identity does not match. This result does not satisfy
#57 efficiency, provider accounting, MAP01, Research Preview, or distribution
gates.
