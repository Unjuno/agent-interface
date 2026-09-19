# CLI lineage freshness gate — Issue #2428

## H/T/D/C/U

- H: public lineage dispatch must reject a receipt whose observation sequence or binding revision differs from the caller's current values before dispatch.
- T: add explicit current observation/binding equality checks after existing lineage validation; test stale observation, stale binding, and valid current delegation with a counting dispatch stub.
- D: `runtime/cli_v1/lineage.py` plus `test_lineage_freshness.py`; local Python unittest in an isolated workspace.
- C: source-level safety result only; no live desktop/model/task or runtime performance claim.
- U: live authority of caller-provided current values and composition with actual focus/target invalidation remain unknown.

## Result

Local unit run: **3 tests, 3 passed**.

- stale observation: typed rejection `LINEAGE_STALE_CURRENT_OBSERVATION`, dispatch calls 0
- stale binding: typed rejection `LINEAGE_STALE_CURRENT_BINDING`, dispatch calls 0
- current lineage: delegated exactly once

The change preserves all prior internal digest/lineage checks and adds the missing caller-current equality gate.
