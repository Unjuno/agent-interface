# Issue #5541 — mutation adequacy T0

**Scoped result:** `PASS_T0_MUTATION_ADEQUACY_AFTER_AUDIT_V2`; the initial audit implementation failed and remains preserved as `results/AUDIT.json`.

## H / T / D / C / U

- **H:** Baseline traces plus one-step metamorphic downgrades will kill ordinary single-gate safety mutants; an independent exhaustive semantic oracle will be needed to expose at least one correlated interaction mutant that those first two layers miss.
- **T:** Freeze a five-boolean action-admission contract and six explicit mutants. Enumerate all 32 states. Run one deterministic candidate CLI to retain baseline, metamorphic, and exhaustive decisions, then audit only the retained raw from a separate process.
- **D:** The strict candidate matched the contract on all 32 states. Five ordinary gate-removal mutants were killed by baseline or metamorphic tests. The declared compound provenance/authority/terminal mutant survived both, but was killed by the independent exhaustive oracle. Audit v2 reports `PASS_T0_MUTATION_ADEQUACY`, six non-equivalent mutants, zero survivors, and `errors=[]`.
- **C:** Synthetic finite model and manually declared mutant set. No real production interface, model, task, human, or runtime behavior is represented.
- **U:** This does not estimate production defect probability or prove catalogue completeness. Results depend on the chosen contract, mutation operators, and declared semantics.

## Execution record

- Source main at freeze and launch: `666a2b0919199bb11251ceb83a31b23be6d71b34`.
- Local pre-run tests: 5/5; all four frozen Python source hashes matched `FREEZE.json`.
- Candidate command: `python3 run.py results/raw.json`; one invocation, exit 0, 32 states × 6 mutants retained.
- Initial raw-only audit: `python3 audit.py results/raw.json results/AUDIT.json`; one invocation, exit 1, `FAIL_AUDIT`.
- Audit v1 root cause: its independent mutant semantics omitted the shared terminal-failure guard for five mutants, and its metamorphic verifier incorrectly expected the valid base state to have `terminal_failure=True`.
- Audit correction: two focused tests passed; separate `audit_v2.py` process checked the unchanged raw, exit 0, `errors=[]`. Raw SHA-256 remained `cc8677299ecb2bef5435f07cd9c90f97555a80ca25980b7b0eaf803e5d7ae6b9`.
- Container invocations: zero. No #5085 assignment covered this Issue; active shared-container use was reported in the coordination thread. This host-only result is not represented as container evidence.

The v1 failed audit, v2 corrected audit, candidate raw, and execution details are all retained separately. No candidate rerun or raw edit occurred.
