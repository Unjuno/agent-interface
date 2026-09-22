# Retrospective publication — public API effect/result separation

This directory publishes a **completed conversation-local experiment** after the fact. It is not GitHub preregistration and no GUI/formal allocation is rerun here. The original local prospective freeze and all negative outcomes remain unchanged inside the lossless evidence capsule.

Refs #2337, #2246, #57, #55, #2789. Closes no broad parent.

## Retained scoped result

**PASS_PUBLIC_API_EFFECT_SEPARATION_SCOPED** on the original fixed source main `6e5a6dd60cd93aee300cd4bd11712bb9d6bd8520`.

One formal allocation, two fixed six-case batches, 12 fresh Tk app lifetimes, zero formal retries/replacements/post-freeze source changes:

| Condition | n | Application effect | Native result | Golden-v3 without app score |
|---|---:|---|---|---|
| Click A then type `7` | 2 | correct A=`7` | completed | partial / task_success=null |
| B remains recipient then top-level focus | 2 | wrong B=`7` | completed | partial / task_success=null |
| No Entry recipient | 2 | no Entry text effect | completed | partial / task_success=null |
| stale observation sequence | 2 | zero input | refused STALE_OBSERVATION | refused |
| stale binding revision | 2 | zero input | refused STALE_BINDING | refused |
| expired lease | 2 | zero input | refused LEASE_EXPIRED | refused |

All six native completions therefore do **not** become task success by default. A separately supplied cooperative exact-value scorer qualifies only the two correct effects. Missing/foreign score evidence never becomes success. The two wrong-field effects and two no-text effects remain negative task outcomes.

This is a result/effect-boundary check through the unchanged public Python `dispatch_golden_v3 -> api.dispatch -> selector -> core admission -> X11 session/backend` plus public read-only `observe`. It does not test CLI argument transport, MCP transport, model/provider authority, automatic semantic target acquisition, six-task end-to-end efficiency, general GUI safety, or a production scoring facility.

## Integrity

- original conversation ZIP: 410,936 bytes, SHA-256 `265585ea337afadb8a26a6a1559a3026d5642090065078c05adc043b8be28f69`
- original study members: 314
- local FREEZE SHA-256: `b06c3ed516af6780745afea19cee3ad178d5a262eb71c869ec63e0e3ad4a4c0b`
- original AUDIT SHA-256: `87b5fa704e76070b983408552f63433873c95a32c38cc874df3d6e0c5f7707eb`
- publication capsule: 90,896 bytes, SHA-256 `4a87b4eca0614d9ade3628a6f575d8af66c4c5a77d6663ec8e0c3537c31b8ada`
- raw-only audit: 12 cases, errors=[]
- frozen unit tests: 13 methods pass
- semantic copied-evidence corruptions: 12/12 rejected
- all 12 app, 2 Xvfb, and 2 batch-runner exits were retained and reconciled
- server-logical terminal key/button state was neutral in all 12 cases

The auditor is separately implemented/executed by the same author; this is not independent human review.

## Review without rerunning the allocation

The eight `evidence.part*.b64` files losslessly reconstruct `evidence.tar.xz`. Use a fresh destination:

```sh
python -B research/integration/public_api_focus_result_v1/unpack.py /tmp/public-api-effect-2337-review
cd /tmp/public-api-effect-2337-review
python -B verify.py
```

`verify.py` runs only read-only/offline validation. Do **not** run the consumed `run.py` or `execute.py` formal identities. Any new GUI allocation requires a separately justified prospective plan.

## Publication chronology and scope

The original README/REPORT/PLAN/FREEZE inside the capsule correctly state that GitHub writes were unavailable **in that earlier session**. Those historical files are preserved rather than rewritten. This publication occurs later through a newly available GitHub write connector.

Publication branch is additive only. No runtime, root direction document, predecessor artifact, or foreign branch is modified. Checks/review and merge are separate delivery gates; scientific disposition, evidence completeness, publication state, and product acceptance remain distinct.
