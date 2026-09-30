# Post-hoc audit supplement — Issue #4667

This is a separate validation of the single retained construction result, not another Calc invocation. The frozen `runner.py`, `audit.py`, raw JSON, workbook and v1 `audit.json` remain unchanged.

## H / T / D / C / U

- **H:** An evidence auditor that binds the exact allocation/image, harness, frozen-audit/raw/workbook hashes, complete root-child query inventory, and workbook value will preserve the scoped PASS; a positively observed document window in either `IsUnMapped` or `IsUnviewable` is contrary evidence, not missing evidence.
- **T:** Run `audit_hardened.py` read-only against the retained `raw.json`, frozen `audit.json`, and original workbook bytes (or the lossless `.b64` publication form). The auditor independently parses the root tree and each same-run `xwininfo` receipt, reopens A1, recomputes source/raw/audit hashes, and never imports the runner or v1 auditor. No GUI or task operation; output is a new path.
- **D:** PASS only if identity and every receipt reconcile, exactly one expected document title is `IsViewable`, exactly one VCL helper is `IsUnMapped`, live A1=7, disk A1=0, no save/store, stable source hash, and the frozen audit is bound to those bytes. Valid positive `IsUnMapped`/`IsUnviewable` on the document window is `CONTRADICTED_DOCUMENT_WINDOW_VISIBILITY`; incomplete, malformed, misbound, or corrupt evidence is `STOP_CONSTRUCTION`.
- **C:** Pinned linux/arm64 image; `--network none --read-only`; audit source and evidence mounted read-only; only a distinct fresh posthoc output path is writable. No experiment retry, model, user data, or shared runtime change.
- **U:** This only strengthens integrity/classification of one synthetic Xvfb construction. Formal Issue #34 cases remain zero; no runtime, model/task, timing, recovery, generality, or product claim.

## Local validation before publication

From the repository root, run:

```sh
python3 -m unittest discover -s research/integration/calc_effect_contract_34_document_window_v1/posthoc_v1 -p 'test_*.py' -v
python3 -m py_compile research/integration/calc_effect_contract_34_document_window_v1/posthoc_v1/audit_hardened.py
```

The tests include the observed visible-document case, both positive contrary map states, wrong image/allocation, incomplete harness, incomplete child receipts, unknown state, wrong disk value, incorrect raw binding, malformed tree and b64-only workbook decoding.

## Container audit command

After this source and exact evidence are committed/read back, run once in a fresh container. Here `/evidence` is a read-only directory containing `raw.json`, `audit.json`, and `document-window-probe.xlsx.b64`; the helper decodes the workbook in memory.

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m --pids-limit=64 --memory=1g --cpus=1 \
  -v "$PWD/research/integration/calc_effect_contract_34_document_window_v1/posthoc_v1:/src:ro" \
  -v "$PWD/research/integration/calc_effect_contract_34_document_window_v1/results/calc-effect-contract-34-document-window-20260927-01:/evidence:ro" \
  -v "$PWD/work/posthoc-4667-output:/out:rw" \
  --entrypoint python3 \
  issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  /src/audit_hardened.py --raw /evidence/raw.json --frozen-audit /evidence/audit.json --out /out/posthoc_audit.json
```
