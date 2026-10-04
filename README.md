# V39 post-execute owner-cleanup drain race A01

## H/T/D/C/U

**H.** When `Backend.execute()` returns and its final drain observes no owner release record, InputOwner can subsequently complete expiry cleanup before ExecutorV3's terminal state query. The aggregate owner state can then be empty while the per-key release receipt was never emitted and the bridge's held ledger remains stale.

**T.** Frozen PR #7805 head `15d56feea35bc6d7c4b499bbaa63e3bb0762ae6c`; candidate owner blob `82d3881dd4064f58e847420bb336a70cd84ee307`, candidate bridge blob `ee1220cdc3d93d96aa1051c072ca7dceeb59c35d`. Current-main dependencies are pinned in `SOURCE_LOCK.json` at `aa2e4b623b2f4ccdcbc8e294535bab09c0092f30`. Container `python:3.12.11-slim`, image ID `sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f`; `--network none --read-only`.

**D.** `RESULT.json` records the raw deterministic barrier run: at bridge drain there were zero owner records/release rows and bridge held `F8`; after the barrier opened, owner appended one `reason=expired` per-key receipt and physically released the fake key. ExecutorV3 terminal was `expired` and aggregate `release.verified=true`, while published per-key receipts stayed zero, bridge held `F8`, and its record cursor stayed zero. Exit 0.

**C.** Repository fake display and real ExecutorV3/candidate bridge/owner code. The test deterministically controls the owner's focus-check scheduling boundary. No real X server or OS input.

**U.** No claim about race frequency on X11, application/game effect, useful feedback, recovery, latency, live MAP01, or Issue #59 completion. This is a telemetry/bridge-ledger lifecycle counterexample only.

## Reproduction

From this directory:

```sh
docker run --rm --network none --read-only \
  --mount type=bind,src="$PWD",dst=/work,readonly -w /work \
  python:3.12.11-slim python probe.py
```

`RESULT.json` is the saved stdout from the successful run. `SOURCE_LOCK.json` identifies every vendored input by upstream Git blob SHA and SHA-256. `audit.py` is intentionally raw-only: it reads the saved JSON and locks, but imports no tested module.

## Disposition

`REPRODUCED_SCOPED_GAP`. This does not prove the latest PR #7805 head has the same behavior; it tests the exact frozen head above. The independent review comment on #7805 records that newer head `32686927ce6b07a035beb4c0297171a1f951c6c6` independently fails its expiry-terminal receipt regression on Windows/CPython 3.11.9. That is corroborating but distinct evidence, not substituted for this run.
