# Issue #5333 — contextual-flow disclosure T0

Finite model-free test of whether a context tuple (recipient, purpose, exact fields, release revision) distinguishes permitted disclosure from a forbidden flow when actor permission and the personal-data label alone are insufficient.

This is separate from the local predicate-only receipt toy noted in #5333: that toy varied evidence representation, while this fixture holds actor/source labels fixed and varies disclosure context. It makes no claim about runtime enforcement or semantic inference.

## Hypothesis / method / limits

- **H:** Context-bound policy can permit one narrow intended flow and one exact purpose-bound release, block wrong recipient/purpose and excess fields, and return UNKNOWN for missing context; actor-only authorization alone is insufficient.
- **T:** Eleven synthetic cards × three policies = 33 rows. The auditor independently checks row completeness, matched-pair invariance, exact output schema, context/provenance, decisions, released-field scope, and nine planted corruptions.
- **D:** PASS only if all frozen expectations reconcile and all corruption controls fail closed. Status is `PASS_METHOD_SCOPED` for this fixture only.
- **C:** Context norms are stipulated by policy JSON; all data and recipients are synthetic.
- **U:** Unknown labels return `UNKNOWN_FLOW`; a known `PUBLIC` label remains an allowed control. No model, human, actual personal data, GUI, external recipient, runtime sink, covert channel, privacy/safety benefit, or product claim.

Preparation failure and repair history is preserved in [CONSTRUCTION.md](CONSTRUCTION.md); the WSLc output-mount smoke is retained in `construction_output/`. `SHA256SUMS` currently records the preparation package source/input hashes. The final `FREEZE.json` and formal `run/` receipts/raw outputs do **not** exist yet: create and verify them only after a fresh main/source/image/output and shared-owner start gate, immediately before formal execution. This Draft is preparation evidence, not a formal freeze or result.

## Execution

Use the local WSLc runtime only, and do not invoke the script until the formal freeze and external shared-owner gate are recorded and checked. The current script orchestrates exactly one network-disabled CPU candidate container, then—only if it exits zero—one separate network-disabled CPU auditor container; it refuses to overwrite an existing `run/`. It does **not** independently refresh main, validate a resource lease, or enforce the start gate. A failed formal step is terminal; do not rerun this allocation.

```powershell
& .\RUN_WSLc.ps1 -PackagePath (Resolve-Path .\research\analysis\contextual_flow_disclosure_5333_t0_20261002)
```

WSLc's configured 256 MiB memory request is not evidence of enforcement; the kernel reported unavailable cgroup/swap limit support during construction. GPU is intentionally unused because this small finite record-semantics workload has no GPU-appropriate computation.
