# Issue #3903 frozen protocol

## H / T / D / C / U

- **H:** A side-effect-aware AST walk can distinguish deferred callables and the conventional main guard from module-executed calls. The frozen `session_entry.py` should be refused because `session_map01_v13.main()` executes in its module-level `try/finally`.
- **T:** One source-only audit of the exact `import_gate.py` and `session_entry.py` text from commit `8652f6a3527d55610185d1103b87d5d9fd8fa985`, with eight synthetic controls. Candidate and independently implemented stdlib-only verifier run sequentially within one Docker container invocation. No target import, compilation, execution, dependencies, workflow, game, model, GUI, or input.
- **D:** `PASS_STATIC_IMPORT_BOUNDARY_SCOPED` requires 8/8 candidate controls, exact target module-call disposition `REFUSE_UNGUARDED_MODULE_LAUNCH`, independent verifier agreement, frozen provenance, and zero endpoint counts. Any disagreement is FAIL; setup/hash mismatch is STOP/HOLD.
- **C:** Docker Desktop 28.5.1, linux/amd64; immutable cached image from `SOURCE_MANIFEST.json`; `--pull=never --network none --read-only`, RO source, dedicated RW evidence only, 1 CPU, 256 MiB, 32 PIDs, all caps dropped, no-new-privileges, 16 MiB tmpfs. Do not clean up unrelated Docker resources.
- **U:** Static syntax does not prove transitive import safety, runtime behavior, workflow policy, historical correctness, or gameplay/product claims. The result applies only to this frozen source-level classification.

## Frozen identity

Base main, historical source commit, exact source Git blob IDs, byte hashes, runner/auditor/script hashes, Docker engine, platform, and image ID are recorded in `SOURCE_MANIFEST.json`. Host construction tests passed 8/8 before the formal invocation. Formal output is fresh at `results/formal01/` and is never overwritten. The formal container invocation has not yet run.

Stop after exactly one formal Docker invocation; preserve failures and do not rerun.
