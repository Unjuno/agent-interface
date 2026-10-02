# #5694 A04 — matched-capture phase contrast

Successor to the immutable A03 HOLD. This allocation uses the same capture schedule `[10, 50] ms`, expiry `20 ms`, and observation horizon `60 ms` in both phase arms; only cue onset is shifted across the first capture. One native-Windows CPU candidate and one separate raw-only auditor are preregistered, with no retries.

No formal run result is present until the one-shot window is consumed. See `PREREGISTRATION.md`, `FREEZE.json`, and `PRE_FORMAL.md` for the H/T/D/C/U, exact hashes, tests, commands, and STOP gates. Scope is a deterministic synthetic measurement-method fixture only; no live-control or GPU claim.
