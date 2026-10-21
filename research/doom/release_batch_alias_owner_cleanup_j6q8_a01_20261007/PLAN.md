# A01 H/T/D/C/U and run protocol

- **H:** On the actual V4→V3→V12 InputOwner composition, a candidate guard refuses duplicate resolved codes without releasing a held key; a subsequent actual owner close releases that key and records verified empty state.
- **T:** One private TCP-disabled Xvfb session with one focused test window. Admit `a`; call guarded `up_batch(["a", "A"])` once; verify refusal and that the key remains held; close the real V4 owner wrapper once; inspect the server keymap, client KeyRelease event, terminal V12 release record, thread state, and Xvfb exit.
- **D:** PASS only if the exact alias maps to one code, refusal occurs without KeyRelease, close yields a matching KeyRelease and a verified empty `owner_release(reason="close")`, the keymap is neutral, the owner thread stops, and Xvfb exits zero. Candidate completion with any contradiction is FAIL. Setup/candidate incompletion is STOP. No retry or overwrite.
- **C:** This isolates the owner-close cleanup path. A caller that fails before invoking close could leave cleanup behavior different. Xvfb event delivery and keymap state do not establish physical device state or application consumption.
- **U:** One synthetic case, no frequency/reliability claim, physical HID, Doom/task, V15/V39 top-level caller unwind, useful feedback, recovery benefit, latency, or Issue #59 live gate.

The source guard is experimental only; production files remain unchanged. Candidate and auditor are each single-invocation artifacts. Candidate raw output is written to an external output mount, then independently audited once.
