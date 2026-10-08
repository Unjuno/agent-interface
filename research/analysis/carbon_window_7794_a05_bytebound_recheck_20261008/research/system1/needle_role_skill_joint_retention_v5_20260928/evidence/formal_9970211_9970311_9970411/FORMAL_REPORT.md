# v5 formal role-skill online-LoRA result

## H / T

This is the preregistered three-seed synthetic explicit-role test for whether an immutable role-A skill plus online rank-2 role-B LoRA improves A retention by at least 0.10 over **each** shared comparator while keeping B accuracy at least 0.90. Allocation `needle-role-skill-joint-retention-20260928-v5`; formal seeds 9970211, 9970311, 9970411; one trainer invocation, no retry or seed substitution; pinned image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (`linux/amd64`), CPU only, offline, read-only source/root.

## D — evidence and decision

- Stage 0 passed 13/13 tests.
- One trainer invocation exited 0 and produced 1,613,764 raw bytes. Raw SHA-256: `6c8f183f1f23dc3635a1cdebe4ee5b6eaadd83852dc655d2999d62dfa24f4667`.
- Independent audit recomputed all 3 seeds and 192 arm-arrival rows. The preregistered auditor reports `HOLD_AUDIT_INTEGRITY` because the recorded actual Docker argv used the equivalent two-argument network spelling `--network none`, while the frozen argv gate requires the single token `--network=none`. This representation mismatch is retained; no claim of an audit-integrity PASS.
- The same audit reports one preregistered scientific failure: seed 9970411 misses the minimum +0.10 A-retention gain over every shared comparator. Separate-skills A=1.000 and B=1.000, but shared-A-replay A=0.99609375, hence the gain is only 0.00390625. Formal allocation result: `FAIL_ROUTING_OR_RETENTION` is not certified because audit integrity is HOLD; the observed scientific gate miss is nevertheless explicit and the outcome cannot satisfy the preregistered pass criteria.

| Seed | Shared B-only A/B | Shared A-replay A/B | Routed shared A/B | Routed separate skills A/B |
|---|---:|---:|---:|---:|
| 9970211 | 0 / 1 | 0.5078125 / 0.5546875 | 0 / 1 | 1 / 1 |
| 9970311 | 0 / 1 | 0.5 / 0.5 | 0 / 1 | 1 / 1 |
| 9970411 | 0 / 1 | 0.99609375 / 0.00390625 | 0 / 1 | 1 / 1 |

Max observed update time remained below 2.1 ms, far under the 60 ms gate. The second preflight-only Docker call initially supplied `python` despite the image's Python ENTRYPOINT and stopped before training; its correction, the strict freeze sidecar readback correction, and the exact argv discrepancy are recorded on Issue #4949. There was exactly one formal training invocation and no retry.

## C / U — scope

Synthetic data with an explicit role bit only. This does not test natural-language role inference, live Needle behavior, real-time deployment, task transfer, GPU value, or product readiness. The descriptive signal suggests separate adapters can prevent the particular forgetting seen under B-only shared updates, while the replay comparator can sometimes retain A almost as well; it is not evidence that the separate-skill route clears the preregistered improvement bar.

Raw payload is gzip-compressed (443,302 bytes) and base64-split into 30 numbered parts in this directory. Concatenate parts in numeric order, base64-decode, then gunzip; verify reconstructed raw SHA-256 above. Compressed SHA-256: `1b54ba22f0cf926532a16a599ba50f25a918d3ef578428fe35fcc84de780772e`.
