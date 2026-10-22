# Canonical MAP01 caller reachability for repeated same-key DOWN

## H / T / D / C / U

**H.** Under the current-main V39 MAP01 controller/backend call path, a well-formed accepted program does not issue a second same-key DOWN while the previous hold is still active. A04's `A down, A down, A up` direct-owner trace is therefore outside the ordinary compiler-generated operation sequence, while remaining a valid owner-component adversarial input worth retaining.

**T.** Pin current main `86a2694c6251c2d7df2f69dbea490ec037903ff7`; inspect the MAP01 command/cover compilers, Executor admission, the V4 inherited session hold validator/executor, and the actual V39 retained-input adapter override. Extract and execute only the source AST for `compile_commands`, `compile_cover`, and the base validator, without importing GUI/X11/game modules. Enumerate each of the ten literal semantic action types at each of four extents (40 single-command programs), every ordered two-command pairing (1,600 programs), and every ordered two-command cover program including 40 same-command repeats. Check that every compiled hold has a unique key list and that the exact inherited whole-program validator rejects an injected duplicate-key hold. Structurally inspect the inherited hold `finally` branch for its per-held-key UP call.

**D.** Scoped source-path PASS requires every enumerated compiled hold to have distinct keys; all valid one- and two-command programs pass the frozen base validator; the duplicate-key hold is rejected before dispatch; the hold cleanup contains a `finally` UP; and the source inheritance/override chain matches the V39 adapter. The reproducible script reports all these checks and source SHA-256 values in `SOURCE_REACHABILITY.json`.

**C.** The owner API itself does accept the repeated DOWN sequence in A04 construction, and `doom_retained_input_backend_v4.raw` forwards each `down` directly without an idempotence guard. A different direct caller, malformed input bypassing `Executor.submit`, a changed compiler, or failure/cancellation behavior can have different reachability. This does not prove that every external caller or all exceptional schedules are safe.

**U.** Source and bounded extracted-function evidence only. No live X11, game, model, container, physical input, exception-path scheduling, task effect, feedback, recovery, or authority was observed. This supplements the A04 one-shot formal STOP but does not repair it, audit its raw, or provide a formal scientific outcome. The #59 live threat-control allocation remains unassigned.

## Reconstructed path

`map01_overlap_controller_v39.compile_commands` lowers each semantic command to one `hold`. The ten literal action key lists are individually unique. The V39 backend subclasses the coast backend, which delegates to session v10 and ultimately the V4 operation implementation. `doom_retained_input_backend_v4` replaces the inherited owner with the transition-owner adapter and overrides `raw`; its DOWN call goes straight to `self.owner.call("down", ...)`. Thus the duplicate guard is above the owner: session V4 validates every hold's `keys` list (`len(set(keys)) == len(keys)`) and validates the whole program before `Executor` creates its worker thread. Inherited session V4 execution releases every key remaining in `self.held` from the hold's `finally` branch before that step returns. `Executor` refuses submission while another program is active.

For the declared 40 single-command cases, 1,600 ordered two-command cases, and 1,600 compiled two-command cover cases (including 40 repeated-same-command covers), the extracted output passed the exact V4 validator and all hold key lists were unique. An injected `{"op":"hold","keys":["Up","Up"],"duration_ms":180}` raised `ValueError`. No two successful adjacent hold steps overlap their held-key intervals in this source path because the first hold's `finally` UP runs before its execution returns and before the executor advances to the next step.

## Evidence files

- `source_reachability_check.py` replays the bounded AST extraction against the pinned commit without importing backend/runtime modules.
- `SOURCE_REACHABILITY.json` records counts, predicates, and SHA-256 for every source file inspected.
- A04 formal STOP remains in [`evidence/FORMAL_01/OUTCOME.md`](evidence/FORMAL_01/OUTCOME.md); its retained raw and non-formal post-run diagnostic are unchanged.
