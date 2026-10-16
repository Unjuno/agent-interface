# #5156 owner-key-up caller/worker bracket construction T4

## H / T / D / C / U

**H — hypothesis.** On current main, the real `InputOwner v10` worker thread plus the `InputOwner v11` caller wrapper can produce a release call whose caller-clock interval encloses the worker-thread XTest key-release request and the following sync return. A separately implemented raw-only auditor should recover that ordering and reject identity, ordering, terminal-state, and authority mutations.

**T — test.** Freeze current main `97afcb82f90616589801a256893f886010ed6d27`, `input_owner_v10.py` Git blob `341b3c01649943ddaad5f28431a792c4889cc36e` / SHA-256 `ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b`, and `input_owner_v11.py` Git blob `842071284156d3ccc647f47135ee62a9e512cb56` / SHA-256 `4f6b61026117d4d9be8a973c65d491fe8a9b0ebbc90bd98c0738cd0aac09821c`. In one host-CPU candidate invocation, import and execute the frozen owner/wrapper code with only Xlib replaced by a deterministic in-memory test double; admit one key, explicitly release it, capture the fake XTest request and fake sync return on the owner thread, then retain the wrapper receipt and terminal fake-key state. Invoke the separate standard-library auditor once after candidate exit 0. No retries or substitutions.

**D — decision.** `PASS_SYNTHETIC_OWNER_BRACKET_JOIN_SCOPED` only if exactly one occurrence has the same owner, intent, operation, and key across the three raw sources; `caller_start <= owner_release_request <= owner_sync_return <= caller_return`; interval arithmetic reconciles; the release leaves the fake key-up state; the owner thread terminates; all authority flags remain false; and eight predeclared raw mutations are rejected by the auditor tests and/or final audit.

**C — counterfactual.** A positive result shows that the current Python queue/owner-thread call path and its telemetry wrapper can be joined under this deterministic fake-Xlib schedule. The fake XTest and sync do not implement an X server. This construction gate requires neither Docker nor an X display; it does not replace the separately gated Xvfb allocation.

**U — uncertainty.** No real XTest request, XSync server processing, XQueryKeymap witness, continuous physical occupancy, application consumption, cancellation, multi-key ordering, useful feedback, recovery efficacy, MAP01 outcome, latency distribution, human tempo, or cross-domain transfer is established. The synthetic occurrence ID and joined owner identity are attached by the test harness, not emitted by the current runtime.

## Environment and commands

- Host: Windows 11, CPython 3.12.10, `perf_counter_ns` = monotonic `QueryPerformanceCounter()`.
- Container: not used. Docker Desktop service was Stopped/Manual; 105 Docker CLI processes were visible and the shared container inventory was unknown. No service, process, image, or container was changed.
- Construction tests (before candidate): `python -B -m unittest -v test_audit.py`.
- Candidate (exactly once): `python -B run_candidate.py --out results/host-t0-01/raw.jsonl`.
- Independent audit (exactly once, only after candidate exit 0): `python -B audit_raw.py results/host-t0-01/raw.jsonl results/host-t0-01/audit.json`.

The three files under `results/host-t0-01/` are the first outcome. Do not rerun or replace them. This record is construction-only and does not authorize or consume #5156's formal X11 slot.
