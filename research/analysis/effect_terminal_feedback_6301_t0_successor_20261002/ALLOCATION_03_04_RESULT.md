# Issue #6350 — finite effect/terminal renderer result

## Disposition

`PASS_METHOD_SCOPED` for the frozen finite synthetic contract, combining one candidate invocation in allocation 03 with one independent raw-only audit in audit-only allocation 04. Allocation 03 itself remains `STOP_METHOD_FAILURE` because its auditor runner omitted the writable report mount; that failure is preserved unchanged. Allocation 04 audited allocation 03's exact candidate output without rerunning the candidate. Issue #6350 remains open; this does not close wider integration, live GUI, model, or task-effect research.

## H / T / D / C / U

**H.** A corrected finite renderer distinguishes current-generation `VERIFIED`, `NOT_APPLIED_VERIFIED`, `UNKNOWN`, and stale-generation-as-`UNKNOWN`; keeps task-terminal status as a separate conjunction; reconstructs the predecessor fixture exactly; and rejects four semantic corruptions.

**T.** Frozen source main `9a573b00dc595e64d09387e567c85e10b61a46c1`, candidate package commit `43e921435e6272816fd2615dbaabee0685f26511`, fixture origin `eba652642a7a741d57bbdfe0c1a9929d3b15bd7f`. Fixture/candidate/auditor/test SHA-256 values: `35bfa13d5edee93d834ddc54c980bb24a48b8a5bb9a4e9bcc9dcddd11d1b51a9`, `b41036c61ebece89a2f1b990e7ae2f9b896512fc2983b29a9b4dd9e712c9cc88`, `831ad1e7a499b1d28bd5b0b9fbfb10b9f5409eddc47460e4a28209d84055977e`, and `5e206a9109b4c4442c3ba52facd14559c8241b339c8fbf648575da4377a7542a`.

Runtime: dedicated OrbStack Ubuntu 24.04 ARM64 VM with its own Docker Engine 29.1.3. Python image was exported from the pre-existing local cache and loaded without pull; immutable image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; interpreter Python 3.12.14. Construction, candidate, and audit each used separate containers; each was network-none, read-only rootfs, all capabilities dropped, no-new-privileges, UID/GID 65534, requested 0.25 CPU / 512 MiB / 64 PIDs. Construction container reported `cpu.max=25000 100000`, `memory.max=536870912`, `pids.max=64`; Docker `HostConfig` records the requested values on all formal containers. VM provisioning requested 1 CPU/2 GiB, while its daemon reported 10 CPUs/16,819,609,600 bytes; no VM-level limit is claimed. No GPU/model/GUI/game/user input or external task effect.

| Stage | Allocation | Invocations | Outcome |
|---|---|---:|---|
| Host construction | 03 prep | 8 tests | 8/8 pass |
| OrbStack construction | 03 | 1 container | 8/8 pass; exit 0 |
| Candidate | 03 | 1 container | 9 traces emitted; exit 0 |
| Independent auditor | 03 | 1 container | Exit 1 before report: missing `/out` mount; `STOP_METHOD_FAILURE` |
| Raw-only auditor successor | 04 | candidate 0, auditor 1 | `PASS_METHOD_SCOPED`; 10 tasks, 30 display records, 4/4 mutations rejected |

No formal invocation was retried. Allocation 03's candidate raw, failed auditor log, inspect record and STOP remain unchanged. Allocation 04 consumed only that raw candidate as read-only input.

**D.** The A04 auditor accepts all 10 task rows and 30 display records, reports no errors, and rejects `drop_pending_obligation`, `forge_terminal`, `promote_stale_effect`, and `accepted_input_as_effect`. `NOT_APPLIED_VERIFIED` remains distinct from `UNKNOWN`; terminal remains `PENDING` where release is unresolved. A stale generation maps to `UNKNOWN`; accepted input alone is not effect evidence.

**C.** One deterministic finite truth table and one retained candidate output. Synthetic states, obligations, and displays are not sampled from live user behavior. A03's missing output mount is infrastructure/method evidence, not scientific failure.

**U.** No model response, live GUI/application effect, user-visible benefit, safety rate, efficiency, latency, MAP01 outcome, broad workload transfer, or product claim.

## Immutable run evidence

- Allocation 03 freeze/protocol: [`ORBSTACK_FREEZE_03.json`](ORBSTACK_FREEZE_03.json), [`ORBSTACK_ALLOCATION_03.md`](ORBSTACK_ALLOCATION_03.md).
- Allocation 03 outputs/logs: [`formal_03/`](formal_03/); candidate JSON SHA-256 `c6024886ab276f24a033c18c5446651eae3adb30bb58ed3c999c1b77595085e1`; failed A03 auditor stdout SHA-256 `d5ebe8dc2a342894a71f9229181dae23af4e40d4e84b7f1952a9292629e688f2`.
- Allocation 04 audit-only freeze/protocol: [`ORBSTACK_AUDIT_FREEZE_04.json`](ORBSTACK_AUDIT_FREEZE_04.json), [`ORBSTACK_AUDIT_04.md`](ORBSTACK_AUDIT_04.md).
- Independent A04 receipt: [`formal_04/audit_out/audit_result.json`](formal_04/audit_out/audit_result.json), SHA-256 `ee09c931c2fef946a5451cadcd87f0a65806412b3aae48bec31629ffb079e202`.
- A04 stdout SHA-256 `84afc5a881d7f859144dc8f42970685179e16eb74d073d53e4973e37638bd416`; container inspect SHA-256 `62b394c2fe17d354a2a8a309518baf93efa990b17dbfb758e68a07b5445da455`.

The original #6301 predecessor STOP, allocation 02's unconsumed requested WSLc window, both pre-start main-advance stops, the T03 auditor mount failure, and the A04 pre-start directory setup issue are retained and not rewritten as scientific results.
