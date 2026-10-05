# V39/V15 dropped explicit KeyRelease composition probe — A01

## H/T/D/C/U

- **H:** In the frozen V39/V15 release composition, a lost XTest `KeyRelease` may still produce a release-batch row with `owner_transition_verified=true`, because the owner receipt proves `XSync` completion and the post-batch state is owner bookkeeping. A separate A04 asked whether the production V13 per-program cleanup catches the key; its candidate stopped before either case.
- **T:** A01/A02 constructor/finalizer STOPs and A03 paired batch probe are preserved on current-main predecessor `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`. A04 froze current main `402c7d1b5147b2a905098f082233db60a47d68db` and attempted to compose V15 batch logic, V4→V3→V12 production owner, and V13 executor with fake X; the constructor STOP occurred before cases. No live X, GUI, Doom, model, or game allocation.
- **D:** A03 failed its bounded batch physical-release gate: the fake server retained the key while the row was owner-transition-verified. A04's frozen production per-program cleanup gate is unresolved because the test stopped before cases. Do not generalize A03's terminal-close diagnostic to per-program executor cleanup.
- **C:** This is a synthetic composition probe of the selected V15 backend and current owner/transition chain. The base controller action loop is a small test double that supplies the same `actions` list into the production backend's `execute`/`raw` seams. It does not prove real X server delivery, application consumption, useful feedback, recovery, latency, threat response, or MAP01 progress.
- **U:** Whether V13's production per-program cleanup detects a dropped explicit key-up, whether a cleanup retry recovers it, and whether any such change alters game behavior remain untested. The private live-game allocation remains unassigned.

## Reproduction

Use the cached Python 3.12 image by digest, `--pull never`, `--network none`, 0.25 CPU, 512 MiB, a read-only source mount, and separate output mounts. A01/A02 construction STOPs, A03 paired raw/audit, and A04 constructor STOP remain preserved. See `RESULT.md` and `RESULT_A04.md` for dispositions and `RUN_COMMANDS.md` for exact commands/resource warnings. A03's audit passed 16/16 but its physical-release gate failed; A04 did not run either case and leaves per-program cleanup unresolved.
