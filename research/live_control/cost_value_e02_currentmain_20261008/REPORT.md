# Cost-value metadata evidence: current-main rescue check

Date: 2026-10-08 JST

## H/T/D/C/U

- **H:** The existing numeric cost-value path may admit booleans/non-finite floats while a proposed domain accepts exact integers, finite floats, or `None`; the comparison asks how metadata policies classify directed values, not whether a provider violates an established contract.
- **T:** Recompose the already-published E02 evidence archive onto current main and verify its committed member hashes without rerunning the consumed Windows probe, candidate, or saved auditor.
- **D:** Original branch PR #7126 was already carried to current-main evidence-only successor #8322. This recheck composes #8322 head `dd20da87ee881d96e25ca99997599ecf1461ccce` onto main `d4eaac02eced2e6ebf2e8d29642343048661d71b` (merge head is in this branch history). PR diff stays six additive archive files under `research/integration/cost_value_57_E02_20261003_01a0ff59/`; no runtime source is changed.
- **C:** `SHA256SUMS` targets: 5/5 exact Git-blob SHA-256 matches. Workspace index: 161 top-level directories PASS; strict analysis index: 779 retained result directories PASS; `git diff --check origin/main...HEAD` PASS. The earlier independent capsule audit for #8322 recorded all 30 decoded packet member byte lengths/SHA-256, including 28 exact original-byte joins and 2 explicitly labeled projections. No historical producer/auditor execution was repeated.
- **U:** This preserves a proposed typed finite-cost metadata comparison only. It does not establish a provider defect, price/credit policy, runtime savings, accounting correctness, or product success. PR #8322 remains Draft and has no independent review; original #7126's review does not transfer. No main merge or predecessor cleanup until fresh review and applicable Issue #57 gates are satisfied.

## Commands

Exact checksum/index/diff checks are listed in `COMMANDS.txt`. The evidence package was read from Git blobs because this sparse worktree does not materialize `research/integration/` locally; no packet bytes were rewritten.
