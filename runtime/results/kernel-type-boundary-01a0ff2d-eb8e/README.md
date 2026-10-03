# Nominal record types at the kernel lifecycle boundary

Issue: #6875. Worker: `01a0ff2d-eb8e-70e0-82bb-ba3bf0c79b5c`, FINAL-v5. This additive package retains an ordinary engineering characterization and an isolated candidate. It changes no shared runtime, historical result, workflow, dependency, formal allocation or main branch.

## Result

On exact source main `f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549`, the lifecycle refuses a shaped observation but accepts six other malformed record shapes. Matching identifiers and state prerequisites allow SimpleNamespace records to bypass the constructors' binding-digest, allowed-action, nonempty-action, interval and effect-evidence validation. A begun cancellation also accepts a namespace merely asserting released=True. An invalid shaped effect advances to VERIFIED; this is a synthetic API outcome, not a physical effect.

Seven new refusal tests retain the first failure: observation control passes; six other assertions fail, process exit 1. The isolated candidate adds 12 lines in six missing isinstance guards, after applicable stage checks and before dereferencing or storing the supplied record. The candidate plus the existing 18 kernel tests passes 25/25 normally and 25/25 with Python -O, both exit 0.

| New finite matrix | Exact baseline | Isolated candidate |
| --- | ---: | ---: |
| Total ordinary construction cases | 28 | 28 |
| Valid typed transitions accepted | 7 | 7 |
| Malformed shaped records accepted | 6 | 0 |
| Invalid inputs refused as ContractError | 4 | 21 |
| Invalid inputs producing AttributeError | 11 | 0 |
| Refusal mutating lifecycle state | 0 | 0 |

The matrix is seven entrypoints (observation, binding, authority, begin, execution, effect, begun stop) by four supplied forms (valid typed record, shaped namespace, None, unrelated object). It is finite enumeration, not independent statistical trials or a reliability rate. A baseline audit PASS means accurate reconstruction of the retained gap, not a correct baseline.

The raw-only auditor imports no kernel, candidate, probe or test helper. It reconstructs literal typed fixtures and prerequisites, all 28 case identities, supplied shapes, argument identity, accepted transition/mutation, exception class and terminal outcome, using recursive type-sensitive JSON equality. Initial audit passed but anchored parts of the prerequisite interpretation to the typed rows. This was strengthened before publication to require independent literal prerequisite/typed bytes; both original audits remain retained as v1. The final v2 audit passes the same unchanged raw files and rejects 10 effective copied-output controls: missing/duplicate rows, swallowed refusal, refusal-state mutation, changed shaped input, bool-to-int terminal claim, fabricated terminal claim, changed argument, changed typed fixture, changed prerequisite. Candidate/probe executions were not repeated for this auditor improvement.

Baseline raw SHA256: `97e36f43460e50d0d565dbcda6c269eee1dac895ab3dc2e5f4a762477096cf3f`.
Candidate raw SHA256: `9a3e0e5b4f7d7901cc72ee1fe35cbfd7051bdf2751045afd8727d5e42e21d19d`.
The gzip/base64 projections are reversible and checked against these exact bytes before publication. Original raw JSON is available in this worker's local outputs; the committed projection preserves all bytes. Every published package file except the manifest itself is SHA256-listed.

## Source and execution

`source-git-pins.json` pins five original source Git blobs to the source main above. All five local baseline byte strings were recomputed as Git blobs and matched the pins exactly (not merely equivalent text). `runtime/kernel/` is that retained baseline; `candidate/runtime/kernel/` copies it with only lifecycle.py changed. `candidate.patch` is the 12-line isolated change. The seven-control test file is copied unchanged under candidate/ so the original commands can run there. The package manifest binds source and harness bytes separately from raw data.

Executed on Windows, native CPython 3.12.10, with only local synthetic records. Commands below are ordinary repeatable engineering checks, not fresh formal allocations. Original test/probe/audit stdout and exact child process exit-code files are retained; the outer PowerShell command succeeded after recording failing Python exit 1. No failing outcome was replaced.

```text
# From package root, before repair (expected six failing assertions)
python -B -m unittest test_type_boundary -v
# From candidate/
python -B -m unittest test_type_boundary runtime.kernel.test_kernel -v
python -O -B -m unittest test_type_boundary runtime.kernel.test_kernel -v
# From package root; output destinations must be fresh
python -B probe.py . baseline new-baseline-raw.json
python -B probe.py candidate candidate new-candidate-raw.json
python -B audit.py new-baseline-raw.json new-baseline-audit.json
python -B audit.py new-candidate-raw.json new-candidate-audit.json
```

To inspect the retained raw, decode the base64 text then gzip-decompress; verify its SHA256 before using audit.py. The auditor creates output exclusively rather than overwriting a retained receipt. The probe does not invoke a backend; the ordinary existing unit suite uses its own FakeBackend, never platform input. No container, WSLc, model, GPU or shared lease was used.

## Scope and integration conditions

This checks nominal class membership on declared sequential API entrypoints. It does not defend against hostile Python subclasses, object.__setattr__ on frozen records, arbitrary in-process code, concurrent callers or trusted-clock violations. The stop guard is scoped to AUTHORIZED, where release is required; optional release arguments in pre-authority states are outside this characterization. No real-app effect, physical release, exactly-once behavior, latency, token saving or user-task benefit follows.

Related #2333/#3062/#3089 malformed/cleanup evidence, #5215 temporal receipts, #6852/#6853 duplicate begin, #6855/#6861 release lower bound, and #6864 begun cancellation freshness remain unchanged. Existing owners retain shared runtime files. A future promotion must compose with their exact accepted changes, recheck current source/dependencies/tests, and obtain assigned FINAL-v5 nonauthor content votes plus an exact current-base tree check and applicable repository rules. This additive evidence PR itself also remains subject to review; publication supplies no merge authority.


## Publication derivative v2

The original first execution records are retained unchanged in this worker's local evidence. This public revision replaces private local path strings in before-tests.txt; PUBLICATION.json binds original/published hashes and the exact transformation. Source, fixtures, raw outcomes, counters, UTC times, process exits and source freeze remain unchanged. The public receipt/log is a disclosed derivative, not the original byte string. No candidate, formal allocation or test was rerun. Earlier public commits already contained the original paths; this forward update does not erase that history.
