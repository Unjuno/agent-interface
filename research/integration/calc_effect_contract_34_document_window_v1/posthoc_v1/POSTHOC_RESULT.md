# Post-hoc container audit result — Issue #4667

Supplemental audit of the already-retained one-case construction; no Calc process, GUI action, or experiment allocation was launched.

Disposition: **`PASS_DOCUMENT_WINDOW_VISIBLE_CONSTRUCTION_ONLY`**  
Post-hoc container invocations: **1**; new scientific/formal cases: **0**.

## Frozen inputs and command boundary

- Audit source branch: `research/calc-effect-34-doc-window-audit-20260927`; source blob `5694045bea7b2d8fa445c065423c21b06a740fe6`.
- Unit test source blob: `df094ac9864066e57839641c27cd681784e3d82a`; plan blob: `c172187955ff5ae1ce0e9a3a7b32496698461d0c`.
- Evidence was first read back from `main` and byte-checked against local: raw Git blob `8b9c85ed3c05fe98f9e6600d3137670518c3e091`; frozen audit blob `ad39bf497732505717e2f6a08cb8a3608274a256`; XLSX base64 blob `28deb48554efb1f3bd91eb520cdd704f59b49fd3`.
- Pinned image: `issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393` (`linux/arm64`). OrbStack Docker Engine 29.4.0.
- One audit-only container used `--network none --read-only`, 256 MiB tmpfs, 64 PIDs, 1 GiB RAM and 1 CPU. Auditor source and staged raw/frozen-audit/base64-workbook evidence were read-only; only the new result directory was writable. No model, network, Calc, user data or action.

## Result

- Auditor exit: 0; errors: `[]`.
- Raw and frozen-audit hashes independently matched the retained files; workbook decoded in memory from the lossless `.b64` representation and reopened as A1=0 with SHA-256 `00e11e4c41a8df87bb5e8bee8b86654c7d33bc8e62c52d11bccf4e6dcc7fc8ea`.
- All 14 child XID receipts reconciled. Exactly one document window (`0x200325`) was `IsViewable`; the single VCL helper (`0x20000b`) was `IsUnMapped`.
- The post-hoc disposition matches the frozen v1 audit and retains the construction-only scope.

Post-hoc output SHA-256: `64a06053fd5208ea4346a26706581e179b0b31279c29c831fed1c5d1541640db`. This output is byte-identical to the host-side posthoc result for the same committed evidence.

Local validation after container execution: 13/13 corruption/decision tests passed; `py_compile` passed; a host reconciliation confirmed output/input bindings and the scoped PASS.

## Reproduction

Stage byte-verified `raw.json`, frozen `audit.json`, and `document-window-probe.xlsx.b64` in a disposable read-only evidence directory; no XLSX extraction is needed. Mount that directory at `/evidence`, mount `audit_hardened.py` read-only at `/src/audit_hardened.py`, and mount a new empty results directory at `/out`:

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m --pids-limit=64 --memory=1g --cpus=1 \
  -v "$PWD/research/integration/calc_effect_contract_34_document_window_v1/posthoc_v1/audit_hardened.py:/src/audit_hardened.py:ro" \
  -v "$EVIDENCE_DIR:/evidence:ro" \
  -v "$OUT_DIR:/out:rw" \
  --entrypoint python3 \
  issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  /src/audit_hardened.py --raw /evidence/raw.json --frozen-audit /evidence/audit.json --out /out/posthoc_audit.json
```

The original #4667 evidence and merged PR #4760 remain unchanged. The supplement validates one existing synthetic construction only; formal Issue #34 cases remain zero.
