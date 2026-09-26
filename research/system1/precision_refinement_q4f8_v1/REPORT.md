# #4400 — selective original-precision refinement

**PASS_SELECTIVE_PRECISION_CONTRACT_SCOPED. Evidence-only; no production/default change.**

## Decision

The declared binary protocol resolved all64 original observation decisions exactly with SELECTIVE64 and ALWAYS64. COARSE_ONLY made38 correct definite decisions and returned26 UNKNOWN. Selective original-precision replies resolved those26; all four separate unavailable/inconsistent/nonfinite control replies remained UNKNOWN. No currentness, source authenticity, physical safety or action permission is inferred.

Actual bidirectional application-protocol bytes,16 sources per corpus:

|Ambiguous sources|COARSE_ONLY bytes / UNKNOWN|ALWAYS64 bytes|SELECTIVE64 bytes|SELECTIVE64 vs ALWAYS64|
|---:|---:|---:|---:|---:|
|0/16|544 /0|800|544|-32%|
|2/16|544 /2|800|644|-19.5%|
|8/16|544 /8|800|944|+18%|
|16/16|544 /16|800|1344|+68%|

Every ALWAYS64 and SELECTIVE64 corpus has8 VALID and8 INVALID, zero wrong decisions. COARSE_ONLY is cheaper on difficult corpora precisely because it leaves answers unresolved; do not compare its bytes as equal-quality delivery. Across all four deliberately selected mixes SELECTIVE64 totals3476 bytes vs ALWAYS64 3200:8.625% more, not an overall observed saving. Repeated numerical values across corpora are intentional controlled inputs; IDs/process counts are not independent population samples.

## H / T / D / C / U

H: the exact retained #4045 rounding enclosure supports sound definite decisions; immutable-source refinement resolves only ambiguous inputs. Its extra round trip costs enough to reverse the byte advantage for boundary-dense workloads.

T: four fixed16-observation binary64 corpora, three modes per source, then four SELECTIVE64 controls:196 fresh receiver processes, one driver invocation, zero reruns/replacements/tuning. Actual stdin/stdout pipes carried coarse/fine/query/final messages. All original input hex, complete wire bytes, PID/argv/time/exit/stderr records, source hashes and actual outer exit are retained. No model, training, GUI, task input, installation or experimental network. Sources/corpus/plan/auditor were published before formal execution, not retrospectively.

D: full196/196 rows and actual zero exits, exact decisions/source bytes/byte accounting, all four fault controls UNKNOWN, independent audit errors=[] with2864 checks, all10 effective evidence corruptions rejected. The scoped decision requires correctness AND the declared sparse-saving/dense-regression accounting, not universally fewer bytes. The formal END has stop=null. Eight excluded construction unit methods passed.

C: the trusted producer retains the ORIGINAL binary64 value. Matching ID and re-encoding consistency detect the tested faults, but cannot authenticate a producer or distinguish a dishonest same-ID substitution within the same rounding cell. Fine precision is not a new observation. The protocol is a newly declared fixture, not the production Agent Interface transport.

U: real boundary frequency, source storage/eviction, packet headers, scheduling/round-trip latency, task/model usefulness, clock freshness, sensor error and arbitrary producer behavior are outside scope. Byte counts are not tokens, latency, memory or monetary savings. There is no sampling reliability claim or calibrated physical uncertainty. Separate same-author implementation/process auditing is not independent human review.

## Conditional proof and accounting

PROOF.md gives the full proof and Japanese variable/unit table. Nearest rounding encloses the original in the Cartesian product of midpoint cells. Whole-box containment in the allowed region proves VALID; empty intersection proves INVALID. Otherwise, obtaining the immutable original and exact rational comparisons resolves membership. The truthfulness/immutability premise is essential.

