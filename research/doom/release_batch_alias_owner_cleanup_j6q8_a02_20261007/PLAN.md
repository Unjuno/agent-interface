# A02 H/T/D/C/U and run protocol

A01 stopped before Xvfb because the runner passed an existing mount root to a candidate that only accepts a new, nonexistent output directory. Its STOP is preserved separately; this A02 is a new construction ID and does not rerun or overwrite A01.

- **H:** On the actual V4→V3→V12 InputOwner composition, a candidate guard refuses duplicate resolved codes without releasing a held key; a subsequent actual owner close releases that key and records verified empty state.
- **T:** One private TCP-disabled Xvfb session. Admit and hold `a`; submit guarded `up_batch(["a", "A"])` once; verify refusal with no KeyRelease and key still held; call the actual V4 wrapper `close()` once; inspect the client event, X server keymap, terminal V12 release record, thread state, and Xvfb exit.
- **D:** PASS only if the alias resolves to one code, refusal occurs before KeyRelease, the key remains held until close, close yields a matching KeyRelease and verified empty `owner_release(reason="close")`, the keymap is neutral, the owner thread stops, and Xvfb exits zero. Candidate completion with any contradiction is FAIL. Setup/candidate incompletion is STOP. No retry or overwrite.
- **C:** This isolates the owner-close path. A particular V15/V39 caller may fail to invoke close after an exception. Xvfb keymap/events do not establish physical device state or app consumption.
- **U:** One synthetic case only; no full V15/V39 controller unwind, physical HID, Doom/task, useful feedback, recovery benefit, latency bound, threat exposure, or MAP01 result.

The alias guard exists only in the frozen candidate source copy. No production source is modified or adopted.
