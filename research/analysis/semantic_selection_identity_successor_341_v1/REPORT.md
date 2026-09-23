# Issue #2018 successor — read-only semantic selection identity

## H/T/D/C/U

- **H:** A public read-only semantic selection source can distinguish stable identity from pixel-identical replacement more reliably than screenshot-only revalidation, while remaining non-authoritative.
- **T:** Freeze six controlled cases: stable selection, pixel-identical replacement, focus transfer, unavailable source, stale generation, and visual/semantic conflict. Compare VISUAL_ONLY, SEMANTIC_SELECTION_OBSERVATION, and VISUAL_PLUS_SEMANTIC_CONSISTENCY.
- **D:** `experiment.py`, case ledger, identity/generation fields, verdicts, digest, and authority-event counter.
- **C:** Stable same-object selection passes; replacement, focus mismatch, unavailable, stale, and conflict fail closed; visual-only must expose false acceptance; authority events remain zero.
- **U:** Real accessibility-source availability, latency, GUI correctness, model benefit, and runtime promotion remain unknown.
- **STOP:** One finite read-only fixture; no click, selection, model, network, or user input.

## Result

Command: `python experiment.py`

- Stable case: combined identity check passes.
- Visual-only incorrectly accepts the pixel-identical replacement, focus transfer, unavailable, and stale cases.
- Semantic/combined checks reject all five non-stable cases.
- Authority/input events: **0**.
- Result digest: `9df031b185304ad8bb14da90e4398555cab9864ff3506e80c6484b540c82d25f`.

**Decision: PASS_READ_ONLY_SELECTION_IDENTITY_SCOPED.**

This is a finite epistemic-boundary result only. It does not establish that a real desktop application exposes a stable semantic identity source or that such a source improves latency, tokens, GUI correctness, or runtime behavior.
