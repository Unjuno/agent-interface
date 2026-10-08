# Issue #6001 T0 allocation-02: mount-contract STOP

## H / T / D / C / U

- **H:** A frozen no-provider T0 audit detects a planted in-deck behavior shift under a stable alias and prevents false route-effect attribution under balanced route order, while distinguishing out-of-deck, schema, prompt/context and stationary controls.
- **T:** One fresh isolated ARM64 OrbStack guest was created during the bounded 13:00–13:15 UTC window. The frozen nested-Docker source expected guest `/study/src`; selective host mount `/private/tmp/issue6001-t0-a02/src:/study` exposed the source files directly under `/study`. Output mount `/out` was empty. The source-layout gate failed before image pull, Docker candidate, or auditor.
- **D:** `STOP_GUEST_MOUNT_LAYOUT_MISMATCH / NOT_EVALUATED`. Candidate=0, container=0, auditor=0, retries=0. This is not `FAIL_METHOD` or scientific PASS.
- **C:** Allocation-01's earlier STOP is immutable and separate. This allocation used its own guest and output directory. The local source/auditor rehearsal passed, but does not repair the formal STOP.
- **U:** Docker execution, candidate/auditor behavior inside the pinned image, and all scientific classifications are unevaluated. Issue #6001's separate canary-induced shared-service interference refinement is not covered by this T0 package.

## Provenance

- Issue: [#6001](https://github.com/Unjuno/agent-interface/issues/6001)
- Allocation: `MODEL-API-CANARY-6001-T0-20261001-02` (consumed; no retry)
- STOP record: [Issue comment #5932240727](https://github.com/Unjuno/agent-interface/issues/6001#issuecomment-5932240727)
- Frozen prep main: `d0df957955f3b837caedbfb57a74b21a24d5000f`
- Main read at start window: `722c42bf0d6d808cf80575ecb6353401de934b26`
- Guest: `agent-interface-6001-t0-a02-20261001`; stopped and observed stopped after the mount gate.
- Pinned intended image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/arm64`. It was not pulled or invoked in this allocation.

## Retained source identities

SHA-256 values from the prospective freeze:

| File | SHA-256 |
|---|---|
| `src/candidate.py` | `d4276e8ad748583d074433287836cb9ed432ebfa041683ce0656582ed51aaabf` |
| `src/audit.py` | `5076a1e03e5ffc38d8707b4b273108cb21e0304f79c231d3a02ded9521570341` |
| `src/PROTOCOL.md` | `411af2524574f6d104763e820d01035fa21c0bc79690f676da00a1d2a5464ad9` |
| `src/freeze.json` | `08a36e2b5b59acc73002e784720fd9f7281d6a335c7530c9da7ef3932b0dba07` |

`results/construction/raw.jsonl` is the post-slot host-only construction rehearsal: 29,605 rows, SHA-256 `80b0df668daec138ece457368ef24691b941d1050810735c0a031a64e64e6bd2`. The independent raw-only auditor returned `PASS_METHOD_SCOPED`, errors `[]`, and 0/200 stationary fixture false alarms (95% Wilson upper bound 0.018846). This quantifies this synthetic fixture only. It is not Docker/OrbStack or provider evidence.

Earlier host rehearsals remain preserved in the local preparation directory `/private/tmp/issue6001-t0-a02/` and are not duplicated in this publication. They must not be pooled with the formal allocation (which emitted no rows).

## Reproduction and gates

From this directory:

```sh
python3 -m py_compile src/candidate.py src/audit.py
python3 src/candidate.py /tmp/issue6001-construction.jsonl
python3 src/audit.py /tmp/issue6001-construction.jsonl
```

These are host-only construction checks. The exact formal STOP cannot be rerun under allocation-02. A future distinct allocation requires a prospective corrected selective-mount destination (guest `/study/src`), an empty unique output path, fresh queue/ownership confirmation, and a new explicit bounded grant. No successor allocation is authorized here.

## Initial branch check

`git ls-remote --heads origin` returned no branch matching `6001` or `model-api-canary`; GitHub MCP branch search likewise found none. The evidence directory above was absent before this branch was created.
