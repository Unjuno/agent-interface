# Issue #3548 attempt 01 — STOP_BEFORE_ROUTE_CALL

This predecessor failure is preserved; the fresh successor allocation is
`evidence/20260920-orbstack-route-unit-02/` and does not replace this record.

- Source main: `987d792b4b5d5075335d75036b924c190a411fa9`.
- Image: `issue-3548-route-unit:20260920`,
  `sha256:0e35cdb51a82e59d359ec09b85ce835d9217a1eab65b68ce1871c9b0a85014c9`.
- Retained OrbStack container: `issue3548-route-unit-01`, ID
  `87801bb9d832055e2d2f13c0140fc3aceb3024662adf35cebdead2c0d2043092`;
  exit 1, network `none`, read-only root.
- Failure occurred in under 0.4 seconds, before Xvfb/fixture startup and before
  all three transports: `ModuleNotFoundError: No module named 'runtime'` at
  `from runtime.cli_v1.observe import observe`.
- API route calls: 0. CLI route calls: 0. MCP route calls: 0. Model calls: 0.
  Input actions: 0. No route verdict can be inferred.

The entry script's directory, rather than `/repo`, was initially the Python
import root. The successor adds `/repo` explicitly, freezes its runner/auditor
commit before launch, and performs a separate allocation. The failed container
and exact error remain available in the linked Issue #3548 record.
