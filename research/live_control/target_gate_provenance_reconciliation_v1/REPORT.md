# Target-gate provenance reconciliation

Decision: **`CONFIRMED_PARALLEL_ALLOCATION_PROVENANCE_CONFLICT`**.

No new X11/formal experiment was run. This is a read-only GitHub-evidence audit plus independent hashing of reachable Git source bytes.

## Lineage A — #965 A1 -> #969 A2

#965 froze task `TARGET-GATE-TOCTOU-20260917-001` with scientific SHA-256:

- `app.py` `301642cf59b5e577effe111c6331397a74dc49074fe8db7584f89bcf374ebe2b`
- `gate.py` `a21abd2075a522eebc41af0796f8fc2d2784e39b65320d3a0a4e617c8ffb96b0`
- `run_case.py` `504272d14d49f8b426d1b5165b0e4e2c54348f93825bf95540e3d824c5ff0d18`

A1 stopped after 9 complete rows with `STOPPED_OUTER_ORCHESTRATION_TIMEOUT`; it was not a 12-row scientific disposition. Fresh successor #969 used task `...-002`, explicitly retained the three scientific bytes above, used fresh IDs `a2-f00..a2-f11`, and reported 12/12 `PASS_TARGET_GATE_TOCTOU_EXPOSED_SCOPED` with RESULT_SUMMARY SHA-256 `80bd4050...`.

Repository search did not locate a separate Git-retained #969 A2 publication by its task ID, result digest or frozen scientific app hash. This is recorded only as `NOT_FOUND_IN_SEARCH_SCOPE`, not as proof that no evidence exists elsewhere.

## Lineage B — PR #968 / main

PR #968 was created at 08:54:48Z and merged at 08:55:40Z as main commit `592427d8f70efafed5819acec123f3fd0efa485b`, while #969 was created at 08:54:55Z and completed later.

PR #968's Git-retained audit declares—and independent SHA-256 over the actual Git blob content reproduces—different scientific bytes:

- `app.py` `30a00c4aebe8190606daa7d6c903447e5d7c4c58adb1fe92456544f075c0eef2`
- `run_case.py` `761df5ada785a025c80ac8e05ecb8c6fec17d964a9f40a76df45ae78684aeab6`

Its formal rows use `p01-stable/p01-swap` through `p06-*`, not #969's `a2-f*` IDs. Its `FORMAL_RESULT.json` is Git blob `0f98ecad...` and identifies task `TARGET-GATE-TOCTOU-20260917-001`.

## Consequence

The two PASS records may each contain useful science, but they are **not one byte-identical allocation lineage**. Current main's PR #968 cannot silently stand in for #969 A2, and #969 A2 cannot be used to explain PR #968's source/cases. A repair or replication must name an exact predecessor: PR #968/main or #965->#969 A2, or explicitly test both under a fresh allocation.

This audit does not rank the two results and does not rerun either experiment.
