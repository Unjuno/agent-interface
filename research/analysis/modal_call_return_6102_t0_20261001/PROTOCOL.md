# Frozen T0 protocol — visible modal call/return matching (#6102)

## H / T / D / C / U

- **H:** On a source-bound, well-nested finite GUI-modal event alphabet, a stack monitor and a depth-matched finite-state monitor preserve exact parent/generation context equally through supported depth 0–3; a flat open/closed flag admits at least one wrong-parent continuation. Missing, stale, duplicate, non-LIFO, interleaved-window, or over-depth events must fail closed as `UNKNOWN_NESTING`.
- **T:** Deterministic no-network synthetic traces over a frozen finite identity/generation alphabet. Compare (1) a flat modal flag, (2) an explicit stack monitor, (3) a finite-state monitor whose states encode every supported stack configuration up to depth 3, and (4) an independently implemented raw-only oracle. Cases cover valid depths 0–3, wrong-parent close, duplicate close, parent destruction with open child, non-LIFO switch, missing open, stale generation after ID reuse, interleaved independent window, unregistered identity, invalid next-action context, and depth overflow. Candidate emits every policy/case row and terminal disposition.
- **D:** `PASS_METHOD_SCOPED` only if stack and depth-3 FSM exactly match the independent oracle on every case; all invalid traces fail closed; the flat flag demonstrably admits a wrong-parent action; FSM and stack agree on supported traces. Report state counts as representation accounting only, not a correctness/speed winner. The test does not claim arbitrary-depth recognition or arbitrary/unbounded GUI identity support.
- **C:** Source-bound events and the finite identity/generation alphabet are authored fixtures. A depth bound makes a finite-state encoding possible; no live GUI event source is exercised. VPA terminology is only a structural analogy.
- **U:** No application, GUI, model, task-effect, authority, safety, or runtime result. The result says nothing about whether production GUIs expose reliable open/close/parent/generation events. No arbitrary-ID or unbounded-depth theorem is claimed.

Seed/inputs: fixed case table in `simulate.py`, no RNG, network disabled. Supported depth: 3. Identity alphabet: root plus `modal-a`, `modal-b`, `modal-c`; generations: 1 and 2. Every source event includes its declared parent, child (where relevant), and generation. The independent oracle is implemented separately in `audit.py` and consumes only raw input/output JSONL.

Any candidate/protocol/test change after `FREEZE.json` invalidates the official run. Construction and official evidence must be kept separate.
