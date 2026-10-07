# Preregistration — ROUTE-BLIND-ADJUDICATION-7436-T0-A01-20261004

## Provenance and allocation boundary

- Repository: `Unjuno/agent-interface`; source main commit: `0db425b379f9438bf6b13c95dce1b763750b06d5`.
- Additive branch: `research/7436-route-blind-adjudication-t0-a01-20261004`.
- Additive package: `research/analysis/route_blind_adjudication_7436_t0_a01/`.
- Output: `research/analysis/route_blind_adjudication_7436_t0_a01/results/`, required absent immediately before candidate invocation.
- Candidate and audit sources, fixture, construction tests, and six source files are SHA-bound by `PRELAUNCH_FREEZE.json`; that file's own digest is reported with the result.
- T0 is method-only and uses no human participant, model, network request, GUI, application, provider call, GPU, or external allocation.

## H / T / D / C / U

- **H:** For this finite synthetic corpus, the presenter will preserve the scoring rubric and evidence while withholding every explicit route/candidate/branch/predicted-winner canary; a custodian will deny route-map reveal until a complete valid score commitment; deterministic randomization will reproduce packet order; an independent audit will reject all eight preregistered effective mutations.
- **T:** Six synthetic packets (three strata × two routes) from `fixture.json` and the paired files under `source/`. Source directory and filenames contain route/candidate labels; metadata contains candidate, branch and predicted-winner values; summaries contain route labels. Candidate receives the fixture as custodian and emits only opaque episode IDs, stratum, evidence, rubric, and evidence pointers in the blinded view. It creates a synthetic score record from blinded evidence, attempts a reveal before commitment (must be denied), commits complete ordered scores, then reveals the escrow mapping. Auditor uses fixture plus raw candidate JSON and does not import candidate/presenter modules.
- **D:** `PASS_METHOD_SCOPED` only at 6/6 exact independently reconstructed packets, required rubric/evidence retained, zero explicit canaries in blinded JSON/output paths, exact seeded order and changed order under adjacent seed, precommit reveal denied, complete score commitment verified and correct postcommit mapping revealed, and all eight effective mutations rejected: route in metadata; candidate/route in packet filename; route in output path; predicted winner in summary; packet-order change; score change after commit; wrong evidence pointer; dropped packet. No-op mutation, leakage, premature reveal, changed evidence/rubric, malformed coverage, or accepted corruption is FAIL. Main movement before candidate, occupied output, missing provenance, or unavailable pinned runtime is STOP before invocation. Candidate nonzero exit means auditor is not run; no retry after either formal invocation.
- **C:** This is a single-process protocol/mechanics test, not a security boundary: source fixture and escrow are readable in the same checkout. Synthetic paired evidence may not reproduce natural route-identifying cues. Hiding explicit canaries does not establish that a human cannot infer route from evidence.
- **U:** Human judgment, false-positive/false-negative rates, route guesses, assessor variance, natural task evidence, machine-oracle accuracy, prospective route-blind effectiveness, and any user or product benefit are untested.

## Frozen commands and execution policy

1. Construction only: `python3 -I -B -m unittest discover -s research/analysis/route_blind_adjudication_7436_t0_a01 -p 'test_package.py' -v`.
2. Candidate exactly once: `python3 -I research/analysis/route_blind_adjudication_7436_t0_a01/candidate.py`.
3. Only if candidate exits 0, auditor exactly once: `python3 -I research/analysis/route_blind_adjudication_7436_t0_a01/audit.py`.

Container first was checked. OrbStack `docker info` reported Docker 29.4.0, Linux/aarch64; `docker image ls` failed because a containerd content-store blob could not be read (`operation not supported`), and Podman is absent. No image build/pull or retry is authorized in this allocation. Because this is deterministic standard-library T0 with no external behavior and the user prefers local iteration, use a host-only fallback and retain the infrastructure STOP; do not infer container isolation or enforcement.

This preregistration freezes a method probe only; it is not a human study and does not test the Issue's directional bias hypothesis.
