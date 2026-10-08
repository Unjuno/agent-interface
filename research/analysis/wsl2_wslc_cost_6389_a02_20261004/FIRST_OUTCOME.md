# A02 start-gate outcome — STOP_MAIN_ADVANCED_BEFORE_CANDIDATE

Allocation `6389-wsl2-vs-wslc-belief-replay-a02-20261004` is terminal. No
candidate, auditor, container, retry, or formal output was produced.

The freeze was committed and preregistered against main
`13bab54ea6d91978247ecc1b70e5060db752367a` at commit
`65f7edb7`. The immediate pre-candidate fetch observed main advance to
`2ed11c5552956499454e8a99acf5a2f374106d34` before any
candidate invocation. A02 therefore stopped under its explicit frozen
current-main gate. Candidate=0; auditor=0; retries=0; WSLc candidate/auditor=0.

The intervening main changes were unrelated to this experiment's source and
result paths: no path changed under the frozen #5368 workload, A01, or A02
directories. This source non-overlap does not retroactively clear A02's
start-gate STOP or authorize running under its old freeze. The A02 source,
construction tests, and preregistration remain immutable. Construction gate
was 3/3 PASS; AST and protocol hash checks passed before the main comparison.

A03, if run, requires a fresh current-main freeze and a separate additive
path. It must not amend A02 or pool any measurements from A01.
