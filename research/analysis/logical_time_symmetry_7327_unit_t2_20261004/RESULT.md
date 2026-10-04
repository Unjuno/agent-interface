# T2 result — explicit logical-time unit representation

Allocation `LOGICAL-TIME-SYMMETRY-7327-UNIT-T2-20261004-01`, Issue #7327. Frozen main `4d42238694c55aaa29bf47cb13a5b8d4c5d4074a`.

## H/T/D/C/U

- **H:** A genuine seconds-to-milliseconds representation of the same six exact-rational schedules, including all declared time values and event timestamps, yields equivalent normalized traces.
- **T:** One formal host candidate and one separate raw-only auditor after preregistration; standard-library Python 3.14.5; candidate and auditor each exit 0; retries 0. The candidate writes both labelled encodings; the auditor reconstructs expected encodings and traces and applies four corruption controls.
- **D:** **`PASS_UNIT_REPRESENTATION_SCOPED`.** Six of six seconds/milliseconds raw input pairs differ. All eight fields per scenario (48 conversions total), including `reference_period`, convert exactly; all seven disturbance timestamps convert exactly. The six independently reconstructed traces match across units. The auditor rejects all four mutation controls.
- **C:** This is only a finite synthetic rational-time model. It does not establish real system homogeneity or any GUI, model, physical-time, controller safety, speed, or accelerated-runtime result.
- **U:** Whether explicit unit conversion preserves this exact fixture's logical trace; broader transformations remain untested.

## Execution and provenance

Formal commands:

```sh
python3 candidate.py spec.json output/candidate.raw.json
python3 audit.py spec.json output/candidate.raw.json output/audit.receipt.json
```

Both formal commands exited 0. Candidate summary: six rows. Auditor receipt: `PASS_UNIT_REPRESENTATION_SCOPED`, 6/6 scenarios, 4/4 mutation rejections, no errors. A separate host-side review recomputed all 48 field conversions, seven event conversions, raw-pair distinctness, and six trace equalities; it passed.

Construction preflight ran before the T2 freeze in a separate `preflight/` directory and is excluded. Its candidate/auditor outputs happen to be byte-identical to formal outputs because this fixture is deterministic; the formal invocations were still separately executed once each after the GitHub preregistration. T1's first candidate failure is preserved in its own package and is not pooled.

The OrbStack Python image could not be inspected because its cached content blob returned `operation not supported`; no pull or retry was attempted. Per the Issue #7327 method-only protocol, this CPU-only rung ran on host Python with the standard library, no network, GUI, model, game, or input. No container resource-limit or speed claim is made.

Source SHA-256: `spec.json` `ddf948f91cb8943211a560737b4314344e0aecaf52303e22499e58139a5564b2`; `candidate.py` `63db6fbd98d2658b3746c3c562d03672f1933a8883564778cd72aa7375263116`; `audit.py` `04a4cb67f66bd988baff8e3f248cb68bd4bcded602fac5a9d11d7de15fde12e7`. Candidate raw SHA-256 `9df949d948d83ea4ac9a682606345e91f944e9cb0968f09ebd676a718cba1729`; audit receipt SHA-256 `e2cff7fb295d5688a643a211fec0f177e859e6c1ea3ffa3e8742ae949be1cb26`.

This result addresses only the missing UNIT_REPRESENTATION leg identified in T0. Issue #7327 remains open; nonzero fixed backend delay, nonzero quantization, physical/semantic rate transformations, and live-control relevance still require separate evidence.
