# Issue #3688 execution evidence

## Frozen byte identities

- Preregistration commit: `68abd9f7f`, based on current main `b04e93dd2e1fb610ed8761a9a91590fe69a7683b`.
- Allocation freeze: `6da69a03edb1f4dc8edb4b87c01e8c2d78444084ddd0fa6ebe7da33b380ab3c0`.
- Exact predecessor raw: `ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807`.
- Exact predecessor freeze: `f40494b1be99fb1e68d7b09c498297df35a72c043740b5f09d3faec7e059acfe`.
- Exact predecessor study freeze: `c038b0b2f5a1c1498613b2b8986d84f70dfc49dfc4e52b051bebe0de5e1deff8`.
- Upstream `audit.py`: `c771624bc93ef66f516ccb35c510c5a46ba33a1ec5aef510dcebd98d28a41edd`.
- Upstream `test_audit.py`: `0066dae870b60d030c062b8ac01e26b58cfcc5c91f998a95f51e08d225b14ce1`.
- Candidate `raw_byte_audit.py`: `3dac162ff352991610da57983f24b28e73bf7115e9d05a162f6f4cf76518f147`.
- Candidate `test_raw_byte_binding.py`: `cf3cbf4be7aa03efcafc4f7074a8de2bc1a8bb0509d43207f1807643ab720ce0`.
- Formal JSON result: `257b1d572ddc3f9cd7b4fede655926c38ce5a5aa73a48e0fffdca381f69bc718`.
- Independent audit JSON: `abd3b83b96e7f4c92aff106c808e36ca8d2ea2a3f2d50f6e62fec978f1df2f51`.

## Formal matrix

One invocation of the frozen matrix ran in OrbStack Docker Engine 29.4.0, Linux/arm64. Base image was `sha256:b138c00ce990cf972f8be1ae4b3f7a11a198ad46e8804b41dabd979052aad8e8`; derived image was `sha256:8c37d3a0ff21d1205a00c567fd184184816ab00d81292cb0feee7be92d572f64`. Runtime network was disabled; rootfs and input mount were read-only; outputs used a unique writable directory. All containers used `--rm`.

| Case | Direct/CLI disposition | Reject stage |
|---|---|---|
| exact original | `PASS_RAW_BYTE_BOUND_STRUCTURAL_AUDIT` | structural audit |
| whitespace appended | `FAIL_PROVENANCE` | raw + predecessor binding |
| altered event | `FAIL_PROVENANCE` | raw + predecessor binding |
| changed expected raw digest | `FAIL_PROVENANCE` | pinned study-freeze binding |
| malformed expected raw digest | `FAIL_PROVENANCE` | pinned study-freeze binding |
| changed source-manifest digest | `FAIL_PROVENANCE` | pinned study-freeze binding |
| modified predecessor freeze | `FAIL_PROVENANCE` | raw + predecessor binding |
| modified source bytes | `FAIL_PROVENANCE` | source-manifest binding |

Direct and CLI JSON were equal in 8/8 cases. CLI exit was 0 only for the exact original and 1 for all seven tamper cases. Mutation files, direct outputs, CLI outputs, and `formal_result.json` are retained under `results/`.

Reproduction from repository root:

```sh
AUDIT_OUTPUT_DIR="$(mktemp -d)"
docker --context orbstack build --network none -f research/audits/issue_3688_raw_byte_binding_v1/Dockerfile -t issue-3688-raw-byte-binding:formal .
docker --context orbstack run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m -v "$PWD/research/audits/issue_3688_raw_byte_binding_v1/inputs:/inputs:ro" -v "$AUDIT_OUTPUT_DIR:/out:rw" issue-3688-raw-byte-binding:formal@sha256:8c37d3a0ff21d1205a00c567fd184184816ab00d81292cb0feee7be92d572f64 python3 /work/test_raw_byte_binding.py /inputs /out
printf 'Fresh audit outputs retained at %s\n' "$AUDIT_OUTPUT_DIR"
```

Use a fresh empty output directory on every reproduction. The committed
`results/` tree is evidence input and must not be mounted as the writable
runner output.

## Independent second-container audit

The first independent-verifier implementation had a Python set/dict comparison bug and stopped before reading case receipts. A separate v2 verifier was then built against the same pinned base image and run in a fresh `--network none`, read-only-rootfs container. Original inputs and formal `results/` were mounted read-only; only `independent/` was writable. It reconstructed all eight receipts and returned `PASS_INDEPENDENT_RAW_BYTE_AUDIT`, `errors=[]`. Verifier/container assembly failures are listed in `AUDIT_ATTEMPTS.md`; none changed raw, freeze, or formal result bytes.

Final independent image: `sha256:35cae705c82c653e5a98b2f40a0827e443e68e03b3184140eb877db1f7b693f5`.

## Scope

This is offline provenance validation for the exact retained #3675/#3676 evidence and the finite mutations listed above. It is not another XRes/X11 allocation and does not claim general audit completeness or product/default-runtime readiness.

## Integration revalidation (2026-09-20 17:22 UTC)

An integration worker independently reran the retained v2 receipt verifier in
a fresh OrbStack container, without rerunning the formal mutation matrix. The
container was Linux/arm64 from image
`sha256:35cae705c82c653e5a98b2f40a0827e443e68e03b3184140eb877db1f7b693f5`,
with `--network none`, a read-only root filesystem, read-only `/inputs` and
`/formal` mounts, and a dedicated writable `/out` mount. It returned
`PASS_INDEPENDENT_RAW_BYTE_AUDIT`, eight reconstructed cases, and zero errors.
The retained stdout JSON is `independent/integration_review_20260921.json`
(SHA-256 `abd3b83b96e7f4c92aff106c808e36ca8d2ea2a3f2d50f6e62fec978f1df2f51`).
