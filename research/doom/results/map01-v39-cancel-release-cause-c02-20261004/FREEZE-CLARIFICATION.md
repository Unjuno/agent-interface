C01 was executed against `input_owner_v10.py` from source commit `8094af4631fc7bc5d92990e5151d5e89477ee39f`. Its source blob is `341b3c01649943ddaad5f28431a792c4889cc36e` and SHA-256 is recorded in `FREEZE.json`.

C02 executes only `input_owner_v12.py` plus the frozen two-case owner-thread harness. The transition/backend/session v14 wiring was added after that run and checked separately by `AUDIT-01.json`; no claim is made that C02 executes MAP01 v14 or the historical `ExecutorV12._publish_release` chain.

WSLc was not used because a different study's container was running at the pre-run check. Local CPython 3.11.9 with fake Xlib was sufficient for this deterministic owner-thread construction. The failed adjacent current-main `test_session_map01_v13.py` check was an existing Windows incompatibility: `main_thread_scorer_polling_v1` calls `select.select` on a pipe and raises `OSError [WinError 10093]` before the test can finish. No retry was made.
