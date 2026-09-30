# Guarded metadata-only presentation: local stage cost

The production fix is merged as #5520. This is a distinct first-run, local comparison of its synchronous presentation + MCP content-construction stage, using the same previously captured public guarded-observe report and 21,844-byte PNG. It performs no GUI, backend, public tool dispatch, relay or model call.

Frozen baseline source: 402e19ae6d2637af46577d67dfa45d4c6a6f2c70. Candidate source: 5527495b4e981d183478bec1acfd80eaeb02511a. PLAN.json was written before the sole run and binds the runner/source references/input hashes. All 2,000 timing rows remain in samples.jsonl, 1,000 alternating-order pairs; no warmup exclusions/retries. Outer execution exit 0; stderr empty.

The runner's outside-timing checks recorded identical final CallToolResult metadata and zero image blocks, with Base64 calls 1 baseline versus 0 candidate. These recorded checks supplement the earlier #5520 red/green + public-use evidence; the read-only timing auditor does not independently rerun those semantic checks.

| Stage metric | Baseline median | Candidate median | Median paired baseline-minus-candidate |
|---|---:|---:|---:|
| Wall time | 0.2322535 ms | 0.211314 ms | 0.018477 ms |
| Process CPU | 0.231475 ms | 0.210605 ms | 0.0184015 ms |

Candidate wall time was lower in 794/1,000 pairs. Wall paired differences by order: candidate first 0.0174715 ms, baseline first 0.019379 ms. These are repeated reads of one cached local file on an uncontrolled WSL host, not independent tasks/population samples or a calibrated uncertainty estimate. They are not end-to-end SDK/model speed, inference time, useful-feedback time or token/cost savings. Receipt acquisition/parsing, async thread scheduling, capture and transport are outside the bracket.

Read-only check: `python3 -O audit.py /absolute/path/to/this/directory`. Five changed-evidence controls reject missing row, wrong order, wrong encoder count, changed PNG and nonzero exit. The frozen allocation must not be re-executed to improve its result. Existing sources/results remain untouched.

integration-intake.json records the inspected current-source/Issue boundaries. The limited stage difference supports treating this fix as small internal work avoidance; it does not substantiate the broader speed goal. Priority remains fresh useful feedback and semantic-completion decision boundaries. This retained measurement is batched with the substantive #5539 admission repair. It was measured on the earlier WSL2.6.3/kernel6.6 environment; it is not a before/after WSL upgrade comparison. Use python3 -O verify.py to check the archive and recompute the data-only stage audit without executing its frozen measurement.
