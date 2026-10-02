# Issue #5442 T8 — target-binding successor result

## Disposition

`PASS_TARGET_BINDING_SCOPED`. The pre-registered OrbStack candidate and separate raw-only auditor each ran once and exited 0; retries: 0. The independent auditor returned zero errors and rejected all six frozen corruption controls, including an actual mutation of `receipt.intent.target_id`. This closes only the missing T7 target-mutation method gate for this finite simulator. Issue #5442 remains open.

## H / T / D / C / U

- **H:** A successful dispatch that changes the wrong object while leaving the intended object unchanged must remain `UNKNOWN` and deny irreversible-commit admission; an intermediate-only policy still reports success. A receipt binds intent target, dispatch target, endpoint target/state and pre/post versions.
- **T:** Allocation `SEMANTIC-RECEIPT-5442-T8-ORBSTACK-20261002-01`; preregistered on Issue #5442 before formal launch, frozen against main `49144844b482026c33fcfbde7e2fd5f7bdc7762c`. Candidate and auditor ran in distinct OrbStack containers, each with the digest-pinned Python image, `linux/arm64`, network disabled, read-only root/source, non-root uid/gid 65534:65534, and requested limits of 1 CPU, 256 MiB, and 32 PIDs. The raw candidate output was mounted read-only into the auditor. Exact inspections and first outputs are retained in `formal_01/`.
- **D:** Candidate result matched all four preregistered rows. The auditor returned `PASS_TARGET_BINDING_SCOPED`, checked four rows, `errors=[]`, and rejected 6/6 mutations: actual nested intent target, endpoint target, semantic decision, missing row, duplicate row, and source intent target. Candidate raw SHA-256: `14822a774c5bdd42d6daf880072eb83208d058c93240ec9e8de5304ffecbce37`; audit JSON SHA-256: `68f2ab03bdcf81f0f69509e3db1d4411749d0de259f73870fe8dc2794611f656`.
- **C:** Deterministic authored object states and a fixture observer stipulated authoritative/fresh. The six host construction tests passed before freeze. Container inspection reports the requested configuration and `OOMKilled=false`; actual memory/cgroup enforcement was not measured or inferred.
- **U:** No real application observer, GUI/task effect, runtime authority, broad safety rate, latency/cost, or product benefit is established. For the wrong-target case, raw records dispatch to `doc:B` and the fresh endpoint observation of intended `doc:A`; the simulated mutation of B is reconstructed from the frozen scenario and simulator, not independently sensed from a real application. Keep this boundary explicit. This is not a runtime implementation or Issue #5442 closure.

## Observed decision table

| Fixture | Dispatch target | Observed intended target | Intermediate-only | Receipt result | Irreversible commit |
|---|---|---|---|---|---|
| `valid_effect` | `doc:A` | `doc:A`, version advanced, goal state | `SUCCESS` | `SEMANTICALLY_CONFIRMED` | admitted |
| `wrong_target` | `doc:B` | `doc:A`, unchanged pre-state | `SUCCESS` | `UNKNOWN` | denied |
| `stale_pre_state` | `doc:A` | `doc:A`, goal state but wrong pre-version | `SUCCESS` | `UNKNOWN` | denied |
| `noop` | `doc:A` | `doc:A`, unchanged pre-state | `SUCCESS` | `UNKNOWN` | denied |

## Execution accounting

- Candidate formal invocation: 1, exit 0, container `2c38675a9421dc5ced82908f2346e6fde0c437df41fbc255564e0a4cee515cbd`; stderr empty.
- Independent auditor invocation: 1, exit 0, container `65284ef22bd5db7ac03a53797f3848270d3c7651ec489bb4569edc23c583eb7d`; stderr empty.
- Retries: 0. No model, GUI, GPU, network service, package install, or post-freeze source mutation.
- Python reported `3.12.14`; OrbStack Docker client/server were `29.5.2` / `29.4.0`, engine `linux/arm64`.
- The host construction suite initially had one setup-only failure while `FREEZE.json` still contained `PENDING` hashes. Hashes were filled before preregistration/formal execution; the final frozen suite passed 6/6. No formal invocation occurred during that setup failure.
- A separate pre-existing container `unjuno-native-ci-6092` remained running and untouched; its sampled Docker stats were 0.00% CPU and 112 KiB / 15.66 GiB.

## Reproduction

See `FREEZE.json`, `PREREG.md`, `RUN_LOG.md`, `formal_01/`, and `SHA256SUMS`. The runner uses `docker create --pull=never` with the exact package mounted read-only, then `docker start --attach`; the auditor has an additional read-only bind mount for `formal_01/candidate.raw.json`. Do not rerun this consumed allocation. A future real-observer/application experiment requires its own scope, authority, and preregistration.
