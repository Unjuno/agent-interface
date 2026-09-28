# #5134 host-filesystem boundary rung — allocation `needle-publication-host-boundary-5134-20260928-01`

This is a new, one-shot host-only boundary experiment because the separate OrbStack formal allocation `...-02` was consumed at a terminal preflight STOP. It does not reuse that allocation or claim to replace the requested OrbStack/macOS bind-mount experiment. It uses the same immutable seed-3788 package bytes solely as synthetic content; it does not read or replay #5073 outputs.

## H / T / D / C / U

- **H:** On this macOS host filesystem, seven same-directory `os.replace` transitions preserve a pre-opened descriptor's exact previous package while a fresh path open after replacement returns the exact next package. In a matched in-place truncate/write arm, an independent reader released during the writer's held partial-prefix interval observes those exact incomplete bytes through both its pre-opened descriptor and a fresh path open.
- **T:** One host, one local filesystem path under `/tmp`, the frozen seed blob/SHA, seven generations 3789–3795, four newly spawned independent reader processes per phase and arm. No Docker/OrbStack command, model, network, GUI, or external side effect. Source/base/image/output identities are frozen in `FREEZE.json` and the run receipt.
- **D:** 7 atomic phases × 4 readers (28 rows, each with held-FD old bytes and fresh-path new bytes); then 7 in-place phases × 4 readers (28 rows, each capturing the strict prefix while the writer is deliberately paused, before it completes the exact next package). PASS only if the independent auditor reconstructs every byte and timestamp relation, all child exit codes are zero, atomic rows equal exact old/new bytes, unsafe rows equal the exact strict prefix, and completed unsafe files equal the exact next bytes. Any contrary row is FAIL; source/environment/process/audit failure is STOP. No retry of this allocation after launch.
- **C:** Same seed-derived payloads, seven transitions, host interpreter, path family, and independent process count. Atomic and unsafe arms differ only in publication action (`os.replace` vs truncate + partial write + completion). Reader timing in the unsafe arm is intentionally barrier-controlled to demonstrate exposure, not to estimate its natural probability.
- **U:** One macOS host, one local host filesystem, Python build, path family, synthetic package, and deterministic schedule. This does not establish container-to-host bind semantics, OrbStack behavior, other filesystems/platforms, crash durability, production safety, model/task quality, GUI effects, or performance/general reliability.

## Execution boundary

Freeze source and tests, run local construction tests, then invoke `host_boundary.py` exactly once into a fresh output path. Run the separate standard-library-only auditor once against the retained raw capture. Preserve PASS/FAIL/STOP and every output; never relabel this host rung as the pending OrbStack formal result.
