# Current-evidence scalar admission repair — #57

The promoted core accepted malformed current evidence even though it already
validated the program's own source and lease values. `now_ns=NaN` bypassed the
lease comparison; negative or boolean time was accepted; boolean/float current
sequence and binding values compared equal to integer `1`. Three calls to the
existing `_bounded_int` helper close this direct-call boundary. Valid inputs keep
their current expiry, freshness and capability behavior.

This is an ordinary, input-free engineering repair on Windows 11 / CPython
3.12.10, not a formal scientific allocation, live exploit demonstration or
backend qualification. Intake main is
`11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`; original contract blob is
`10786d38b98fc8988108230fe59ba8df9ed17cb4`. `baseline_contract.txt` is an inert
byte-exact source snapshot for separate regression replay. Historical studies
and all other workers' paths remain untouched.

## Contract and decision

| 引数 | 日本語の意味・定義 | SI単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| `now_ns` | 呼出し元が提供する現在の単調時計値 | ns（10⁻⁹ s） | 0〜2⁶³−1。時計領域の一致は呼出し元の責任 | `int`、boolを除く |
| `current_observation_seq` | 現在の観測の連番 | 1（無次元） | 0〜2⁶³−1。プログラムのsourceと比較する | `int`、boolを除く |
| `current_binding_revision` | 現在の対象bindingの版番号 | 1（無次元） | 0〜2⁶³−1。プログラムのsourceと比較する | `int`、boolを除く |

- **H:** Exact bounded integer validation of current evidence refuses malformed
  values before freshness/capability checks, without changing valid behavior.
- **T:** Test-first direct core regression; full core suite; exact production
  Win32/X11/Quartz session code with a recording backend; a separate raw-only
  auditor with explicit expected outcomes and corruption controls.
- **D:** Malformed context returns `Admission(False, 'INVALID_PROGRAM', ())`;
  valid controls retain admission and refusal precedence; invalid session rows
  never call preflight, execute or release; raw-only audit has zero errors.
- **C:** Public CLI/API dispatch already rejects some non-integer generation
  values. This defect is the direct core/session boundary and should not be
  described as a demonstrated public GUI attack. Existing integer comparisons
  suffice after type/range validation; no new parser or authority mechanism.
- **U:** The spy is not an OS backend. Clock-domain consistency, physical input,
  concurrency, application effect, recovery efficacy, resource enforcement and
  latency are unmeasured. Hosted/cross-platform CI is not claimed passed.

The existing expiry comparison (`now_ns > expires_at_ns`) is retained, including
admission at exact equality. Changing deadline inclusivity is a separate decision.

## Executed checks

| Check | Observed result |
|---|---|
| First RED regression | 8 tests; exit 1; 44 failing subtests/assertions, 4 type exceptions |
| Separate exact-baseline regression replay | Same 8 tests; exit 1; 44 failures, 4 exceptions |
| Repaired complete core suite | 73 tests; exit 0 |
| Direct nine-control baseline/repaired comparison | 7 malformed admissions before repair; all 7 structured refusals after repair; valid/expired controls unchanged |
| Three session wrappers × seven cases | 21 rows; 18 refusals with zero preflight/execute/release calls; 3 valid controls each call execute once on the spy |
| Raw-only session audit v1 | 21 rows; zero errors; four frozen corruption controls rejected |
| Raw-only session audit v2 | 21 rows; zero errors; five corruption controls rejected, including a boolean counter |
| Core compile and platform doctor | Exit 0; doctor reports native backend not loaded and no input authority |

Session source bytes are unchanged. Private placeholder modules replace the
native `.backend` imports; the real session code and patched core run unmodified.
`spy_execution_count` counts calls to a recording object, not physical emissions.
The auditor imports no core, session or backend code and checks literal expected
rows. Source identities are in `PROVENANCE.json`; file hashes are in `SHA256SUMS`.

## Reproduction

From the repository root, run:

```powershell
python -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v
python -m compileall -q runtime/core_v1
python -m runtime.core_v1.doctor
python research/integration/current_evidence_scalars_57_20261003_45e9/session_probe.py > sessions.json
python research/integration/current_evidence_scalars_57_20261003_45e9/audit_sessions.py sessions.json
```

`core_probe.py` takes a contract source path; `baseline_regressions.py` uses only
the retained inert baseline. Ordinary repair checks may be repeated. No consumed
formal allocation is replayed here.

## Evidence custody and integration state

The public first-check logs retain complete assertions and process outcomes,
with the local checkout prefix replaced and line endings normalized to LF.
During publication preparation a repeated finalization script overwrote the
private unredacted copies of the first red/green/session/audit/compile/doctor
logs with those derivatives. Their exact original byte custody is therefore
unavailable; it is not represented as recovered. The separately identified
baseline regression replay and subsequent check originals are retained
privately, and original source bytes remain exact. No result is relabeled or
substituted for the first outcome. The finalizer now preserves existing private
copies rather than replacing them.

Current status: local repair verified, proposed delivery only. FINAL-v5
non-author content approvals, current-main combination verification, mandatory
GitHub rule checks and conditional application are outstanding. No shared
input/GPU/runtime resource was acquired. No container, model or GUI allocation
was used. A fleet deadline has not been independently confirmed and is not
reset by this work.
