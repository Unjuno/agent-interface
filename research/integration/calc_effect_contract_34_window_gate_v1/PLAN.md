# Issue #4643 — same-run Xvfb visibility-gated Calc construction

Allocation: `calc-effect-contract-34-window-gate-20260927-01`  
Base: `6081879249170a41cd4467cbbe47b18012d71d41`  
Image: `issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393` (`linux/arm64`)  
Branch/path: `research/calc-effect-34-window-gate-20260927` / `research/integration/calc_effect_contract_34_window_gate_v1/`

## H / T / D / C / U

- **H:** The earlier `xdotool --class soffice` failure was an observer incompatibility. In a new Calc process, a root-tree VCL child with same-run `Map State: IsViewable` can satisfy the visibility evidence while live A1=7 remains unsaved, disk A1=0, and the source hash remains unchanged.
- **T:** One new workbook/process/allocation: edit A1 0→7 through Calc UNO, never save, capture X root tree and target VCL window attributes in the runner, independently inspect saved workbook and hash. Separate auditor consumes only retained raw and workbook, never imports runner.
- **D:** `PASS_WINDOW_GATED_CONSTRUCTION_ONLY` iff the auditor identifies exactly one VCL root-tree child, its captured attributes state `IsViewable`, live A1=7, independently reopened disk A1=0, and pre/post/current SHA-256 match. Missing/ambiguous evidence is STOP; values contrary to hypothesis are contradiction. This is construction-only, not a formal #34 allocation.
- **C:** Pinned linux/arm64 LibreOffice image, network none, read-only root and source, disposable output, new profile; no user files, physical desktop, model, or retries.
- **U:** One synthetic cell, no public runtime/planner, modal, delayed save, wrong-target, collateral-edit, recovery, cross-app, cost, or product claims.

## Exact run

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=512m --pids-limit=128 --memory=2g --cpus=2 \
  -e HOME=/tmp/home -e XDG_CACHE_HOME=/tmp/cache -e XDG_CONFIG_HOME=/tmp/config \
  -v "$PWD/work/calc_effect_contract_34_window_gate_v1:/src:ro" \
  -v "$PWD/work/calc_effect_contract_34_window_gate_v1/results:/out:rw" \
  --entrypoint sh \
  issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  -c 'python3 /src/runner.py && python3 /src/audit.py /out/calc-effect-contract-34-window-gate-20260927-01/raw.json'
```

Exactly one construction attempt; retries 0. Original #4626 artifacts remain immutable.
