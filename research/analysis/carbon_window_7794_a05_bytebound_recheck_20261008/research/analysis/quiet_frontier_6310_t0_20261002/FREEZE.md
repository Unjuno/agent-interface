# Issue #6310 T0 freeze — predicate-relative quiet frontier

Allocation: `QUIET-FRONTIER-6310-T0-20261002-01`  
Issue: https://github.com/Unjuno/agent-interface/issues/6310  
Main snapshot at intake: `c81e3d8ffebc7cbc2af971dfb7fb2d9b1ba1f7fe`; formal-preflight main: `ab43adce8141182f6bcfa76df469854b1ae11116` (+1 commit, Issue #59 X11 app-event evidence only; unrelated to this synthetic fixture).  
Runtime: Arch Linux WSL2 + WSL Containers 3.0.1; pinned `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64).

## H / T / D / C / U

- **H:** A finite method can certify only `QUIET_AS_OF_FRONTIER` for an explicitly complete set of event writers through a source-side frontier F. It cannot infer `SAFE_TO_ACT_AT(B)` from that certificate alone; an atomic source-version compare at B must independently reject a relevant F→B change.
- **T0:** Exhaustively adjudicate seven deterministic synthetic traces: complete quiet interval, relevant change before F, relevant change after F but before B, unregistered writer, sequence gap, epoch change, and irrelevant noise. Candidate emits scoped frontier disposition and distinct actuation gate. A separately authored auditor reconstructs output from raw fixture semantics and checks four corruptions.
- **D:** `PASS_METHOD_SCOPED` only if all seven rows match the independent oracle; only fully covered, same-epoch, contiguous, event-quiet A→F intervals return quiet; observed relevant changes are not quiet; incomplete writer/sequence/epoch coverage returns UNKNOWN; a post-F/pre-B mutation never authorizes actuation and is rejected by atomic version comparison; all four frozen mutations are rejected.
- **C:** A direct fresh state check at B may be simpler; a complete event-writer set may not exist in real GUIs. This finite method may mostly produce UNKNOWN.
- **U:** Synthetic finite traces only. No real GUI event-source completeness, clock translation, atomic compare-and-act backend, action authority, model behavior, safety, or performance is tested.

## Frozen semantics

The predicate is a Boolean versioned state. Interval A→F is quiet only when the complete required-writer set is enrolled, every writer's epoch matches, each source sequence from A-exclusive through F-inclusive is contiguous, and no predicate-changing event occurs in that interval; irrelevant events do not invalidate it. Missing writer, sequence, or epoch evidence yields UNKNOWN. `QUIET_AS_OF_FRONTIER` is historical and advisory. Actuation at B is separately allowed only when the fixture's atomic compare at B confirms the version observed at F; no certificate bridges F→B by itself.

Cases are fixed in `fixture.json`; candidate and auditor are frozen before the single formal candidate/audit sequence. Construction checks are separate. No retry, tuning, Docker, GPU, GUI, model, provider, network, or user data.
