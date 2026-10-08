# Issue #5352 T10 — observed bound-breach fail-closed response

## Disposition

`PASS_BOUND_BREACH_STOP_SCOPED` for the frozen finite simulator and raw audit.
This is not runtime, task-safety, or MAP01 evidence.

## H / T / D / C / U

- **H:** A generation/sequence-bound gate can stop further local permits after
  an observed out-of-bound or critical event without suppressing in-bound
  continuation or silently rearming after stale evidence.
- **T:** Fixed inclusive disturbance bound 3. The runner enumerated all
  disturbance sequences of lengths 1–4 over `{0,1,2,3,4}` and compared static
  continuation with a per-observation fail-closed gate. Eight explicit
  controls covered current critical events, generation change, sequence gap,
  duplicate sequence, exact bound 3, breach 4, and a lower-valued sample after
  breach.
- **D:** The runner exited 0 after exactly one invocation. The independent
  raw-only auditor exited 0 with `errors=[]` and reconstructed all 788 rows.
  All 780 in-bound traces match static continuation. Of 440 traces containing
  a breach, 355 allow 730 total later local permits in the static arm; the
  candidate permits zero after the first breach. All eight controls matched
  their frozen literal expectations. No candidate code was imported by the
  auditor.
- **C:** Both arms received identical traces and horizon; only the candidate's
  current evidence/critical/bound gate differed. CPython 3.11.9 x64, local
  Windows, standard library only. No container, model, GPU, CUDA, network, GUI,
  or effectful input.
- **U:** Synthetic finite model; the threshold is not calibrated. This does
  not prevent the first out-of-bound event, establish that it is observable
  before harm, or prove runtime authority, task quality, latency, live-control
  efficacy, reliability, human tempo, or cross-domain transfer.

## Execution record

- Construction: `py -3.11 -B -m unittest -v test_runner` — 8/8 passed; AST
  parse passed for all three Python sources.
- Formal runner, exactly once: `py -3.11 -B runner.py > output/RAW.jsonl` —
  exit 0; raw SHA-256
  `cd5a78203b7b4b89fd078fb96dd93508980ac42f5d04b5542c6f34352b7f1322`,
  172,193 bytes.
- Independent audit, exactly once: `py -3.11 -B audit.py output/RAW.jsonl` —
  exit 0; `PASS_BOUND_BREACH_STOP_SCOPED`, `errors=[]`.
- Lossless transport: deterministic gzip (`mtime=0`), 4,914 bytes,
  SHA-256 `5dc5102d139a5b90b356d71f9639add53b1d7ac76a0b28b45dd578593af02cc7`,
  stored base64-encoded in `results/formal-01/RAW.jsonl.gz.b64`.
- No retries, tuning, or additional candidate execution occurred.

## Relation to T9

T9 reported violations under an actual disturbance alphabet wider than its
declared bound and identified a separate fail-closed response as one possible
next step. T10 tests only the response after a breach is observed. It is a
different finite horizon and does not re-evaluate T9's counts or calibrate the
disturbance bound.

## Reproduction and source identities

Frozen source, environment, commands, decision gates and source hashes are in
`FREEZE.json`; first outcome and audit receipt are in `results/formal-01/`.
The candidate runner, independent oracle and construction tests are retained
beside this report. Historical #5352 results remain unchanged.

