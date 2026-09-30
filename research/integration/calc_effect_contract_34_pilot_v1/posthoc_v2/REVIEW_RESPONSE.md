# PR #4633 review follow-up

Review identified that the original v1 auditor only rejected the exact empty list and could let a missing, null, or wrong-typed visibility field fall through. The v1 code and its executed audit bytes are preserved unchanged. This additive post-hoc verifier requires a non-empty list of hexadecimal X window IDs.

In the pinned container, six unit tests passed: missing, null, empty, wrong type, malformed ID all reject; a non-empty hex ID passes the type/shape check. Re-auditing the retained #4626 raw row and workbook with this verifier emits `STOP_CONSTRUCTION`, `visibility_evidence_valid=false`, because the preserved raw value is `[]`. It does not alter the original raw or audit and is not a new construction run.

The publication-checkout note in `PLAN.md` now warns that tracked `results/` is occupied and must never be mounted as writable `/out`. For any separately authorized new allocation use a fresh empty disposable output directory; this correction does not authorize rerunning #4626.

Audit output SHA-256: `5dd39c7c5267fc419bf1c5d13a34f7df87f97c43e4d4275c565ae1a796bd0cd6`. Unit tests: 6/6 pass. Hardened verifier SHA-256: `4a02e3983c394d2d370bfb22145b1cd363d78072f03673593db09a9badb4674a`; tests SHA-256: `0c5cf04aad3314661b7544c1c5df660ae7283b77fd2c32038a4df79a4a106942`.
