# Acknowledged update vs scorer-read status construction

## H/T/D/C/U

- **H:** If the native update call returns and advances the episode tic, but the following scorer read raises, the current emitter labels the update unavailable and omits the producer/update identity. This makes actual progress impossible to distinguish from an update failure in the retained sidecar.
- **T:** Run the focused regression against current `main`, then exercise the scorer's full focused module in a cached, network-isolated WSLc image with a read-only source mount.
- **D:** The regression must fail on current `main` and pass after the change. The emitted failure row must independently report `update_status=UPDATE_RETURNED`, `sample_status=UNAVAILABLE`, and retain the producer's tic interval. Update-call failures and no-advance validation failures must remain distinguishable.
- **C:** This verifies sidecar classification and identity in fake-game source construction. It does not measure engine freshness, cadence neutrality, useful feedback, input release, recovery, or gameplay.
- **U:** WSLc reports that the host kernel lacks swap-limit support; the run used one requested CPU and a 512 MiB memory cap, without claiming enforcement. No live session or input allocation was used.

## Result

Baseline source `research/doom/acknowledged_scorer_v1.py` at `54009330859258ae59c5cd555c89058c00b68c81` failed the regression: after `advance_action` returned and advanced tic 2→11, a `ValueError` from the scorer callback produced `status=UPDATE_UNAVAILABLE`. Exact focused test output and exit are in `out/construction01/red.txt` and `red-exit.txt`.

The repair emits separate update and sample statuses, stores producer identity before calling the scorer, and retains the existing sticky failure/no-retry behavior. The no-advance case is now classified as an acknowledged update with validation failure, while an exception from the update itself remains `UPDATE_UNAVAILABLE`.

After the repair, the full focused module passed all 11 tests in WSLc with the cached image `sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378`, `--pull never`, `--network none`, nonroot UID 65534, one requested CPU, and a requested 512 MiB memory cap. Raw output is retained in `out/construction01/wslc-green.txt`; command details are in `argv.json` and `FREEZE.json`.

This is a scoped source-construction PASS only. The earlier merged #7545 evidence and outcomes remain unchanged; the fix is a current-main follow-up, not a regrade or a live qualification.
