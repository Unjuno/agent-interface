# #1882 DATA-restricted safety cut-set analysis — formal result

Task: `SAFETY-PLANE-DATA-CUTSET-R0-20260919-001`
Decision: **`PASS_SAFETY_PLANE_DATA_CUTSET_THEOREM_SCOPED`**

## Formal outcome

The one frozen formal invocation enumerated all 32,768 directed acyclic dependency graphs over `s,d0,d1,a0,a1,r` with declared DATA set `{d0,d1}`.

- complete unique coverage: 32,768 / 32,768;
- arbitrary-failure theorem/oracle mismatches: 0;
- bounded-failure mismatches: k=0: 0, k=1: 0, k=2: 0;
- base-reachable graphs: 28,999;
- arbitrary-DATA-failure guarantee: 24,064;
- up-to-one-DATA-failure guarantee: 25,046;
- minimum DATA-only cut sizes: 0 => 3,769, 1 => 3,953, 2 => 982, no DATA-only cut => 24,064.

Directed controls matched preregistration:
- `COUPLED_SINGLE_DATA`: min DATA cut 1; arbitrary guarantee false;
- `DIRECT_SAFETY_PATH`: no DATA-only cut; arbitrary guarantee true;
- `TWO_DATA_ROUTES`: min DATA cut 2; k=1 true but k=2/arbitrary false.

Independent `audit.py` recomputed all 32,768 rows without importing `prove.py` and returned PASS. Four retained-evidence mutations were rejected 4/4.

## Interpretation

For the declared graph semantics, surviving arbitrary failures of DATA vertices is equivalent to retaining an `s→r` path with no DATA vertex. Surviving every DATA failure set of size at most k is equivalent to every DATA-restricted `s→r` cut having size greater than k.

Therefore, “no single shared DATA bottleneck” is insufficient for arbitrary-failure independence: two alternate DATA-routed paths can survive either single failure while still failing when both DATA vertices fail.

This is a dependency-design discriminator for #17. It is not a hard-timing, backend-availability, physical-device, or production-safety claim.

## Integrity

Frozen source SHA-256 remained exact after formal:
- `prove.py`: `8baabdbdc44dafd016f1d95ef9a872d23f6510ec8ea9993dd3252d05b0f1cc0d`;
- `audit.py`: `06fade7d6f4a63262028d31ee29d67675dfafe8af6b7e6a72fa51ab3b518fd94`.

Result SHA-256: `ce88f2e05a503ee64c98fe7effbe383116f60b652c2e4b896b3d775041bbe839`.
Audit SHA-256: `314c2dd9a7f81f1abc23e5d8e4f1f450bf452c7765a83dbd0c952cc22e0d2838`.
Raw-row artifact SHA-256: `9f78d85c83c8b5611ccd2e09abf16a9d5ba344dce3c40d1a2244ae1c27ffec7e`.

Formal invocations 1; reruns 0; replacements 0; tuning 0.

## Limits / successor

Hidden synchronous dependencies, scheduling, kernel/backend stalls, missing fault domains and deadlines remain outside this result. The next useful rung is a retained-evidence adapter that maps one real safety path into this typed dependency graph and audits edge completeness before any new live experiment.
