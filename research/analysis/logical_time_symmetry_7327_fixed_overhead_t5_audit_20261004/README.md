# Audit-only successor T5 — Issue #7327

## H / T / D / C / U

- **H:** T4's preserved candidate raw is reconstructible from its frozen spec and candidate identity; it shows homogeneous trace equality, unchanged zero-startup control, and a later normalized first hazard observation when nonzero startup overhead is held fixed.
- **T:** Audit only the exact T4 `spec.json` and `output/raw.json`; do not invoke either T4 command again. A new independent auditor reconstructs all transformed parameters, event samples, and first-unsafe times. Test authentic raw plus four corruptions before the one formal audit invocation.
- **D:** `PASS_FIXED_OVERHEAD_DISTINGUISHED` only if the full raw reconstruction matches, homogeneous traces and the zero control match, the fixed-delay hazard reaction differs, and all four mutations are rejected. Otherwise report STOP/FAIL without retry.
- **C:** Offline exact-rational synthetic model; this is a recovery audit of retained evidence, not a new candidate run or live/runtime result.
- **U:** Whether T4's saved three-case raw actually supports its preregistered method outcome.

T4 remains immutable: candidate ran once/exit 0; its auditor ran once/exit 1 before writing a receipt due to a mutation-control indexing bug. T5 is a distinct audit-only allocation with a different auditor implementation and path; it does not retry the T4 auditor or candidate.

Host CPython 3.14.5 stdlib is used. OrbStack inventory fails on a containerd blob; no image pull, launch, or retry. No network, GUI, game, model, GPU, or physical input.
