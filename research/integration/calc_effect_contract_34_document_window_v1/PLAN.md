# Issue #4667 — identify Calc document-window visibility

Allocation: `calc-effect-contract-34-document-window-20260927-01`  
Base: `5db30b52e3a1e89a18d2696002090fffe65931e1`  
Image: `issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393` (`linux/arm64`)  
Branch/path: `research/calc-effect-34-document-window-20260927` / `research/integration/calc_effect_contract_34_document_window_v1/`

## H / T / D / C / U

- **H:** The document-titled Calc top-level window can be mapped/viewable even while the private `VCL ImplGetDefaultWindow` helper is unmapped. This will clarify what the #4643 visibility contradiction refers to.
- **T:** One new fresh workbook/profile/display. After UNO changes A1 from 0 to 7 without saving, record the root tree and `xwininfo -id` output for every direct child XID; independently reopen disk workbook and compare SHA-256.
- **D:** PASS only when the expected document-title child occurs exactly once, is `IsViewable`, every direct child ID has exactly one successful attributes record, live A1=7, disk A1=0, and hashes match. Explicit non-viewable document window is contradiction; missing/ambiguous identity/state is STOP. Construction-only, not formal #34 evidence.
- **C:** Pinned image, network none, read-only root/source, disposable outputs, fresh private profile. No model/API/user data/physical desktop, no save, one run, retries 0.
- **U:** Xvfb presentation state for one Calc document only; no runtime policy, modal, delayed save, cost, recovery, cross-app or product evidence.

## Exact run

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=512m --pids-limit=128 --memory=2g --cpus=2 \
  -e HOME=/tmp/home -e XDG_CACHE_HOME=/tmp/cache -e XDG_CONFIG_HOME=/tmp/config \
  -v "$PWD/work/calc_effect_contract_34_document_window_v1:/src:ro" \
  -v "$PWD/work/calc_effect_contract_34_document_window_v1/results:/out:rw" \
  --entrypoint sh \
  issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  -c 'python3 /src/runner.py && python3 /src/audit.py /out/calc-effect-contract-34-document-window-20260927-01/raw.json'
```
