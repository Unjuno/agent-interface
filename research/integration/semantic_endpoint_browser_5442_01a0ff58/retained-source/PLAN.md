# Application-bound endpoint construction for Issue5442

H: scoped DOM dispatch success does not imply the requested SQLite target and
precondition/effect. A fresh endpoint observer can distinguish them and bounded
fresh-version recovery can establish a new, explicitly different repair receipt.
T: one owned hidden Codex IAB tab and one private loopback HTML/SQLite app;
8 rooms (2 desired strings x valid/wrong-target/noop/stale-precondition).
Each gets exactly1 initial DOM form submit, not a simulator/candidate replay.
Read SQLite through a separate process/connection; preserve first8 results.
For the6 UNKNOWN rooms, a new guarded repair intent uses freshly observed A/B
versions, one repair submit max, atomically restoring only fixture-owned B and
writing A. Valid rooms get no repair. Original actions remain UNKNOWN forever.
D: PASS_APPLICATION_ENDPOINT_SCOPED if all8 initial UI submissions return and
show accepted, the independent persisted-state observer confirms2 and refuses6,
then6 fresh-version repairs satisfy their separately declared predicates with
no extra/missing operations. STOP/HOLD on missing identity/source/effect/trace,
unexpected UI, unknown submit outcome or a duplicate; preserve partial data.
C: same form/control/target A and scoped namespace, source, observer and desired
texts; only seeded endpoint modes differ. Authority is only these authored
SQLite rows. Namespace/target/preversion/text, nonces and phase are explicit.
U: actual controlled HTML form and SQLite commit/read visibility, not arbitrary
app observer authenticity, human/task safety, physical desktop input/release,
durability under power loss, generic concurrent correctness, performance,
latency-matched efficacy, model efficiency, promoted runtime or public MCP.

Private browser owner: this worker; IAB browser2/tab1, DOM-only actions via CUA.
Loopback server binds127.0.0.1 at an OS-assigned port, one process, stdlib only.
No external site/data, shared display/container/GPU/model lease or extra worker.
Graphics provenance is unmeasured; no training/inference job is invoked.
Initial DB absent, source/actor/plan/predicates frozen before server startup.
Initial first source/output remains immutable; no retry/restart/reset of this DB.
T7/T8 formal allocations, hashes, outcomes and source stay untouched.
Prospective main reference:6da2b492b9c2a9d76e5c54d35a0ae50b7b49edde.
There is no imported repository runtime; app source and event-to-predicate
transfer are the construction question, not kernel integration/adoption proof.
