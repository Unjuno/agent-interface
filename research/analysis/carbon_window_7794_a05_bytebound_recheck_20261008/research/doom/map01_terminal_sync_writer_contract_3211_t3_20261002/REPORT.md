# MAP01 terminal trace-writer contract — T3 result

Disposition: **PASS_WRITER_CONTRACT_SCOPED**. This is a synthetic serialization-contract result, not a MAP01 or recovery result.

## H / T / D / C / U

- **H:** A corrected JSONL writer emits each event as one physical JSON record even when a value contains an embedded newline; the exact historical delimiter control does not.
- **T:** Frozen package at main `73235730af05375fddf3a9d102d30632e7d43af5`; candidate launched one synthetic Python child and wrote the identical two-event sequence through fixed and legacy-control writers. An independent auditor checked process exit, event order/content, raw sizes/hashes, physical line counts and ordinary JSONL decoding.
- **D:** Candidate exit 0; 2 exact events (`probe`, then `terminal`). Fixed `session-events.jsonl`: 100 bytes, 2 physical lines, SHA-256 `be2fed607255cb2d98165e5c5303c10eb2488f990d35923526fa412552427454`; strict JSONL decoded both exact events. Historical control: 110 bytes, 1 physical line, SHA-256 `db04370fa45f76c84e9cc9c3ff562bc81bfae99af60fe39149572d0c5d4eae9d`; ordinary line parser rejected it. Independent auditor returned `PASS_WRITER_CONTRACT_SCOPED` with matching hashes and zero errors.
- **C:** The target-side writer change is validated only as an isolated contract. The source runner remains unmodified, and T3 does not test queue timing, process cleanup under MAP01, or the recovery-arm terminal.
- **U:** The #3202/#3211 timeout remains unexplained. The absent recovery trace is still not identifiable as dropped, delayed, omitted, or lost during packaging. No formal allocation, game, model, GUI, input, efficacy, or MAP01 outcome is inferred. Candidate 1; independent auditor 1; retries 0.

## Verification

- Freeze manifest/source hashes verified before the candidate.
- `python -B -m unittest -v test_construction.py`: **4/4 passed**.
- In-memory Python `compile(...)` check for all four `.py` files: **PASS**.
- `python -B candidate.py --out results/t3-01`: one invocation, exit 0.
- `python -B audit.py --out results/t3-01`: one invocation, exit 0; retained in `AUDIT.json`.
- Docker Desktop was not started or modified. At the read-only check, `com.docker.service` was Stopped/Manual and `docker version` timed out after four seconds. Shared container inventory/ownership was unknown and no owner-bound slot was transferred, so there was no container invocation.
- No workflow dispatch, GPU/model, game, GUI/input, old runner, consumed allocation, or retry.

## Integration boundary

This is a standalone additive writer-contract prototype. It does **not** patch the frozen diagnostic runner or automatically authorize its use in another allocation. Any adoption must be reviewed as a scoped diagnostic-format correction, with the timeout lifecycle handled separately.

Raw event files and receipts are under `results/t3-01/`; input identity is in `FREEZE.json`; all retained file hashes are listed in `SHA256SUMS`.
