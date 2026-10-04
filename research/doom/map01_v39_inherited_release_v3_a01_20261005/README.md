# V39 inherited release barrier × ExecutorV3 A01

## H / T / D / C / U

**H.** If an expiry owner has applied `KeyRelease` but is blocked before publishing its per-key owner record, the V39 bridge's `execute()` final drain runs too early. ExecutorV3's later inherited `release_all()` can verify neutral owner state and publish terminal status without publishing that pending per-key receipt. A final-drain wrapper around the inherited method should publish the record before terminal, without duplicating a no-op release edge.

**T.** On the pinned current-main coast/session source chain, run one controlled paired fake-display schedule. Admit F8, let lease expiry apply the fake physical up, block the owner's `sync()` before record publication, let `execute()` exit and queue ExecutorV3's `release_all()` barrier, then unblock the owner. Compare inherited-only behavior with a wrapper that delegates to inherited `release_all()` and drains owner records in `finally`. Capture owner records, bridge events, terminal, and final fake/bridge state.

**D.** The control should produce zero bridge up receipts while reaching one verified `expired` terminal and empty state. The wrapper case passes only with exactly one context/actuation-matched `CONFIRMED_PHYSICAL_UP` before the same verified terminal, no second per-key edge from the final no-op release, and empty state. Any timeout, mismatch, duplicate, or non-neutral state fails the probe.

**C.** The barrier forces a specific interleaving. Both arms use the repository's fake Xlib owner harness; only the wrapper arm drains after the inherited final release. The `execute()` body is an explicit test seam to control when expiry is raised. The current-main coast class and its session inheritance are loaded from the frozen source snapshot, and method resolution is checked at runtime.

**U.** This is one synthetic schedule, not real X11/OS input, a game, application consumption, useful feedback, recovery efficacy, latency, safety, or live allocation. `session_v4` capture behavior and owner imports are inert/stubbed; the inherited `session_v5.Backend.release_all()` implementation and current coast/session class chain are the source under test. It establishes a scoped receipt-order result only.

## Result

`PASS_SCOPED_FINAL_DRAIN`: inherited-only control emitted zero contextual up receipts; the final-drain wrapper emitted exactly one before terminal. Each arm produced two owner-release records (`expired`, then the inherited final `release`), one verified `expired` terminal, and empty fake physical and bridge-held sets. The no-op final release generated no duplicate per-key measurement.

Current main was `dccf55e264f434ca27f2948fe53be09919047819`. The nine frozen implementation files and their Git blob/SHA-256 identities are in `SOURCE_LOCK.json`. `audit.py` verifies retained raw output and source identity without executing the candidate. Reproduce with:

```sh
python3 run_once.py
python3 audit.py
```

`COMMANDS.txt` gives the exact retained runtime commands; `SHA256SUMS.txt` covers the package, and the auditor checks it read-only.

Runtime used for the retained run: CPython 3.12.14 on macOS 27.0 arm64. Docker Engine reported 29.4.0, but `docker image ls` failed while reading its content-addressed store (`operation not supported`). No container was launched and that engine failure was not retried; this construction probe ran on the host instead.
