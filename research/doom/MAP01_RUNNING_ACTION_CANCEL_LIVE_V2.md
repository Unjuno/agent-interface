# MAP01 running-action cancellation live v2

The first frozen allocation failed before input. It initialized two WAD glyph
readers after capturing its freshness source, so the source was 926.873ms old
when checked against a 500ms contract. The runtime emitted only clock, ready and
one exact observation events. No command or input was admitted. The wrapper did
not retain owner-close, post-score or exit-code evidence, so those cleanup claims
remain unavailable. That result is preserved unchanged under
`results/map01-running-action-cancel-live-01`.

V2 moved WAD parsing and glyph-template construction before runtime launch and
registered bounded wrapper cleanup. Its separately hashed one-episode allocation
loaded the same real Freedoom MAP01 fixture through X11. A controller-authored
probe set `minimum_ammo` to the initial screen-visible value,48, then submitted
one 450ms held-fire program. The first visible decrease to47 invalidated that
exact action while the program was active.

The runtime accepted one program, recorded one matching cancel, emitted no later
input admission, and returned a cancelled terminal with independently verified
empty keys and buttons. All14 independent audit checks pass on Windows and WSL.

Measured local intervals:

| Endpoint | Time |
|---|---:|
| submit send → Executor accept | 11.192ms |
| accept → first feedback capture | 59.546ms |
| accept → first feedback emission | 149.841ms |
| accept → invalidating capture | 213.724ms |
| invalidating capture → guard decision | 128.488ms |
| guard decision → cancel requested | 8.291ms |
| guard decision → empty release | 10.206ms |
| invalidating capture → cancel requested | 136.780ms |
| invalidating capture → empty release | 138.694ms |

The preregistered capture-to-cancel threshold was150ms and capture-to-release
threshold was200ms; both pass. Most of the remaining reaction interval precedes
the guard decision because the current path waits for image publication and then
reopens the PNG for HUD recognition. The next candidate should emit a small
typed HUD signal from the captured frame before full image encoding/publication,
while retaining the exact frame hash and later reconciliation.

This is one controller-authored motor-safety probe with zero model calls. It does
not establish planner-authored schema-v6 behavior, MAP01 progress, survival,
task completion, general reaction speed or human-level control.
