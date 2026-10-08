# #5037 formal and corrected audit addendum

## Formal invocation

One frozen invocation completed on OrbStack Docker context, local `python:3.12-slim-bookworm` image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, Linux/ARM64, CPython 3.12.14. Exit 0. The runner retained seven isolated rows and 32 manifested evidence files. Broker source remained blob `5734f54f318db9ac5e96b2bed6f6bed105ac39ff` / SHA-256 `e44822269b921aa6327563b27e48a6d8ef4ebe35a182f50de541cf66fce6199c`.

Observed: actual fake-child exit 0 -> broker 0/receipt 0; exit 23 -> broker 23/receipt 23; timeout -> typed `HOST_BROKER_SUBPROCESS_TIMEOUT`, broker 1, no response bytes; missing executable -> typed `HOST_BROKER_EXECUTABLE_UNAVAILABLE`, broker 1, zero child calls; malformed instructions -> `InvalidInstructions` / `HOST_MODEL_INSTRUCTIONS_REJECTED`, broker 1, zero child calls; idle `--once` externally timed out at about 492 ms with no IPC outputs; queued `a-first`/`z-last` processed only `a-first`. All emitted receipts stated `authority_granted=false`.

The raw tree is `research/integration/broker_fake_child_boundary_4485_orbstack_successor_v1/formal01/`. `FILE_MANIFEST.json` SHA-256 is `5ae0e8e6dd5cf1d194cf4270f1dc210896e4e78e8fed09599d403177e7b8ad46`; `RESULT.json` SHA-256 is `ae09573149160bda321e10ff14483b9cd4690d5c472b4a630b4ebef6b7583a59`.

## Audit chronology and disposition

The first frozen independent audit invocation exited 2 with `FAIL_AUDIT`, `errors=["broker_source_hash"]`; the auditor incorrectly looked for a top-level freeze field instead of nested `target_source.sha256`. Its output is preserved unchanged at `research/integration/broker_fake_child_boundary_4485_orbstack_successor_v1/audit01/AUDIT.json`, SHA-256 `a69284a0a245723469ff740051907271c1f62795151abb4f83a9267a32fbb441`. It rejected 8/8 mutations but did not pass the registered baseline.

Fresh audit-only allocation #5047 corrected only this audit implementation and examined the immutable raw bytes in a separate offline, read-only ARM64 container. It returned `PASS_AUDIT_ONLY_RECONSTRUCTION`, 7 rows, errors=[], 8/8 mutations rejected, exit 0. Output `audit02/AUDIT.json` SHA-256: `007bcb4487f808b2eb62f1c4ed4bf71baee0bdc0c3915434ca142aeaa00b6d8f`. The corrected auditor independently checked manifest file identities/lengths, duplicated per-case results, IPC paths/content, request hashes, broker source digest, runtime/architecture, and semantic outcomes. No formal case or broker was rerun.

**Scoped disposition:** `PASS_BROKER_EXIT_CONTRACT_SCOPED` supported by the formal raw plus the distinct corrected audit-only reconstruction. Preserve the historical first-audit failure as a validator defect in the chronology; do not rewrite it. This says only that the unchanged broker's local fake-child subprocess boundary matched these seven registered outcomes on one OrbStack Linux/ARM64 image. It is not a live Codex/model/provider, authority, GUI/task effect, latency, product, or cross-platform claim.

## Collision and integration boundary

After #5037's formal execution, an independently registered #5036 plan was found for the same broad #5013 hypothesis on Docker Desktop/Linux/amd64. The #5036 Issue's last recorded comment says its formal output was not present at that time. The late discovery means these tasks were not selected with complete cross-task visibility; retain both histories as separate platform allocations, do not pool or label them a planned replication, and coordinate before any further run. Active research tasks were notified. No runtime source was modified.

All raw, the first failed audit, corrected audit, launch scripts, freeze records, hashes, and local checks are included in this additive evidence bundle. Merge is contingent on exact-head CI/review and successful GitHub readback of the full evidence.
