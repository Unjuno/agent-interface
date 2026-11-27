# Calc provider-wait stale-source and task-effect experiment (2026-11-03)

Runs r16 (normal Python) and r17 (`python -O`) exercise a synthetic App Server provider wait. While the first response is pending, Fake X Calc metadata is reobserved under a changed Calc title cue. The old request is refused with `CALC_REVIEW_SOURCE_STALE` before input. A bounded fresh attempt then completes two transitions; both releases are verified and owner close confirms release. The joined provider ledger records two attempts and 90 input / 20 output tokens.

The fixture uses a 5,000 ms capture-freshness limit for minted aliases, the API maximum, and observes again after preparation immediately before minting. This avoids conflating a stale reviewed sequence with alias capture expiry. The exact resolved point diagnostics are retained in `calc-provider-wait-evidence-20261103-r16.zip` and `r17.zip`.

For the task-effect check, Fake Calc writes the FODS fixture only when it receives Ctrl+S after both expected entries (`731`, `864`) have been accepted. The test no longer writes the artifact after close. After input release and owner close, the parent independently parses the generated artifact and verifies those cell values. This is a task effect within the synthetic Fake X application; `live_calc_task_effect` remains false. It is not evidence from a live Calc process.

Each ZIP preserves the run's original files and internal SHA-256 manifest. The bundle index records each archive digest; r16/r17 raw-member hashes and archived manifest checks passed. Earlier r08/r09 inserted an artifact after close and must not be used as task-effect evidence. Earlier failed attempts are retained separately in their archives. No live provider, WSLc, MAP01, or efficiency comparison is covered.
