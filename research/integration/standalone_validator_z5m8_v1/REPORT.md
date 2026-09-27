# Standalone static validator — retained engineering result (#4343)

Decision: **PASS_STANDALONE_VALIDATOR_ENGINEERING**.
This qualifies a separate static-validator artifact on the measured Linux/Python
condition, not runtime action admission, model benefit or a finished release.

## Why this changes the usable interface

At intake main `9bc9343564a1522df2cf62f4c5cfcdb38194b7c4`, the validator from
#4336/#4338 is available as a source module, but the explicit unified-archive
allowlist omits it. This additive builder emits a standalone `.pyz` using the
unchanged validator as its exact `__main__.py`, plus four unchanged core modules.
The dispatch-oriented `runtime.cli_v1/__init__.py` and native backends are not
included. Existing dispatcher, validator, core and unified builder are unchanged.

## Source-first chronology and first outcome

Source/corpus/auditor freeze was published and read back at
`e4d94a3102464f062b9c9ac383199130595c1742`, Issue comment5825606828,
before the retained matrix. Five upstream files match their exact main Git blobs;
nine study files and both new builder/test blobs match local bytes. The provided
execution source is an exported five-file snapshot, NOT a full checkout.
BUILD.json therefore explicitly says `directory_snapshot` and null revision;
BASELINE.json records its exact upstream main identity. Normal builds from an
actual Git checkout read committed HEAD, not dirty working files.

The single retained allocation completed32 subprocess calls over16 exact inputs.
All16 direct-source/archive pairs have byte-identical stdout and matching exits.
Each entry returns7 static-valid,7 static-invalid and2 input-loading errors.
All32 stderr streams are empty and input files are unchanged. Exit0 denotes static
validity, exit1 invalid program and exit2 loading/JSON error; none is task success.
All responses retain side_effect_authority=false, backend_checked=false,
runtime_admission=not_evaluated and task_success=null.

Positive controls include observe, key repeats, Unicode text gaps,128 expanded
operations and a statically valid expired lease. Refusals include wrong schema,
missing w/h, unknown operation, Boolean repeat,129 expanded operations and a
non-object input. Unknown-field compatibility stays unchanged. Diagnostic output
does not echo the PRIVATE_PAYLOAD_87 marker. These are finite contract tests,
not a population reliability sample or adversarial-input security assessment.

## Artifact and audit

- Standalone artifact: **28437 bytes**,7 entries, no third-party dependencies.
- SHA256: `238171672ecc368356a3ced49c5b60d81072400cea28136ae67849bb4958e017`.
- Two builds before the matrix are byte-identical.
- Frozen raw-only audit: **500 checks, errors=[]**.
- Effective copied-evidence controls: **10/10 rejected**, each unmodified copy
  first passed the auditor. Controls do not rerun validation programs.
- Actual external matrix launcher: exit0, timeout=false.
- Construction02:10 focused unit methods passed before freeze. This includes
  exact source inventory, deterministic rebuild and real Git dirty-copy isolation.
- Scientific reruns, replacements, exclusions and post-result tuning:0.

The direct reference uses runpy on the original validator with its source root
explicitly inserted. It is NOT a full public CLI/API/MCP initialization test.
The archive runs normally outside the checkout under Python -I -S -B with
DISPLAY/WAYLAND_DISPLAY/PYTHONPATH unset. Archive import behavior is the tested
residual; no independent tracing claim about every possible system call is made.

Environment: supplied Linux6.18.44 x86_64, CPython3.13.5/GCC14.2.0, standard library,
no Docker image identity, no CPU/frequency pinning. Python3.12 is an implementation
minimum; this local matrix tested3.13 only. No GUI/native input, model/provider,
human trial, package installation, performance benchmark or experimental network.
Sizes are byte counts, not characters or tokens. No calibrated physical
uncertainty or confidence interval is manufactured.

## Evidence retention and incidents

`raw_parts/00.txt` through07 are lossless zlib/base64 storage of the ORIGINAL
34288-byte RAW.jsonl, not regenerated outcomes. RECORDS.json binds both encoded
and decoded bytes. Exact original subprocess argv/cwd/start/end/stdout/stderr,
exits and input identities are preserved. LAUNCHER.json and RUN.json are original
receipts. The untouched RUN status precedes the subsequent successful AUDIT.

`verify_retained.py` reconstructs the original raw bytes, rebuilds the exact
archive from unchanged source bytes in a temporary no-Git snapshot, requires the
original artifact/manifest identity and byte-identical frozen audit. It never
starts the validator or the consumed matrix. The generated binary is reproduced
mechanically rather than stored as another large source-code duplicate. The
original binary and all initial construction files also remain in the local
conversation handoff. Unit/CI reruns are not new engineering-matrix samples.

Construction01 had a test ROOT path error:10 setUp failures before any artifact
build. The source root was corrected before construction02 and freeze. The full
failed test and logs are retained locally; CONSTRUCTION_INCIDENT.md records exact
hashes and the limitation that these initial failure bytes are not fully mirrored
in GitHub. There was no matrix failure or replacement.

Publication also exposed an assistant transcription error in the first long
base64 upload. That unreferenced Git tree was never attached to the branch. Eight
short parts were then uploaded, each matched to its exact local Git blob, and
joined/decompressed to the unchanged RAW.jsonl digest. This is neither GitHub
corruption nor a tool safety block. PUBLICATION_INCIDENT.json retains it. Prior
unrelated blocked source/payloads were not retried or included.

## H/T/D/C/U and integration boundary

H: exact static source can be packaged without changing diagnoses.
T: frozen16 inputs/two isolated entry forms and deterministic build checks.
D: complete32 records, expected categories, exact paired output/source/hash
identity,500-check audit and10 effective controls passed.
C: the same author wrote the separate auditor; this is not external human review.
U: cross-OS launch, live backend/lease correctness, model repair/token/latency
benefit, hostile dependencies and full product distribution remain untested.

This new builder can be integrated only after exact-head applicable CI and scoped
review. #3850 and the repository ROADMAP remain open. No branch with pending
provenance or dependent PR is deleted by this work.

## Usage

From a checkout containing this builder (outputs must not already exist):

```sh
python -m runtime.distribution_v2.build_validator --out /tmp/validator.pyz
python -I -S /tmp/validator.pyz --program program.json
```

Read-only evidence reconstruction:

```sh
python -S -B research/integration/standalone_validator_z5m8_v1/verify_retained.py
```

An expired lease may be statically valid: live authority remains unevaluated.
Building the three output files is not atomic across all files; callers must
retain any partial-output failure. Trusted source/output directories are assumed.
The separate artifact avoids expanding native execution capability merely to
inspect a program. It is not the existing unified runtime archive or an official
GitHub Release.
