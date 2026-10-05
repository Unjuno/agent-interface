# V39/V15 dropped KeyRelease probe — A04

A04 is a preserved constructor STOP. The candidate used the selected V15 release-batch backend and V13 executor with a fake-X production input owner, but its test-only base controller did not provide the construction owner expected by the production V2/V15 constructor chain. It failed before either paired case started (`AttributeError: 'NoneType' object has no attribute 'close'`). Per the frozen stop rule, A04 was not repaired and rerun; no dropped-release terminal behavior was measured.

The STOP is distinct from A01 and A02 and does not change their outcomes or A03's bounded synthetic result. It leaves the production V13 per-program cleanup question unresolved. The candidate and auditor hashes plus production source hashes are recorded in `FREEZE_A04.json`; exact frozen commands are in `RUN_COMMANDS.md`.
A04's frozen candidate stopped during backend construction with AttributeError: 'NoneType' object has no attribute 'close'; no paired case started. The frozen one-run rule was honored. Subsequent static correction work was moved to candidate_a05_unrun.py / audit_a05_unrun.py and was never executed; these files are not A04 evidence.
## H/T/D/C/U — A04 per-program cleanup STOP

- **H:** V13 terminal cleanup calls V15's owner `release` RPC. The production V4→V3→V12 owner tracks touched keycodes and should detect a suppressed explicit KeyRelease; V13 should publish a failed terminal when release verification fails.
- **T:** Freeze current main `402c7d1b5147b2a905098f082233db60a47d68db`; use paired normal/lost fake-X cases through V15 batch code and the V13 executor, with production V4→V3→V12 owner code. One candidate execution, preserve STOP/FAIL/PASS raw, then one independent audit only if candidate raw exists. No GUI, Doom, model, or physical input.
- **D:** Pass only if normal delivery completes with verified release and no key down, while suppressed release yields a failed terminal with keycode 38 remaining and a verified=false cleanup diagnostic. Constructor failure before cases is STOP/unresolved.
- **C:** Synthetic source composition only. A04 stopped before cases because the test-double base controller lacked the constructor-owner contract. Corrected static harness code is preserved as A05-unrun and is not evidence.
- **U:** Per-program lost-release detection/recovery, physical input state, application effect, and the live #59 MAP01 exit gate remain unresolved.
