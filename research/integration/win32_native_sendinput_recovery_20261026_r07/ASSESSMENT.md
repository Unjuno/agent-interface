# R07 assessment — recovery passed; continuation harness failed before task input

R07's first phase passed the R06 recovery gate. The held SHIFT input was recovered in 17.142 ms, the exact old fixture exited with code 0, and a second fixture had a distinct PID and target generation.

The old-generation focus-only probe then stopped at program-schema validation because the probe omitted the required single `release_all` operation. Its raw response was `invalid_request`, `input_dispatched=false`, and session `call_count=0`; no task action was attempted and the new fixture effect file remained absent. Therefore R07 does not qualify old-generation refusal or task success.

The final cleanup also recorded task-fixture exit code 1. Inspection of the frozen R07 runner confirms its cleanup path loads `run/fixture/meta.json` even though the continuation fixture metadata is `run/task-fixture/meta.json`; it sent the close request to the already retired window, timed out, then terminated the fresh fixture. This cleanup defect is preserved. The next trial corrects the stale probe to include `release_all` and closes the current `meta_path`; it uses a distinct R08 attempt ID.

The independent audit verifies the R07 first outcome and all raw/pretrial hashes. R07 is an immutable failure and was not replayed. No WSLc, Docker, AppServer model, or continuation task input was used.
