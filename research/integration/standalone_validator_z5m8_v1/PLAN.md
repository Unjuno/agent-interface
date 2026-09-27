# Standalone static validator — #4343 / z5m8

## H / T / D / C / U

H: exact promoted validator and core bytes can run as a small standalone zipapp
outside a checkout with unchanged reports and exits. Existing unified runtime,
core, validator and dispatcher are NOT modified.

T: one retained engineering allocation, 16 fixed inputs in CASES.json x2 entry
forms =32 subprocesses. Seven valid, seven invalid, two input-loading failures
per entry. Run both with Python -I -S -B, display variables and PYTHONPATH unset,
from a fresh directory outside source. Direct reference uses runpy.run_path on
the exact validator file with the source root added explicitly; it is NOT the
full public -m CLI initializer. The candidate invokes the .pyz normally.
Build twice and require byte equality. No model, native input, GUI, package
installation or experimental network. Timeout10s per child; first failed or
incomplete orchestration is retained, not rerun or replaced.

D: every expected category/exit, complete32-record ordering, unchanged input
hashes, byte-identical paired stdout, no stderr, static-only result fields,
exact archive inventory/source mappings, deterministic artifact and actual
launcher exit0. Read-only separate audit must have no errors and all10
predefined copied-record controls must reject. Complete semantic contradiction
is FAIL; missing source/process/coverage/control evidence is HOLD/STOP. A valid
static result is not live authority, a supported backend, or task success.

C: source packaging changes the module entry location, not validation logic.
No complete API/CLI/MCP initialization comparison. The empty generated runtime
initializer is packaging plumbing, not a backend stub; the full unchanged core
initializer is retained. All five upstream files must match BASELINE.json.
Native backend code and cli_v1/__init__.py are not included. Library import
semantics are supplied by Python, not proven from hashes.

U: tested here only on supplied Linux x86_64 / CPython3.13.5. No Docker image
attestation, Windows/macOS test, calibration, benchmark, task/model/token gain,
security sandbox or production release claim. Python3.12 is an implementation
minimum, not a tested platform claim in this local allocation. Same-author
independent audit code is not external human review.

## Ownership and chronology

Base main9bc9343564a1522df2cf62f4c5cfcdb38194b7c4. New builder and unit test only
under runtime/distribution_v2; this additive research directory and one new
focused CI workflow. No old results or blocked publication payload reused.
Construction01 failed all10 methods before building: test source-root had one
extra parent component. Original test/stdout/stderr are retained locally;
CONSTRUCTION_INCIDENT.md records exact cause and hashes. Corrected construction
passes10 methods. These tests are separate from the32 retained invocations.
No full matrix evaluation before public freeze.

Local source is a five-file exact Git-blob-verified snapshot, not a complete Git
checkout. Artifact BUILD.json must say source_kind=directory_snapshot and
source_revision=null. BASELINE.json supplies the verified upstream identity.
A user building from a real checkout gets HEAD-pinned committed source bytes.

## Conditional argument and units

All five source files are copied whole and verified by byte hashes. Placing the
unchanged validator at archive __main__.py invokes its existing main function;
its imports resolve to the unchanged included core package and Python stdlib.
Under identical input bytes, interpreter and relevant environment, this changes
neither its validation rules nor its static-only output contract. Archive-import
and path behavior are the environment-dependent residual tested here. This is
not a proof against arbitrary Python implementations or malicious dependencies.

Counts are invocations/files; sizes are bytes, not tokens, characters or SI
physical quantities. Input SHA256 hashes the exact UTF-8 byte sequence, including
its terminating newline; source mapping checks exact bytes at the archive path.
No latency threshold or invented combined measurement uncertainty is used.

## Roadmap and reproduction

Exact-source intake -> excluded construction -> public source/case/auditor
freeze/readback -> one32-invocation matrix -> raw audit/10 controls -> full
small readable evidence PR -> exact-head applicable checks/review -> qualified
main merge/readback. #3850 and the global ROADMAP stay open.

Build from an ordinary checkout:

```sh
python -m runtime.distribution_v2.build_validator --out /tmp/validator.pyz
python -I -S /tmp/validator.pyz --program program.json
```

Build outputs must not preexist. A multi-file output write is not an atomic
publication transaction; failures must be observed by the caller. Trusted source
and output directories are assumed.

Primary references: Python3.13 zipapp application archive format and command-line
-I/-S documentation (docs.python.org). They specify interpreter behavior, not
validation of this artifact or empirical model benefits.
