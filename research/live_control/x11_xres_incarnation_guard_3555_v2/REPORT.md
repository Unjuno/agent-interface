# Formal report — Issue #3575 allocation 04

## Decision

`PASS_PROVENANCE_COMPLETE_XRES_GUARD_REPRODUCTION` for one fresh allocation, based on a pre-run exact-source/image audit, a one-shot container execution, and independent reconstruction. The result is narrowly scoped to the pinned linux/arm64 image and private Xvfb. The guard remains research-only and is not promoted to the default runtime.

## Frozen experiment

The hypothesis and H/T/D/C/U, decision rules, no-retry limit, exact main SHA, 17-file source manifest, image digest, architecture, network/rootfs/mount policy, Xvfb setup, and Python/Xlib/Pillow versions are in `allocation-04/FREEZE.json` and `allocation-04/source_manifest.json`. Before Xvfb or fixture start, a separate read-only container auditor recomputed all 17 source hashes, manifest hash `09344719083872cbad3ea063ecd6258308ba2f831c4b18df7c716985bf0ad410`, freeze hash `f3b4055f11795e962eb1bf59cf83de7c9cd3b5daa0206b6814ad560e4090b440`, and the pinned image ID. Candidate import smoke and seven guard unit tests passed in the same pinned image before the single formal invocation.

During packaging, `main` advanced from the frozen `c3abca57` to `befe9212` (seven commits). A GitHub compare showed the only changed tested backend source was `runtime/backends/x11_v1/backend.py`: it adds `=` and `*` text-symbol mappings. This allocation emits pointer clicks only and uses no text operation, so that later change is outside the exercised path. The PR is based on current main; the c3 source freeze, raw, and result are not rewritten.

## Observation

Allocation ID: `issue3575-xres-guard-formal-04`.

- p1 XID `2097152`; p2 XID `2097152`.
- p1 PID/start ticks `22/368714`; p2 `25/368720`; XRes server-reported owner matched each fixture process.
- Geometry was `[80,80,240,160]` for both clients.
- p1 client-window bytes were captured while p1 was alive at monotonic ns `3687198035010`. p1 exit was observed at `3687201633457`; p2 started at `3687206790148`. Thus the p1 byte capture precedes p1 exit and p2 creation.
- The separately retained p1 and p2 buffers were each 153600 bytes and independently hashed to `3b80132900d7ab9ce6a54b7f01b7fa0d345dd50aafb69135b740ae655c3aba0c`; byte equality was true.
- Old alias decision: refused, reason `PROCESS_INCARNATION_MISMATCH`; bridge click invocation `false`; backend emissions `0 -> 0`; p2 effect `[0,0,0] -> [0,0,0]`.
- Conditional fresh alias control: permitted for `SAME_PROCESS_INCARNATION`; dispatch completed; emissions increased by 3; independent p2 effect `[1,212,118]`; release receipt verified with no keys or buttons held.
- p1 and p2 cleanup receipts show observed exit code 0; bridge close was recorded. Six PNGs match raw byte-size and SHA-256 entries.

## Independent audit

`allocation-04/independent-audit/audit_rawonly_3575.py` imports none of the candidate guard, bridge, runner, or fixture. It reconstructed the decision from immutable raw in a separate network-disabled, read-only-source container and passed 10/10 corruption controls, including missing pre-exit p1 bytes and p1 capture after p1 exit. The supplemental artifact auditor independently checked timing, byte hashes, release, cleanup, and all six PNGs. Outputs are in `independent-audit/formal-04/`.

## Failed/held allocations retained

Allocation 01 stopped before fixture start on a runner import-path error. Allocation 02 started p1 but bridge construction failed because `capture_artifacts.py` was absent from the source bundle; no stale guard or input was attempted. Allocation 03 produced a candidate PASS, but audit review found that it read the reused XID twice after p2 existed, so the claimed p1/p2 pixel equality was not supported. Its raw and audits remain byte-for-byte unchanged; `formal-03/AUDIT_REASSESSMENT.md` records `HOLD_AUDIT`. Allocation 04 independently captures p1 bytes before exit and is the first allocation that satisfies that requirement.

## Limits / next work

This verifies one local fixture allocation, not resistance to a concurrent owner-change race between identity check and actual native emission. A separate hypothesis would be needed for such a TOCTOU test. The result does not cover remote X11, other servers, production compositor behavior, general task reliability, or default-runtime security.
