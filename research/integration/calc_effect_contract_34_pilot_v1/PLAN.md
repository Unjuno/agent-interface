# Issue #4626 — Calc persistence-boundary construction pilot

Allocation: `calc-effect-contract-34-pilot-20260927-01`  
Base at intake: `e786135bf5576f308c7d0185cfb484b9970bf6de`  
Image: `issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393` (`linux/arm64`)  
Owned branch/path: `research/calc-effect-contract-34-pilot-20260927` / `research/integration/calc_effect_contract_34_pilot_v1/`

## H / T / D / C / U

- **H:** Calc may display the requested cell value in its live document while the saved XLSX still has the previous value. Program termination or live-view agreement is not evidence that the declared saved-document effect occurred.
- **T:** One fresh Xvfb/Calc process opens a disposable workbook with A1=0, changes A1 to 7 through local UNO, and intentionally never calls `store`/`save`. A separate read-only observer independently opens the saved XLSX after the UI runner records the live value. A pure classifier contrasts terminal-only, live-required-effect, and saved-effect-contract outcomes.
- **D:** Runner emits an immutable per-run `raw.json`; `audit.py` independently rereads the workbook, verifies pre/post SHA-256 and cell values, then emits `audit.json`. Exactly one case. No retry, no model/API/provider.
- **C:** Pinned Linux/arm64 image; `--network none`, read-only root and source, disposable output mount, fresh user profile. No user data or physical desktop. The UNO operation targets an actual Calc GUI process in Xvfb; it does not represent a public runtime or planner integration.
- **U:** One synthetic unsaved-cell case only. No modal persistence, delayed save, wrong target, collateral edit, model-facing token/cost, recovery, promotion, or cross-app result.

### Frozen acceptance

`PASS_CALC_PERSISTENCE_BOUNDARY_CONSTRUCTION_ONLY` iff Calc reports live A1=7, an independent reopen reports persisted A1=0, source SHA-256 is identical before/after, terminal-only and live-view shortcut classifiers would accept while the saved-effect classifier refuses VERIFIED, and the independent audit has zero errors. Missing or mismatched evidence is `STOP_CONSTRUCTION`; it is not converted to a scientific negative. Formal case count is zero and this pilot cannot satisfy Issue #34's promotion boundary.

### Exact command (workspace construction)

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=512m \
  --pids-limit=128 --memory=2g --cpus=2 \
  -e HOME=/tmp/home -e XDG_CACHE_HOME=/tmp/cache -e XDG_CONFIG_HOME=/tmp/config \
  -v "$PWD/work/calc_effect_contract_34_pilot_v1:/src:ro" \
  -v "$PWD/work/calc_effect_contract_34_pilot_v1/results:/out:rw" \
  --entrypoint sh \
  issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 \
  -c 'python3 /src/runner.py && python3 /src/audit.py /out/calc-effect-contract-34-pilot-20260927-01/raw.json'
```

For a repository checkout after publication, replace both workspace paths above with `research/integration/calc_effect_contract_34_pilot_v1` (the read-only source mount) and its `results` child (the writable output mount).

The first local run is a construction result, not a source-frozen formal allocation. Preserve every output and any first failure; do not reuse this identity for another case.

### Publication-checkout path correction (post-run review response)

The tracked `results/` directory already contains the retained allocation and must not be mounted as `/out` for a new construction. If only checking the retained evidence, run the independent audit against the saved `raw.json` and workbook in read-only mode and write to a separate new audit path. If a fresh construction is explicitly authorized under a distinct allocation, mount an empty disposable directory as `/out`; never point `/out` at the tracked results directory. This correction does not authorize rerunning the original allocation.
