# Formal report — Issue #4462

## Decision

`PASS_STRATIFIED_CORRECT_AUGMENTATION_SCOPED`. The preregistered stratified treatment passed all three fresh paired seeds. This is a synthetic, authority-neutral proposal classifier result; it does not promote a production model or grant execution authority.

## Frozen allocation

- Seeds 3480, 3481, 3482; balanced control versus treatment; six 700-step trainings.
- Treatment retained 1,024 balanced CORRECT rows and added 512 band-A plus 512 band-B near-boundary rows. Initialization and minibatch streams were paired.
- Local `needle-pilot05:local`, image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`; CPU-only, no network, read-only source/root, dedicated output, 2 CPUs, 4 GiB, 64 pids, 64 MiB tmpfs.
- Construction tests: 11/11. Formal invocation: exactly one; no retries or tuning.

## Treatment results

| Seed | Shift accepted accuracy | Shift CORRECT recall | Paired recall lift | IID accuracy | p95 latency (ms) | Seed gate |
|---:|---:|---:|---:|---:|---:|:---:|
| 3480 | 0.9989 | 1.0000 | 0.8012 | 0.9962 | 0.0341 | PASS |
| 3481 | 0.9992 | 1.0000 | 0.6521 | 0.9988 | 0.0455 | PASS |
| 3482 | 0.9992 | 1.0000 | 0.6416 | 0.9996 | 0.0429 | PASS |

Shifted CORRECT recall standard deviation was 0.0. The mean paired lift was 0.6983; IID accuracy stayed above 0.95 with no paired drop over 0.02. Boundary and all five invalid controls yielded, false-CORRECT and latency gates passed, and the independent audit recomputed the same PASS decision.

## Integrity and limits

Independent audit: `PASS`, zero errors. It reconstructed training-row/band and minibatch digests, paired setup, evaluations, controls and decision. Integrity is reported separately from the scientific scope.

- `FORMAL_RESULT.json` SHA-256: `4906487079fc2e4166752ea9f3ed5651d5a73e20cf9e13fc1c7f29db550e4bcc`
- `AUDIT.json` SHA-256: `a73db7288be30e12a157104a23617c8bf31c371ec444f53c4cee480e5c16f0d6`

This validates only the declared synthetic shift and three seeds. It does not establish real-task utility, cross-distribution generalization, production safety, or execution authority. Any integration must be a separate review and implementation decision.
