# Issue #8549 T0 A01 — method-only result

## Question and scope

This allocation tested whether a prospective second-alert study can hold its factorial stimulus conditions and score source-bound responses as specified. It did not test whether people miss a second alert after processing the first. No participants, model, GUI, OS input, user data, or consequential action were involved.

## Frozen method

The freeze is source commit `be4a25fcfa85d36559cfde6f752b25d2c11bd913`, based on main `a6343bb76e4dc0a4afa32a29c8a485a617faeff8`. The fixture crossed first-event demand (`process` / `task_irrelevant`) with 250, 500, and 2,000 ms inter-event gaps in four matched blocks, producing 24 schedules. The same two source-bound facts, two-event count, salience, display duration, and T2 response deadline were retained across factorial cells. Event order and screen position were counterbalanced; cell presentation order used the frozen seed. T2-only, isolated-T1, and persistent-history controls were labeled outside the primary factorial. Six synthetic response cases exercised correct, wrong-event, wrong-source, wrong-fact, late, and missing outcomes.

## Execution and result

The formal candidate ran once with `sh run_candidate_once.sh` (exit 0; 24 schedules, six response cases). The independent read-only auditor ran once with `sh run_auditor_once.sh` (exit 0). It reconstructed 24/24 schedules, independently scored 6/6 responses, reported zero errors, and rejected all 4/4 frozen mutations (missing trial, altered deadline, altered salience, and changed source score). The disposition is **`PASS_METHOD_SCOPED`** under the preregistered method gate.

Candidate raw SHA-256: `a0e2744e4990d3ed1b58dfddecb70ffde4df22bbca0c929361ee9c29c5f9f0d8`.

Auditor output SHA-256: `7e86049fce0d2896b01f6db58bfb33f8259df989a331bfd1751b5b985eafe035`.

Exact stdout, stderr, exit receipts, and hashes are retained in `raw/first-outcome/` and `OUTPUT_SHA256SUMS`. Frozen source/data hashes are in `SHA256SUMS`.

## Runtime and limitations

Host CPython 3.14.5 on macOS was used for this CPU/file-only method fixture. OrbStack reported Docker 29.4.0, but its read-only `docker ps` call failed with a containerd content-store missing-blob error. No container was started. This records a local runtime limitation; it is not a scientific finding about containers.

The result validates only this synthetic schedule, controls, response truth key, and auditor. It establishes no attentional-blink effect, participant response rate, practical alert spacing, human benefit, safety, or production policy. A human-effect test still requires a separate approved, consented, adequately powered prospective study. Issue #8549 remains open.
