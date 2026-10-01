# Obstac/OrbStack runbook — Issue #3858

The immutable predecessor #3204 v2 STOP and #3827 STOP are not edited or reused. This successor corrects the image scanline filter and request format, retains the prior 12-row/9-call policy plan, and captures HTTP error bodies before any STOP.

## Construction-only rung

After `FREEZE.json` is complete, run:

```sh
python3 research/integration/issue_3858_model_facing_recovery_v3/launcher.py --construction
```

The mock bridge must receive 9 requests and return 9 mock records without contacting Ollama. Confirm 12 rows, 9 emitted requests, 0 model calls, valid filter-0 PNGs, exact hashes, and matching `OBSTAC_*` provenance. Construction is not model evidence.

## Formal one-shot

Commit/push the preregistration, source and freeze; record the branch/head and hashes on Issue #3858 first. Check the pinned image and local Qwen digest, and confirm `formal/output/` and `formal/exchange/` are empty. Then execute once:

```sh
python3 research/integration/issue_3858_model_facing_recovery_v3/launcher.py
```

The formal request budget is 9, retries are forbidden. On the first HTTP/infrastructure/model/provenance error the bridge must persist exact status/headers/body, the runner must stop issuing requests, and the result must remain STOP. Never repeat the allocation.

## Independent audit

After the formal run, stage the exact output/exchange and frozen inputs using:

```sh
python3 research/integration/issue_3858_model_facing_recovery_v3/audit_launcher.py
```

The independent audit runs under the same pinned image, OrbStack context and `--network none`; it recomputes PNG CRC/filter validity, every request/response byte-link, model/source/freeze identity, the policy result gate, and corruption controls without importing the candidate policy.
