# Issue #5970 T7 — pre-input liveness of recorded X event target

## H / T / D / C / U

- **H:** X RECORD target XID 2097170 from T4/T6 is not part of the pre-input Tk window hierarchy because it is absent, unmapped, or otherwise not selectable until the key event lifecycle; this explains why selecting all pre-existing windows does not capture it.
- **T:** Launch the exact hash-pinned T3-derived Tk app under a fresh private Xvfb, wait for its Entry focus, recursively enumerate the live window tree, and query XID 2097170 directly for attributes, parent/children, and second-client KeyPress/KeyRelease selection. No XTest imports/calls or input dispatch. Preserve raw success/error codes and cleanup.
- **D:** `PASS_TARGET_ABSENT_PREINPUT` if direct query yields BadWindow and XID is absent from the tree; `PASS_TARGET_PRESENT_UNMAPPED` if query succeeds but is unmapped/not in tree; `HOLD_TARGET_PRESENT_MAPPED` if valid/mapped; `HOLD_QUERY_ERROR_OTHER` otherwise. This classifies only pre-input X resource liveness, not the reason for event routing.
- **C:** One Tk fixture, one Xvfb server, read-only tree/attribute query and one mask selection request; no key or pointer events. Docker Desktop engine remains unavailable; private WSL2 Xvfb fallback.
- **U:** Why/how a later KeyPress/KeyRelease names this XID, whether it is a focus proxy created during input handling, how X RECORD event.window semantics interact with Tk, and whether any capture design transfers to deployed #4135 or benefits recovery.

Candidate and independent raw auditor each run once. T3-T6 allocations remain immutable; no formal #4135 rerun.
