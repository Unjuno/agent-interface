# Interrupted full six-task guarded move comparison

**HOLD.** Candidate `04c34a39b8d482dcf0137f43947e6b534c1882ff`, frozen seed
1001049, full A/A/A/B/B/B fixture, same primary caller and Ubuntu private X11.
The guarded arm saved tasks 1–5 exactly once and stopped before input on task 6
when `field_b` returned STALE. The direct one-program field/Save arm saved all six
exactly once. Independent token history records no duplicate or unexpected saves.
This is retained failure evidence, not a six-task guarded pass or promotion gate.

Guarded task 4 rejected the old A target before input; the primary explicitly
reviewed the new B window scope, confirmed old source and alias revocation,
grounded B targets and completed tasks 4–5. Each of the five Save moves emitted
only pointer motion, followed by 100ms wait, primary image review, a fresh hover
alias and separately guarded click. The before-press checks were preserved.
Task 6 unexpected refusal ended the arm under the prewritten stop rule; there
was no repair, retry, replay or restart of either consumed allocation.

The caller was interrupted for environment verification between task 5 field
and Save. Alias mint to task-6 refusal spans **375.769609906 seconds**, exceeding
the bridge's 300-second alias TTL. The STALE reason groups alias expiry and
capture freshness; the interval establishes expiry without proving it was the
only failing condition. Do not rank these arms by end-to-end tempo: the long
interruption and serial known-family order confound that comparison.

| Retained observation | Guarded | Direct |
|---|---:|---:|
| Exact-once saved tasks | 5/6 | 6/6 |
| Public calls including setup/close | 43 | 29 |
| Completed input programs | 21 | 12 |
| Reply images | 26 | 13 |
| Input emissions | 563 | 588 |

Direct submission uses 200ms field waits, 100ms after Save movement and 100ms
after clicking. Navigation is 400ms in both arms. This is not the fastest direct
baseline, a redraw acknowledgement, held-out task comparison, compiled third
arm, broad-domain test, model token/cost measurement or human-speed measurement.
Tokens, dollars and human comparison remain unmeasured. Caller review receipts
are attribution, not independently measured perception timestamps.

The unexpected-refusal Node invocation surfaced text without a visible image in
its tool result. Primary text review was recorded, then the original native PNG
was opened after neutral close and visually confirmed an empty task-6 B field.
The additive delayed-image note retains this distinction; the earlier receipt
must not be interpreted as image perception at that timestamp. Initial guarded
review and task-5 field review receipts were also delayed, as their reasons state.

Both public closes verified empty held keys/buttons. Original fixture handles
5355 and 43753 terminated with exit 0; both relay transports terminated with
code 0. Cleanup child exit codes are retained individually, including a child
with code 1 in each arm; this is not an all-child-success assertion.

`raw.tar.gz` retains the frozen plan, portable archive/build/source hashes,
caller, fixture, all original requests/replies, native PNGs, primary review
receipts, independent scores, cleanup and original-process terminal attribution.
`manifest.json` hashes the archive and every member. Run `python3 verify.py`
or `python3 -O verify.py`; rejection checks must survive optimized Python.

Integration implication: pointer-only move handles hover semantics through
explicit primary review, but reusable target references have a finite lifetime.
Next work should expose expiry information to the caller and evaluate explicit
fresh grounding after a pause, with fresh allocations and a frozen recovery
policy. Do not extend TTL or relax the exact-region/before-press checks to turn
this failed arm into a pass. The candidate remains under review in PR #5639.