The wire uses explicit big-endian standard widths and no native padding:9-byte type/ID header,25-byte coarse packet,41-byte fine packet; refinement query and terminal V/I/U each9 bytes. Non-refined SELECTIVE64 costs34 bytes; refined costs84; ALWAYS64 costs50. Therefore the exact refinement-fraction crossover is32%, for THIS protocol only. Both directions and terminal statuses are included. Original source capture and process startup are outside the byte boundary. No efficiency default is selected.

## Provenance and environment

Intake main4c701cc51b06296268ad8d9ae3eff1dd6f2d379d. Issue4400 and dedicated branch research/precision-refinement-4045-20260926-q4f8 precede formal execution. Complete source/corpus archive committed at5cf9fc3c865ea116c9835a1f6f505209a5de5820; all9 publication file IDs/sizes were read back before authorization comment5841200195. First-outcome comment5841205928 precedes result packaging.

Freeze SHA256:946a42c2e2fc4bff211602b131d5b3be98aca77bab35f9dae75b414f6b52919b.
Source archive SHA256:a81db9b45df83a7446fa044b99d062713dc17d6c527967e1347cfa39d611560c.
Exact vendor Git blob:3b03f12c34dd64250deebb9cde78ea48a50a7b5e; old #4045 evidence unchanged.

Provided Linux6.18.44 x86_64 container, CPython3.13.5, guest Intel Xeon Platinum8573C, stdlib only. Binary32/64, exact rational comparison, explicit byte order. Docker/gh CLI unavailable; no Docker/OrbStack image attestation. Frequency/load/core isolation uncontrolled; no performance benchmark is reported. ENVIRONMENT.json retains executable/module identities. All features are dimensionless, including normalized age.

Actual formal driver and196 receivers exited0; launcher shell and audit exit0; actual study stdout/stderr are empty. A TERM-environment diagnostic printed by the outer container tool is separate from saved study stderr and has not been silently attributed to the study. No formal timeout or science correction occurred.

The prior source-age r3h6 incomplete experiment remains STOP_OUTER_TOOL_TIMEOUT/HOLD_FORMAL_INCOMPLETE and was recorded retrospectively in #4255 comment5841118147. Its complete conversation ZIP is NOT included here. No prior live/training/scientific run was repeated. Current work neither owns nor changes parallel #4387/#4374/#4255/#2542.

## Revalidate without a scientific rerun

From this published directory, choose two NEW destinations:

```sh
python -S -B unpack.py SOURCES.json /tmp/q4f8-source-review
python -S -B unpack.py RESULTS.json /tmp/q4f8-result-review
python -S -B /tmp/q4f8-source-review/audit.py /tmp/q4f8-result-review/formal --controls > /tmp/q4f8-reaudit.json
cmp /tmp/q4f8-result-review/AUDIT.json /tmp/q4f8-reaudit.json
python -S -B -m unittest -v test_unpack
```

Do not run consumed launch.py/run.py. The source archive preserves16 files; result archive preserves10 files, including RAW.jsonl/END.json/PROCESS.json, first audit, launch output/exits and public readback record. Restoration verifies exact original bytes, not regenerated experimental observations. Publication helpers/tests are postmeasurement engineering, distinct from the scientific freeze. Filesystem parents are trusted/quiescent; the restorer is not an adversarial filesystem sandbox.

## Integration boundary

Only additive research/system1/precision_refinement_q4f8_v1/. No shared runtime/workflow/root index/old-result edits. Current-head CI, review and main reachability are separate delivery gates; publication does not itself establish them. Global ROADMAP and parent #3442 remain open. A next adoption decision requires actual source-retention semantics and measured boundary frequency; no new allocation is authorized by this report.

### ERROR CHECK

Complete denominator and actual exits retained; no quality-losing coarse arm called equal-quality compression. Both directions and common final status counted. Dense regression and pooled cost increase reported. Closed preimage is conservative at ties. IEEE decoding in the independent auditor uses integer/rational arithmetic, not the receiver's struct/cell implementation.
