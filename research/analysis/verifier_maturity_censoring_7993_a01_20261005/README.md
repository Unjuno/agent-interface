# Issue #7993 T0 A01 — outcome-maturity verifier-risk method slice

Status: formal A01 completed once: **`PASS_METHOD_SCOPED` for the frozen finite
synthetic method slice only**. This is not completion of Issue #7993's broader
pre-allocation gate; independent generated-cohort/superpopulation IPCW
evaluation remains untested. See [`RESULTS.md`](RESULTS.md) and `raw_a01/`.
See [`PLAN.md`](PLAN.md) for the frozen H/T/D/C/U protocol and decision gates.

The endpoint is the binary event that an executed proposal's narrow verifier
claim is contradicted by the final independent oracle. `candidate_input.json`
contains only checkpoint-visible observations; `oracle_input.json` is separate
and is read only by the independent raw auditor. The planned finite corpus has
25 snapshots, including the complete 16-mask independent follow-up enumeration.

The comparison deliberately separates complete-case risk, exact all-assigned
identification bounds, and a Horvitz–Thompson point estimate. The latter is not
a bound or risk certificate. Safe terminal stops and permanent unknown-cause
loss remain typed unknowns; they are not negative labels or administrative
censoring.

## Intended runtime and command

Use WSLc 3.0.1 with cached image
`python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
(linux/amd64, Python 3.12.14), `--pull never`, `--network none`, one CPU,
requested memory 512 MiB, read-only `/src`, and separate writable `/out`.
Construction tests and the one formal candidate/auditor invocation are
separate; only the latter can produce the study disposition. Preserve any
WSL/cgroup/swap warning. A configured memory limit is not proof of enforcement.

The formal container command will be:

```powershell
wslc run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume "${pkg}:/src:ro" --volume "${raw}:/out:rw" --workdir /src `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python -B run_experiment.py --output-dir /out
```

The host must capture WSLc stdout, stderr and exit status. The runner separately
captures candidate and auditor stdout/stderr, source hashes and process status
under `raw_a01/`. No candidate retry is allowed after the frozen formal call.

## Scope

This is a finite synthetic method check only. It is not a new conformal or
survival-analysis theorem, a live verifier calibration, a GUI/application
effect, a model or policy result, or evidence of runtime safety. Prior results
and dispositions for #5315, #6129, #6208 and #2279 are unchanged.
