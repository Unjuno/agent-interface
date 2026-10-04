# F01: fractured Draw reads synthesize a false goal

Issue #6259 successor boundary transfer from its retained C01 SQLite study. No previous T0/C01/browser STOP is replayed or modified. This is actual Draw/UNO, not a model or desktop-input result.

H: reading objects separately across an independent writer can assemble a goal from different application states.

T: one WSLc invocation, two fresh documents stable/mutated. Goal A1900/B2700; initial A1900/B2800 (all y1000, size500). Read A first. In the mutated case a separate UNO process sets A1800, records the page prefix, then sets B2700 and records the next prefix. Read B after writer completion. Compare split satisfaction with a fresh post-writer page read, independent observer and saved FODG. The controller emits no writes after setup.

D: producer/container exit0/errors[], first frozen auditor exit0/errors[], SUPPORT_FRACTURED_DRAW_READ_SCOPED. Mutated split reads A1900+B2700 and reports satisfied, while initial state, recorded after-A prefix (A1800/B2800), and final (A1800/B2700) all fail the goal. Stable split and both serialized fresh reads refuse. Independent observer and saved XML match final states; hashes retained. Read-A completion precedes writer completion, which precedes read-B completion.

C: image sha256:bab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d, CPU1, memory512MiB, networknone, user65534:65534, read-only source mount/writable output. No model calls. Root filesystem is not claimed read-only.

U: scoped actual application read-consistency counterexample. Recorded writer prefixes are not instrumentation of every native internal instant. The fresh read succeeds as a comparator only under the controlled schedule with no additional writer; multiple fresh UNO calls are not established as an atomic snapshot. No generic state-oracle completeness, authenticated generation, GUI/input release, natural race rate, safe retry, real task completion or model value claim. This transfer informs post-effect verification in #2122 without invalidating its controlled R03 result.

Evidence: six pre-run frozen sources including literal B03 controller source, first raw/run/audit logs, independent writer prefix output, observer outputs and two FODG documents. FILES.json covers copied members; publication README, FILES.json and .gitattributes are outside the manifest. Attributes preserve raw bytes. Source/raw review supplements the finite saved-state auditor.

First result: https://github.com/Unjuno/agent-interface/issues/6259#issuecomment-5975213782
