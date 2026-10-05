# Issue #59: V39 MAP01 threat exposure A04

A04 is a single frozen six-decision V39/V15 live exposure on current main `6860b585`. The raw run completed, with an approaching enemy visible while an authored cover and model turn were active. The run does not demonstrate task success or a health-saving effect.

The typed stream recorded health 97→4 and ammo 45→42. The model explicitly noticed the initial 18-point health drop and changed its plan toward retreat/fire, but this is descriptive alignment rather than causal evidence. One input plan was admitted; five of six model actions were discarded as stale or invalid. One pending turn was interrupted after source evidence expired. The health value was unchanged (30→30) at that guard; ammo had moved 43→42 and its soft-change event was allowed to preserve the existing policy. The cover was canceled before the pending model answer, with verified empty owner state 7.655 ms after monitor receipt and a cancelled terminal 41.135 ms after receipt.

After that cancellation, the next fresh answer took 12.70 s. Health fell 30→4 during the wait and that answer was rejected as no longer current. The episode ended at the six-decision cap alive, with zero kills, no MAP01 exit and no independent scorer progress. This is bounded release-path evidence, not demonstrated recovery or MAP01 completion. Six per-key XSync releases were recorded; they do not prove physical key state or application consumption.

Earlier formal startup STOPs A01–A03 and construction-only diagnosis are retained in `results/prior-startup-stops.zip`, `results/startup-diagnostics.zip`, and `STARTUP_STOPS.json`. The intermittent native `DoomGame.init()` hang remains unexplained; none of those STOPs count as a live trial.

## Revalidation

Run `python audit.py`. The independent standard-library audit checks the raw ZIP inventory and SHA-256 list, all six prompt-image hashes, event/delivery identity, per-key release identities, empty owner releases, the source-expiry cancellation, the scorer outcome, and freeze/manifest binding. `VISUAL_AUDIT.md` records human inspection of frames 205 and 216; enemy semantics are not inferred by the audit script.

Key artifacts:

- `FREEZE.json`, `SOURCE_MANIFEST.json`, `FROZEN_COMMAND.txt`: frozen protocol and source provenance.
- `results/raw-a04.zip`, `results/RAW_SHA256SUMS.txt`: all 553 raw files (73,106,775 uncompressed bytes).
- `AUDIT.json`, `RESULT.json`, `VISUAL_AUDIT.md`: checked facts, interpretation, and limits.
- `CONTAINER_EXECUTION.json`: runtime image/flags and separately observed same-flags cgroup mapping. The A04 container was removed after exit, so cgroup values were not captured from that container itself.

The evidence supports a single limited live exposure. It does not close Issue #59's broader threat-control research gate.

REDACTIONS.md documents the narrow account-metadata redactions in public protocol-log copies; the unmodified raw run remains locally preserved.
