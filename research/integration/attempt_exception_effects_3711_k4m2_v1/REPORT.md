# #3711 k4m2 — current-module exception / partial-effect boundary

## Result

PASS_CURRENT_MODULE_EXCEPTION_EFFECT_BOUNDARY for one source-first ten-case allocation. This is a finite current-module composition result, not a new exception algorithm, native GUI test, production repair or general reliability claim.

| Case | Actual file effect | Worker returncode | Retained recovery |
|---|---|---:|---|
| RuntimeError before first append | empty | 0 | report_recorded; runtime_failed, unknown effect |
| RuntimeError after first append | A | 0 | report_recorded; runtime_failed, unknown effect |
| KeyboardInterrupt before first append | empty | -2 | unknown_or_incomplete; no report |
| KeyboardInterrupt after first append | A | -2 | unknown_or_incomplete; no report |
| SystemExit before first append | empty | 23 | unknown_or_incomplete; no report |
| SystemExit after first append | A | 23 | unknown_or_incomplete; no report |
| os._exit before first append | empty | 23 | unknown_or_incomplete; no report |
| os._exit after first append | A | 23 | unknown_or_incomplete; no report |
| Complete | AB | 0 | report_recorded; returned, task_success null |
| Preexisting run directory | empty | 0 | unknown_or_incomplete; callback not invoked |

The ordinary-error worker returns 0 because the experimental harness receives the real module's failure report normally. This is NOT the public CLI's error-to-exit-code mapping and is not a claim of task success. The callbacks perform real writes only to experiment-private files; their task semantics are synthetic.

Six interrupted/exited cases share request-only recovery: three have no effect and three retain A. The weaker proposition 'missing report means no effect' has counterexamples. Ordinary error reporting also preserves unknown effect with either empty or partial content. All twenty separate real inspect_attempt calls preserve replay_allowed=false/process_state=unknown and all original file bytes. No retry or rollback is authorized by this finding.

## Execution and provenance

Intake main 874d9760683ae0974946786eafe17397edc97c3a; exact subject Git blob bd1725a18b6aef6f45c62297cbd794c760ea0a9f, SHA256 637dd42eb7a06036165c7b60c59d4f150301c877f46146c2dd0dee07744db9f1, 4797 bytes. This is the complete unchanged attempt.py, imported by file location. It is not a simplified reproduction and not the full package/import/backend path.

Public source commit c8921ba8612998a999e7544c8f4b85d99d33ebc8 and Issue comment6016893819 precede the allocation. Source archive19784 bytes/SHA25684b52713652b20ea6e1ba3fe2ff20627d2622e8ecb348dcd6045f5beb10fd268 contains107 members; original FREEZE SHA25639ab6d2837419af77ed04ba7fcc0a58b74e90f1c04ff16cf52aa5e219cab527a binds106 files. Five uploaded binary blobs and all eight publication-file identities/sizes match a separately computed and read-back Git subtree065634cc8417563c31f373d9a7b62ead05371a37. Current subject identity was rechecked immediately before execution.

Actual command and process receipt are in formal_execution.json. Collector invoked once, outer exit0/no timeout. Ten worker processes plus20 read-only inspector processes were waited/reaped; all recorded absent afterward. Nine callbacks entered once each; Conflict entered zero. Final effect bytes are five empty, four A, one AB. Formal reruns/replacements/exclusions/source changes0. No expected exception exit is silently converted into an observed normal completion.

## Audit and construction failures

Separate raw-only auditor imports neither subject nor worker/collector:342 checks, errors[]. Eight well-formed byte-effective copied-evidence corruptions rejected, including boolean exit, source substitution, omitted partial effect, duplicate callback, false replay/process authority, premature read and false known-no-effect claim. Complete mutated input records are retained. The effect oracle and independent file snapshots reconcile the actual bytes and journal order; source hashes are checked separately. Same-author separate implementation/process is not external human review or execution attestation.

Four XY construction cases are excluded. Five initial unit assertions failed against the deliberately incomplete audit stub, then five passed after implementation. Construction audit140/errors0. First mutation-control result incorrectly called a False-for-0 mutation unchanged using Python equality, even though the auditor rejected it. Original source/output are retained; serialized-byte comparison fixed the control before freeze. The same saved construction rows then gave8/8 effective controls. No construction callback was replayed for that correction.

## Limits and integration decision

Provided private Linux x86_64/CPython3.13.5 container. Children request one permitted CPU,256MiB address-space and3CPU-second limits,8s communication timeout. No hardware-frequency control or benchmark is claimed. No WSLc/Docker/OrbStack image attestation, native GUI/input, model/provider, shared game host/GPU, user files or experiment network. Explicit exception raising is not externally timed OS cancellation; os._exit is one point, not power loss. File fsync plus subsequent read is not a distributed transaction or physical durability guarantee.

Do not change Exception into BaseException catching merely to create a report: this experiment evaluates existing semantics and proposes no catch-policy repair. Recovery must distinguish report availability, callback result and independently observed current effect. Partial effects remain real even when the final report is absent. No compensation/idempotency/automatic replay mechanism is implemented. Broader #3711/#57/#59/global ROADMAP remain open.

PR #8239's previously claimed 8-case A01 raw/source are unavailable for revalidation here. Its historical uploaded text already contains an assistant-supplied ellipsis placeholder, not evidence of connector truncation. Qualification comment6016481923 preserves that distinction. This ten-case allocation neither fills its missing bytes nor corroborates its claimed audit.

See PLAN.md for original H/T/D/C/U, variable/unit table, prerequisites and roadmap. Scientific result, complete evidence publication, checks/review and main adoption remain separate gates.
