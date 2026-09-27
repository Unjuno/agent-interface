# XDamage temporal-boundary successor #4893

Status: source/construction phase. Formal invocation count: 0.

This additive study tests whether a non-clearing XDamage subscription records drawing activity across equal endpoint captures, while making no claim that damage identifies semantic change. It is scoped to a private core-X11 drawable on the pinned local Xvfb image. No GPU treatment is used: XDamage server-side event delivery is independent of the RTX 3080.

## H / T / D / C / U

**H:** Equal RGB endpoint captures do not prove temporal continuity. A→B→A may be suppressed by the exact O1 endpoint gate while an uncleared XDamage NonEmpty subscription retains interval drawing evidence. Repainting identical pixels can also notify, so damage means drawing evidence only and never grants action authority.

**T:** One fresh allocation, eight private Xvfb sessions and six 64×64 cases per session (48 total): QUIET, REPAINT_A, PERSIST_B, ABA_1PX, ABA_2X2, ABA_8X8. The renderer, observer and endpoint candidate are separate roles. The candidate receives only baseline and endpoint frames; middle capture is score-only. Retain RGB bytes, event fields, process exits and identities.

**D:** Before the one formal invocation, source, exact main gate, image digest, case schedule, scorer, independent raw-only auditor and corruption controls must be committed and read back. Any failed provenance, protocol or audit gate is STOP/HOLD; no retry or replacement invocation.

**C:** Barrier-authored directed transients are not natural GUI miss-rate estimates. Damage may coalesce or over-report drawing; repaint is the negative semantic control.

**U:** GPU/compositor/Wayland, natural event loss, semantic event recovery, latency, usefulness and task correctness remain untested. This experiment does not change runtime or O1.

## Frozen intake

- Base main: 1c9ad8d8895f9adf83d7b1bcf1c919cf9addd48a
- Source image: agent-interface-gtk-preflight:local, linux/amd64, image ID sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4
- ExactGate: research/observation_gating/exact_gate.py at base main; Git blob d2629bc94d40cc0a8e1bf9e053585549218629ed
- No network, no package installation, no GPU, no user desktop, no input API.

Formal status remains NOT RUN until the frozen source readback and all preformal gates pass.


## Executed construction boundary

Construction 05 ran once in the pinned image and passed a separate RGB-byte audit for the six conditions. Exact command, source and output identities, per-case hashes, lossless raw archive and limitations are in [CONSTRUCTION_05.md](CONSTRUCTION_05.md). This is construction-only on one X client/session; it is not formal evidence and does not satisfy the planned role separation, eight sessions, ExactGate boundary, provenance audit or corruption controls. Formal invocation remains 0/1. The incomplete formal launcher was removed so this branch cannot accidentally report a run that is not implemented.


A second excluded block, [CONSTRUCTION_06.md](CONSTRUCTION_06.md), recompiles the exact GitHub-readback C source after construction 05 exposed a newline-related source/executable identity mismatch. Its separate six-row raw bundle and manifest are retained. This repairs provenance for construction only and does not consume or satisfy the formal allocation.
