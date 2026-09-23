# Direct lineage freshness tests — Issue #2428

## H/T/D/C/U

- H: direct public lineage dispatch tests should prove stale observation and binding are rejected before dispatch while current lineage delegates exactly once.
- T: add three unittest cases using a deterministic digest-bound program/receipt/sidecar fixture and a counting dispatch stub.
- D: `runtime/cli_v1/test_lineage_freshness.py`; current main `runtime/cli_v1/lineage.py` implementation.
- C: source-level test result only; no live desktop/model/task or performance claim.
- U: caller-supplied current values and composition with live focus/target invalidation remain unknown.

## Result

Container-compatible local unittest run: **3 tests passed**.

- stale observation: `STALE_OBSERVATION`, dispatch calls 0
- stale binding: `STALE_BINDING`, dispatch calls 0
- current lineage: delegated exactly once

This PR adds coverage only; it does not change the already-landed implementation.
