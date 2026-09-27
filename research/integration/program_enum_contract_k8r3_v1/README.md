# k8r3: enum diagnostics survive standalone packaging

**PASS_ENUM_CONTRACT_ENGINEERING**, one prospectively frozen engineering
comparison. This is supplemental verification under #3850. #4369/e9q4 owns the
shared-core implementation; this PR changes no production runtime file.

| Per 123 inputs | Pinned baseline | Local three-guard proposal |
|---|---:|---:|
| Valid input, same capabilities | 33 | 33 |
| Invalid input, indexed ContractError | 54 | 90 |
| Core/admission TypeError | 36 | 0 |
| Static-invalid report | 90 | 90 |

The baseline static inspector already rejects all90 invalid inputs. The defect
is missing typed core refusal and operation location, not demonstrated unsafe
native input. All87 unaffected semantic reports match. Both versions' complete
static reports match their unchanged-builder standalone zipapps for123/123
inputs. No CLI/expander/default was modified. Source indices0/1/1 map to expanded
indices0/2/5 for plain/repeat/gap contexts. The five test methods also retain six
synthetic admission refusals: expired, stale observation, stale binding,
unavailable capability, permission required and unsupported coordinate frame.

246 fresh isolated CLI processes, two workers and the measured command completed
with recorded exits; no timeout, stderr or repeated retained invocation. Every
CLI is Python -I -S -B without display variables. This is the provided Linux
CPython3.13.5 container, not an image-attested Docker/OrbStack replication. No
backend/GUI/input/model/provider/task call occurred. Synthetic admission is not
live authority. There is no speed, token, recovery-quality or product claim.

## Provenance and scope

Base4a1f3957e91b412a64769199f78f2c4b0102d28b. Public source/gate commit
d203318c3c8b6a2067658beb79e91ee5376098c6 preceded the retained comparison;
#3850 comment5832622924 records the exact command. All9 published readable file
identities matched before execution. FREEZE binds21 local source/fixture files.
All six baseline source files match their complete upstream Git blobs. Candidate
core blob9cc6f4b76516ff17deca1cdf201346e18aaf90f3 is a local test fixture, NOT an
assertion that e9q4's eventual source has that identity. Compare complete bytes
before transferring this evidence to another revision.

The separately implemented raw checker imports no runtime or runner. It reports
zero errors and rejects8/8 effective copied-record changes, including boolean
indices/exit status; no-op detection compares serialized types rather than Python
numeric equality. Same-author verification is not independent human review.
All21 frozen sources and both zipapp member-to-source mappings match after run.

The complete48 original files plus manifest are retained in eight checked XZ
archive fragments: both full source trees, all246 raw CLI/core/admission/static
records and inputs, actual process receipts, two generated zipapps, exact plan,
freeze, auditors, unit outputs and excluded construction. Four CLI construction
cases and two core probes are not pooled. No local failure or formal rerun is
hidden. The test corpus was development-known; this is engineering verification,
not blinded science or natural error-rate measurement.

## Read-only reproduction

Run `python -S -B verify_evidence.py`. To keep restored files use
`python -S -B verify_evidence.py --out /absolute/new-directory`.
This verifies all member hashes and frozen sources, then reproduces both retained
raw-audit/control outputs byte-for-byte. It never runs measure.py, a GUI or native
backend. Trust the local destination parent; this is not an adversarial extraction
sandbox. See EVIDENCE.json for exact archive/part identities.

The readable test_program_enum_types.py is a handoff copy intended for placement
under runtime/core_v1 in the restored candidate tree; do not run it as a standalone
research-path test. To run it there: from restored/candidate use
`python -S -B -m unittest -v runtime.core_v1.test_program_enum_types`.

Integration decision: use existing indexed ContractError handling for invalid
JSON enum fields, and retain static validity versus live authorization distinctions.
Keep #3850, #4369 and the global roadmap open. This additive evidence does not merge
a competing core patch or alter another worker's allocation.
