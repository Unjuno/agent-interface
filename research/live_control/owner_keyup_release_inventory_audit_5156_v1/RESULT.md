# Allocation 06 — result

**PASS_RELEASE_INVENTORY_AUDIT_CONSTRUCTION_SYNTHETIC_ONLY (with execution-copy EOL normalization disclosed).**

The pinned 14-test fake-Xlib suite passed 14/14. The expected-inventory auditor accepted the pristine three-admission trace and rejected empty trace, all brackets omitted, one bracket deleted, one admission deleted, terminal deleted, keycode corruption, and inverted owner timestamps. The predecessor raw-row auditor accepted pristine and all omission controls (false-accept). v10 and v11 emitted the same six key requests, each used seven XSync calls, and both ended with no fake keys down. Three terminal owner records were verified neutral. A separate raw-only independent audit returned errors=[].

**Source identity limitation:** the GitHub frozen blobs and manifest hashes are exact, but the ephemeral execution copies of v10/v11 were line-ending normalized (mixed CRLF/LF to LF) by materialization. This changes no Python tokens, but means the run is not byte-identical to the frozen blobs. See EXECUTION_NOTES.md. Do not cite this as byte-identical reproduction.

**Scope:** deterministic host fake-Xlib construction only. No Docker/shared allocation, real X server, GUI, physical key-up, game, model, GPU, held-input occupancy, or MAP01 efficacy was tested. Formal X11 allocation remains unperformed; Issue #5156 stays open.
