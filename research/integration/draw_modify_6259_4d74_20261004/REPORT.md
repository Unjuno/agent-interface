# F02: measured Draw modification notifications detect fractured reads

Issue #6259 successor to F01 (#7350); earlier results remain unchanged.

H: XModifyListener callbacks may expose the actual independent setPosition writes across a split read.

T: one WSLc invocation, two fresh stable/mutated Draw documents. Register listener after setup. Goal A1900/B2700, initial A1900/B2800. Read A; mutated case runs a separate writer setting A1800 then B2700, recording both prefixes; read B after completion. Capture notification count before reading A and after reading B. The candidate accepts split satisfaction only if the counts agree. No controller object writes follow setup. Independent observer and saved XML check final effects.

D: producer/container exit0/errors[]. Unchanged F01 effect auditor exit0. First separately frozen notification auditor exit0/errors[], SUPPORT_MODIFY_DETECTION_SCOPED. Stable count0→0 and unsatisfied split; mutated count0→4 with false-positive split, rejected by changed-count guard. Saved/observed mutated state A1800/B2700; stable A1900/B2800. Original F01 false-positive is preserved.

C: image sha256:bab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d, CPU1, memory512MiB, networknone, user65534:65534, read-only source/writable output. No model calls; root filesystem not claimed read-only.

U: notification qualification for this property and schedule only. Four callbacks are not assumed to correspond one-to-one with two operations. A local count is not an authenticated or complete document generation. No complete mutation coverage, callback timing guarantee, atomic snapshot, later-writer safety, generic state oracle, task/model value or production adoption follows. The stable control is unsatisfied, so this study does not qualify a satisfied positive admission case. Callback completeness and acceptance eligibility remain separate unresolved gates.

Evidence: seven pre-run frozen sources including literal F01 controller and byte-identical effect auditor; two saved FODG files, initial/recorded writer prefixes, independent observer, original run and both audit logs/exits. FILES.json covers copied members; publication README, FILES.json and .gitattributes excluded from manifest. Attributes preserve bytes. Source/raw review supplements notification audit.

First result: https://github.com/Unjuno/agent-interface/issues/6259#issuecomment-5975248094
