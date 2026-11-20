# Issue 7822 A03: uncontrollable-closed finite cross-check

Allocation `BP-7822-LINUX-A03-20261006`; intake main `a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028`.

This is a new method cross-check, not a rerun or repair of A01/A02. Original A02 candidate blob `32f363f8dac04b66fb02eb65d91901ac03c0cfef` is unchanged. Its stationary-policy/cycle oracle is separately implemented and imports no candidate. No old result, runtime or workflow changes.

## Prospective H/T/D/C/U

H: the unchanged horizon solver agrees with independent complete stationary-policy enumeration; filtered safe-graph coaccessibility need not equal existence of an implementable safe/evidenced nonblocking supervisor, since uncontrollable events cannot be deleted. A diagnostic difference alone is not a solver defect.

T: 2,401 graphs enumerate four slots q0->q0, q0->q1, q1->q0, q1->g, each absent or C/U with safe+evidenced, unsafe+evidenced, or safe+unobserved attributes. Add initial-goal, direct-goal, three-step and optional-dead-end controls: 2,405 total. Cap 3, terminal goal, fully observed finite graph, no fairness assumption. Preserve complete input graphs and returned policies. Independent oracle enumerates every controllable subset while retaining all uncontrollable events; reachable compliance, coaccessibility, deadlocks, cycles and longest paths are recomputed without the candidate's winning-set recurrence.

D: require exact corpus/source identity, zero horizon or policy discrepancies, no completion/action claim, and all 12 effective well-formed mutations rejected. Diagnostic disagreements are counted separately with witnesses. Any solver mismatch is FAIL; missing source/execution/evidence is HOLD/STOP. Candidate once, then only after exit zero auditor once, with exclusive consumed markers. No rerun, replacement, pooling or post-result tuning.

C: trusted complete public graph, correct evidence flags and terminal goal; event-step semantics allow an enabled event to occur, but impose no real-time bound. A stationary-policy oracle is sufficient for finite fully observed sure reachability by rank-decreasing memoryless choices; complete argument and variable/unit table are in the frozen PROTOCOL.md.

U: provided Linux x86_64 execution container, CPython 3.13.5, stdlib only; no Docker/WSLc/OrbStack image attestation or shared-workstation allocation. No model/provider, GPU, GUI/input, user data, installations or experimental network. Finite method result only, not live progress, wall-clock deadlines, task usefulness or runtime safety. Same-author separate implementation/process is not external human review.

## Complete pre-execution source commitment

All 22 source/freeze/construction files are stored losslessly in three binary parts. Concatenate SOURCE.part00, SOURCE.part01, SOURCE.part02 in that order to obtain SOURCE.tar.xz (12,136 bytes), SHA256 `d0f6121919b57cfea609d5a3824259317d0a781cb340bac59a2709b4137c3d09`. Its 22 regular members include all seven Python modules, full PROTOCOL.md, ENVIRONMENT.json, FREEZE.json and 12 construction records. Full source is in this archive before measurement; it is not claimed to be all rendered inline. The subject is also directly readable as candidate_a02.py.

FREEZE.json SHA256 `9ff4c5ca178bb49232dbb6c5161af07ed019d5554ba74b77f048e6156a9368c5`; it pins 21 other members. All source/blob hashes were verified locally before publication. Construction includes the deliberately failing initial oracle stub, seven expected red assertions, two 10-test green receipts, four disjoint small subject probes and independent corpus-recipe equality. No scored 2,405-graph candidate invocation has occurred at this commitment.

For extraction, first verify the concatenated archive digest, use a fresh trusted directory and Python 3.13 tarfile data filtering. Extraction executes no study. From that new directory the prospective commands are `python -S -B invoke.py candidate` and, only on observed exit zero, `python -S -B invoke.py auditor`. Each role has a 30-second subprocess bound and retained actual exit/stdout/stderr receipt. The consumed identity must not be rerun later. Read-only audit of retained bytes and unit regressions are allowed.

All work is confined to this additive namespace and its Issue-owned branch. No new Issue is needed. Source-readback precedes execution; first outcomes will be added without rewriting this record. Merge requires applicable exact-head checks and scoped independent review.
