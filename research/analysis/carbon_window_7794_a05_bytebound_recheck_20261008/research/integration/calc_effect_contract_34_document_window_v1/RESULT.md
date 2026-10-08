# Construction result — Issue #4667

Allocation: `calc-effect-contract-34-document-window-20260927-01`  
Disposition: **`PASS_DOCUMENT_WINDOW_VISIBLE_CONSTRUCTION_ONLY`**  
Formal Issue #34 cases: **0**; construction attempts: **1**; retries: **0**.

## Frozen inputs and runtime

- Branch/base: `research/calc-effect-34-document-window-20260927` / `5db30b52e3a1e89a18d2696002090fffe65931e1`.
- Pinned image: `issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393`; independent image inspect returned the same image ID, `linux/arm64`.
- Source Git blob IDs read back from the frozen branch and rechecked locally: PLAN `8926a8ac67da0d90564b11a479072032b7749172`; runner `2e6ee81adfaa85b2bf6df2ca05ac814c30f4aafc`; auditor `fafd7f3956ca6bec89aa0c4ed23aa90484f88e13`.
- OrbStack Docker Engine 29.4.0 (`linux/arm64`), LibreOffice Calc `7.4.7.2 40(Build:2)`.
- One invocation used `--platform linux/arm64 --network none --read-only`, `/src:ro`, a distinct `/out:rw`, 512 MiB `/tmp`, 128 PIDs, 2 GiB RAM and 2 CPUs. No model/API, user desktop, external network, or save/store call.

## Observed result

- Fresh workbook started with A1=0; live UNO document became A1=7 and reported modified/unsaved.
- Root tree contained 14 child XIDs; every same-run `xwininfo -id` query exited 0 and matched its requested XID.
- Exactly one document-titled window, `document-window-probe.xlsx - LibreOffice Calc` (`0x200325`), was `IsViewable`.
- The separate `VCL ImplGetDefaultWindow` (`0x20000b`) was `IsUnMapped`.
- Independent XLSX reopen found A1=0; no save/store was called; before/after workbook SHA-256 was identical: `00e11e4c41a8df87bb5e8bee8b86654c7d33bc8e62c52d11bccf4e6dcc7fc8ea`.
- The frozen independent auditor returned `errors=[]`, document-window count 1 and `PASS_DOCUMENT_WINDOW_VISIBLE_CONSTRUCTION_ONLY`.

Raw SHA-256: `ab1e362f78c87db0eab240767750d09d1815cfcf82d22da97272d7dd973d1e78`.  
Audit SHA-256: `8c1887e52562f647f3867062efcaf145102bc4688d0fafa9eb6e28f95c875bbc`.

The publication bundle stores the XLSX bytes losslessly as `document-window-probe.xlsx.b64`; its decoded bytes have the source SHA-256 above. To independently replay the frozen auditor, decode that file to `document-window-probe.xlsx` beside a copy of `raw.json` in a disposable directory, then run `python3 audit.py <disposable-directory>/raw.json`. Do not overwrite the retained `audit.json`.

## Exact command

```sh
/Users/taka/.orbstack/bin/docker --context orbstack run --rm --platform linux/arm64 \
  --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=512m \
  --pids-limit=128 --memory=2g --cpus=2 \
  -e HOME=/tmp/home -e XDG_CACHE_HOME=/tmp/cache -e XDG_CONFIG_HOME=/tmp/config \
  -v "$PWD/work/calc_effect_contract_34_document_window_v1:/src:ro" \
  -v "$PWD/work/calc_effect_contract_34_document_window_v1/results:/out:rw" \
  --entrypoint sh \
  issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  -c 'python3 /src/runner.py && python3 /src/audit.py /out/calc-effect-contract-34-document-window-20260927-01/raw.json'
```

## Scope

This resolves only the one-case Xvfb presentation construction: the document window was viewable while the VCL helper was unmapped. It does not revise #4643's frozen row, prove formal #34 runtime behavior, or establish modal/delayed-save behavior, model/task efficacy, recovery, latency, cross-app generality, or product readiness. Preserve every original and post-hoc predecessor artifact unchanged.
