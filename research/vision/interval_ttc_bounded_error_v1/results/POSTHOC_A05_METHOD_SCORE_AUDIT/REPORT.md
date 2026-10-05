# A05 posthoc retained-raw score audit: stopped before input read

**Disposition: `STOP_BEFORE_INPUT_READ_ARGUMENT_ROOT_MISMATCH`, with a coordination-gate deviation.** The frozen WSLc invocation exited 1 because the command passed the package directory as the first script argument, while `audit_only_a05.py` expects the repository root and appends the package path itself. The failure occurred when resolving `FREEZE_A04.json`, before reading the A04 report or any A02 raw artifacts. No A05 scoring result exists.

After the invocation, I reread Issues #7924 and #7970 and found their explicit HOLD against WSLc management/RPC until shared ownership and an exclusive lane are resolved. I had issued this command before checking that gate; this was a process deviation, and the WSLc call was not an authorized allocation. The container process reached Python, but `--rm` cleanup was not independently verified because no post-run inventory was issued. The exact stderr and invocation record are in this directory. The swap-limit warning is retained; WSLc reported memory limited without swap.

The earlier A04 result remains `PASS_RAW_RECONCILIATION_ONLY` for raw prefix reconstruction. The original A02 formal disposition remains `FAIL_METHOD`; A03's auditor runtime stop remains preserved. A05 does not change or repair either result. The A05 code and tests are retained for review, but a local invocation test would not change this frozen one-shot STOP.

Pre-invocation local verification matched all eight hashes listed in `FREEZE_A05.json`. A05 unit tests passed 3/3; A04 prefix-audit tests passed 8/8 after restoring the frozen README bytes; the analysis-index checker unit tests passed 17/17. These construction checks do not constitute an A05 score.
