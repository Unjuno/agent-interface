# A18 retained-raw boundary construction

Parent scientific question: Issue #5156; supports #59's input-release instrumentation.
Worker: /root, FINAL-v5. Base: `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`.
Run ID: `5156-A18-RETAINED-BOUNDARY-WSLC-C01-20261003`.

H: A18's retained validator does not cover global chronology, teardown identity,
and exact activity-counter types; a supplemental validator can enforce these
checks without changing the historical source/raw or any input behavior.

T: One immutable positive raw and ten predetermined single-factor corruptions.
Eight new negative controls plus two existing bracket/keymap controls. Compare
the retained audit function with additive checks, then independently verify each
contradiction directly from retained mutated JSON, without importing either
validator. Source/freeze identity, ordered census and output hashes are checked.
Construction diagnosis and red/green host regression precede the pinned run;
the eight false accepts were already observed. This is confirmatory construction,
not a blind scientific discovery or the consumed A18 formal allocation.

D: Retained-auditor coverage FAIL if any invalid row is accepted. Supplemental
construction PASS only if the unchanged original is accepted and all ten negatives
are rejected. Independent audit must reproduce the contradiction witnesses and
all output hashes. Missing source, failed launch, exception or nonzero process
exit is STOP; preserve output, no retry of C01. Candidate=1; auditor=1 only after
candidate exit 0; timeout 30 seconds per subprocess; maximum output 1 MiB.

C: The original six controls tested local brackets and booleans, not these
additional contracts. A mutation is a coverage counterexample, not evidence that
the retained live raw is fabricated or that input failed. The supplemental
checker composes with the unchanged auditor rather than superseding all gates.

U: No continuous physical occupancy, application delivery, input safety rate,
MAP01 efficacy or latency gain. Only observed event times use the candidate clock;
future lease deadlines are excluded from the containment check. Cancellation's
`requested_ns` is sampled after setting the cancel flag, so it is not used as a
lower bound on cleanup onset. The cancel teardown's null intent is valid after
the owning intent has already been released. Keymap snapshots were reduced to
booleans in A18; this construction cannot recover their original bytes.

Environment: cached Python 3.12.14 linux/amd64 image ID
`sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`.
WSLc, pull never, network none, read-only source, dedicated output, CPU 0.5,
requested memory 128 MiB. Cgroup enforcement is unknown until launch diagnostics;
do not infer enforcement from the request. No GPU, X11, daemon changes or downloads.
Deadline unknown; this bounded construction needs less than 60 seconds after launch.
