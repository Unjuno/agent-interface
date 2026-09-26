# Formal report — Issue #4462

## Decision

`HOLD_PROTOCOL_DIVERGENCE`. The run and its raw data are retained, and the auditor reproduced the run as generated, but its training-band boundary did not match the public Issue contract. Therefore the Issue's preregistered experiment has not passed and the scores below are descriptive evidence for the executed variant only.

## Frozen allocation

- Seeds 3480, 3481, 3482; balanced control versus treatment; six 700-step trainings.
- Treatment retained 1,024 balanced CORRECT rows and added 512 band-A plus 512 band-B near-boundary rows. Initialization and minibatch streams were paired.
- Public Issue #4462 specified band A `|dx| in [.071,.110]` and band B `|dx| in [.111,.149]`. The frozen runner instead generated band B from `.110 + .039*U`, i.e. `[.110,.149)`. It admitted values in `[.110,.111)` that Issue #4462 excluded. This is a source-to-preregistration mismatch; the formal audit checked reconstruction against the runner but did not compare runner semantics with the GitHub Issue contract.
- Local `needle-pilot05:local`, image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`; CPU-only, no network, read-only source/root, dedicated output, 2 CPUs, 4 GiB, 64 pids, 64 MiB tmpfs.
- Construction tests: 11/11. Formal invocation: exactly one; no retries or tuning.

## Treatment results

| Seed | Shift accepted accuracy | Shift CORRECT recall | Paired recall lift | IID accuracy | p95 latency (ms) | Seed gate |
|---:|---:|---:|---:|---:|---:|:---:|
| 3480 | 0.9989 | 1.0000 | 0.8012 | 0.9962 | 0.0341 | PASS |
| 3481 | 0.9992 | 1.0000 | 0.6521 | 0.9988 | 0.0455 | PASS |
| 3482 | 0.9992 | 1.0000 | 0.6416 | 0.9996 | 0.0429 | PASS |

Under the executed variant, shifted CORRECT recall standard deviation was 0.0 and mean paired lift was 0.6983. These are descriptive, exploratory figures only. Although ancillary and model gates passed under the frozen runner, the Issue-level acceptance decision is HOLD because the declared intervention was not implemented exactly. Do not treat the original PASS label emitted by the within-run audit as qualification of Issue #4462.

## Integrity and limits

Independent audit: `PASS`, zero errors for the executed source contract. It reconstructed training rows, paired setup, evaluations, controls and the runner's decision. It did not identify the mismatch against the public Issue text; this limitation is why the allocation-level conclusion is HOLD.

- `FORMAL_RESULT.json` SHA-256: `4906487079fc2e4166752ea9f3ed5651d5a73e20cf9e13fc1c7f29db550e4bcc`
- `AUDIT.json` SHA-256: `a73db7288be30e12a157104a23617c8bf31c371ec444f53c4cee480e5c16f0d6`

The unchanged formal bytes are retained to document this protocol divergence. A corrected successor must use band B `[.111,.149]`, independent per-band bounds in its auditor, fresh seeds, a new allocation and one new preregistered run. The original Issue and these outputs must not be silently rewritten as a pass. This synthetic work does not establish real-task utility, broad generalization, production safety or execution authority.
