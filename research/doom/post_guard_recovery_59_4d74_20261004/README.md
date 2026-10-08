# Post-guard recovery preparation: actual WSLc/Windows planner transport

This is an additive transport/setup archive for #59. It does not demonstrate game recovery, useful task effects, physical release, cancellation latency bounds, human tempo, or a completed roadmap. No existing formal/game allocation was reused.

## Retained outcomes

- Dependency preflight01: the existing cached Chromium image lacks ViZDoom, wslpath, node and codex; its hardcoded /mnt/c Windows node path is absent. Xvfb/Pillow/Xlib/numpy exist. These are observed dependency facts, not runtime enforcement proof.
- Image build01 failed because FROM sha256:... was parsed as a repository. Preserve the original error. Unfrozen setup build02 checks the cached base tag identity and installs ViZDoom1.3.0. Image94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378. Dependency preflight02/native import pass; no game instance was created.
- initialize01: real Windows Codex app-server initialize/initialized crosses a private network-none WSLc mounted-file boundary. No thread/turn/provider ran. This alone is not asynchronous qualification.
- First planner-source materialization stopped on a nonexistent client-v2 test filename. Corrected source materialization uses actual main files. Existing planner suite first has9/10 PASS, one Windows-only literal path expectation FAIL. Separate portable expectation suite10/10 PASS; production/original test unchanged. Fake-client tests are not provider evidence.
- relay-construction01: explicit Windows fake peer/current-source client+planner/private WSLc first interrupts a pending turn, then host PermissionError STOP. Original source snapshot and first raw remain. Request5 is readable after termination; the exact OS sharing cause is not established.
- relay-construction02: distinct frozen setup after a bounded2s PermissionError read wait was added. Eight requests/thirteen responses; interrupted refusal, completion-after-interrupt refusal, and distinct fresh continuation pass. No sharing error occurred, so effectiveness of that added wait branch is unexposed. Four post-run copied-record corruption checks reject. No provider/game/input.
- real-relay-construction01: first/only frozen actual-provider transport construction. Two requested gpt-5.6-luna/low turns on one ephemeral read-only thread: actual started/interrupt/terminal interrupted, stale result ineligible; distinct fresh turn completed with exact marker. Six requests/forty-two responses reconcile byte-for-byte and with client journal. Three post-run negative controls reject. Guest/host exit0/readers terminal; client.close terminates the relay proxy(exit-15), not graceful EOF proof.

## Cost and scope

The fresh second turn emitted input8682/output24/total8706, cached/reasoning0. The interrupted first turn has no attributable usage receipt. Whole-episode token and monetary cost remain UNKNOWN. Two requested turns do not prove two billed invocations. Do not add cumulative and last usage receipts. No observed tool items. Eight-point-eight-four-four seconds is the observed host setup/run envelope, not cancellation latency.

CPU1/512MiB and uid65534/networknone/sourceRO are requested arguments. Original swap/cgroup warnings remain; effective resource enforcement is unproven. All runs used private namespaces. No GPU, game, X11 session, GUI input, scoring or task-effect experiment occurred in this archive.

## Provenance and reproduction

Production source snapshots come from main a2f6b60ac84300d45beb82c7cf5a6e06cfc7c456. Source/CLI SHA and actual argv appear in freezes. Run scripts contain historical absolute host paths and outputs are exclusive; they require deliberate adaptation and a fresh authorized allocation, not blind rerun. Real CLI executable/credentials and images are not bundled. Image build networking is not asserted disabled. Preserve source snapshots and first outcomes.

fixture-materialization.json identifies already-public main fixture-v2 save/source and the matching WAD. Those binary assets are intentionally referenced rather than duplicated here; they were only read/copied, never loaded into a game. SETUP_FILES.json is the earlier41-member setup checkpoint; FILES.json covers the final archive. PREPARATION.json is an unfrozen earlier draft, not a preregistration overriding later FREEZE files.

Post-run auditors audit saved records; they are not independently authored full protocol authorities. audit_relay.py / audit_real_relay.py can inspect local saved results, with the real audit requiring the pinned host CLI for its hash check. Actual provider usage may remain unknown. A future game recovery allocation still needs current qualified per-key release instrumentation, an actual host-compatible image mapping, a post-invalidation decision slot, independent useful scoring and a dedicated live lane. Parent#59 remains open.
