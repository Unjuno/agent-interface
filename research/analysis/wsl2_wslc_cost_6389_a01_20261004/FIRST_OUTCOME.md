# A01 first outcome — STOP_PINNED_IMAGE_UNAVAILABLE

Allocation `6389-wsl2-vs-wslc-belief-replay-a01-20261004` is terminal. It is
not retried or repaired in place.

## Exact outcome

- Current-main and frozen source/protocol hash gates passed at main
  `13bab54ea6d91978247ecc1b70e5060db752367a`, branch commit
  `79733b0a4ef4871c51a3aec39159a3eb37427b85`.
- Pair 1 order began native WSL2, then WSLc. Native candidate exit 0 and
  independent audit exit 0; external candidate-plus-audit elapsed time was
  `1.0036581000022124 s`. The raw-only audit reported `PASS_METHOD_SCOPED`,
  9/9 rows, zero errors, zero unsafe admissions, and 4/4 mutation controls
  detected.
- Native outputs: `formal_raw.jsonl`
  `6030a0b9e2e1607a824cc1815e4e92a4c4047715aeaa4fcbe11cb0de3a15d532`;
  `sticky_baseline.jsonl`
  `1307417697b3e20e7b49be1872f08fe75943feaf00253a796b5d1805ae8eba07`;
  `age_baseline.jsonl`
  `5f39a2e4a914c8e6a65f177fbc20f857285d0bbfbae0c730820223548ee75716`;
  auditor `86fd66f63b012b7eed8387d0ef7f4e8c5406215a612d45d9817b74f875c43be6`.
- The WSLc pre-invocation cache gate returned STOP before a WSLc candidate or
  auditor invocation. Its check searched for the concatenated token
  `python@sha256:<digest>` in a human-readable `wslc images --digests` table,
  which actually prints the repository/tag and `sha256:<digest>` in separate
  columns. The same read-only table showed the pinned digest and local image ID
  were cached. Therefore this is a measurement-harness false STOP, not image
  unavailability or a scientific/runtime failure.
- Candidate invocations: native 1, WSLc 0. Auditor invocations: native 1,
  WSLc 0. Retries: 0. No WSLc container was started; no Docker/Podman, network,
  model, GUI, input, or GPU was used. All older containers and images remain
  untouched.

The native output hashes happen to match the historical #5368 portability
outputs, but those historical files came from a different frozen source hash.
They are not treated as a paired comparison, pooled, or used to infer parity.
No iteration-cost or memory conclusion is supported by this incomplete pair.

## Routing

A successor may correct the image-presence predicate only in a new allocation
and additive path. It must rerun a complete fresh paired sequence; these A01
native timings and outputs are custody evidence only and will not be pooled.
