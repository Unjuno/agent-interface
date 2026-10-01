# Symbolic keyboard current-state live rung

Allocation: `symbolic-keyboard-current-37-20260926-01`.

H/T/D/C/U are frozen in Issue #4450, with this preformal construction correction: a long-lived Python-Xlib connection retained its pre-change keysym→keycode map after `setxkbmap us -> de`. Construction observed RAW `Ctrl+z` use keycode 52 and cause REDO under German, while a fresh current-map connection used keycode 29 and caused UNDO. No formal row had run.

Formal gate therefore distinguishes three policies: RAW preserves the stale-map negative, SNAPSHOT refuses the generation change, CURRENT reopens/re-resolves the current keymap and must produce the correct UNDO. Context gates remain as Issue #4450: RAW emits unsupported Return in NO_MODAL/STALE_CONTEXT; both symbolic policies refuse.

Six conditions × three policies × two repetitions = 36 fresh sessions. Fixed order: rep, condition, policy. One invocation/case; no retries/replacements/exclusions/tuning.

PASS counts: RAW exact6/wrong6/refused0; SNAPSHOT exact6/wrong0/refused6; CURRENT exact8/wrong0/refused4. All current-symbolic wrong effects=0. Every emitted input ends neutral. No authority grants. Raw-only auditor errors=[] and eight mutation controls reject.

Limits: cooperative context, X11 only, known mappings, no model/task/token/latency/product claim.
