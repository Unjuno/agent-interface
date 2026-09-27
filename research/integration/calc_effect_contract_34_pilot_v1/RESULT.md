# Construction result — Issue #4626

Allocation: `calc-effect-contract-34-pilot-20260927-01`  
Disposition: **`STOP_CONSTRUCTION`**  
Formal allocation cases: **0**; construction attempt: **1**; retries: **0**.

## Executed command and environment

Executed once against source files byte-identical to the frozen GitHub branch blobs. Container command:

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=512m --pids-limit=128 --memory=2g --cpus=2 \
  -e HOME=/tmp -e XDG_CACHE_HOME=/tmp/cache -e XDG_CONFIG_HOME=/tmp/config \
  -v "$PWD/work/calc_effect_contract_34_pilot_v1:/src:ro" \
  -v "$PWD/work/calc_effect_contract_34_pilot_v1/results:/out:rw" \
  --entrypoint sh \
  issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  -c 'python3 /src/runner.py && python3 /src/audit.py /out/calc-effect-contract-34-pilot-20260927-01/raw.json'
```

Observed image platform `linux/arm64`, LibreOffice Calc `7.4.7.2 40(Build:2)`, Python `3.11.2`, openpyxl `3.0.9`, UNO, Xvfb. Network disabled; root and `/src` read-only; only `/out` writable.

## First outcome (preserved)

- Calc opened a disposable XLSX with A1=0; the live UNO document reported A1=7 and `document_modified_unsaved=true`.
- No save/store call was made. An independent openpyxl read while Calc still held the document reported on-disk A1=0.
- The baseline and post-action workbook SHA-256 both equal `9f5fc410d9c67430ca60ed99d47eeb774a6342f578d52c6127708ecc8dc07323`.
- The raw actor classified terminal-only and live-value-only shortcuts as `VERIFIED`, while the saved-effect contract classified the independently observed mismatch as `CONTRADICTED`.
- However, the frozen audit's visible-window predicate used `xdotool search --onlyvisible --class soffice`, which returned no IDs. The independent audit therefore correctly emitted `STOP_CONSTRUCTION` with the sole error `no visible Calc window was detected`; this allocation is **not** relabeled as PASS.

Raw file SHA-256: `55dbaefdc28dd93f10cbb0476797894be093edad8992cd9fca0b8f37ba4e5061`.  
Audit file SHA-256: `fc2fa81deaa038758b80e83c1ae72923e7d6774b964ba0d8396f40e83835e618`.  
Generated baseline workbook SHA-256: `9f5fc410d9c67430ca60ed99d47eeb774a6342f578d52c6127708ecc8dc07323` (4,815 bytes).

## Separate environment diagnostic (not a rerun)

A separate blank-document Xvfb/Calc process was used only to diagnose the selector. `xdotool ... --class soffice` again returned no IDs, while `xwininfo -root -tree` showed the visible `VCL ImplGetDefaultWindow` at 1280×800; `wmctrl` reported no EWMH client-list property because no window manager is present. This demonstrates that the chosen class filter is incompatible with this image's Xvfb/window setup. It does not retroactively prove that the original task window was visible, so the original STOP remains.

## Scope and next gate

The retained rows are a useful observed live-versus-disk discrepancy but do not satisfy the frozen acceptance gate because same-run visible-window evidence is missing. No modal, delayed-save, collateral-edit, model-facing, latency/cost, recovery, integrated-runtime, or cross-app claim follows. Do not rerun this allocation. A new source-frozen allocation with a root-window-aware UI observer would require a distinct successor and path; keep all files here unchanged.
