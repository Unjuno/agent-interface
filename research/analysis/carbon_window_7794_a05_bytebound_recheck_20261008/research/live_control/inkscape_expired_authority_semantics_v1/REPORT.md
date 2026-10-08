# Inkscape legacy `expired` → `authority_ended` semantic audit v1

Status: **FAIL_DIRECT_UPGRADE / RETAIN_SEMANTIC_MISMATCH**.

Immutable base: `0bf4103e69e4108f92a153e38a5ea1f7253f1f93`. Tracks #163. This is a retained-artifact/source audit only: no new GUI session, model call, OS input, socket/network effect, or production promotion.

## Question

The retained durable-submit composition can safely precommit a request identity, consume a durable authority-end token inside the transport callback, and only then perform actual transport. Before using that composition on the established Inkscape expiry-observation path, this audit asks whether the old Inkscape terminal can honestly produce the newer `authority_ended` receipt without inventing evidence.

It cannot.

## Retained source identity

The audited real Inkscape seed-240 run is `results/expiry-observation-01`. Its event stream Git blob is `aae6d81013e479d2ad1f2f068ccc4c8ad5c8c653`.

Frozen relevant sources:

- `probe_expiry_observation_v1.py`: blob `3c6e3ad67199ad530a1ae9ef64c34cd543022790`, SHA-256 `3bb2f3f5255c08dd7dd04e2b212b6ed9444bc9fcdc34e02a874066518ddac045`;
- `post_release_observation_v2.py`: blob `83b7ebda20cc2aa499ca3e9f7ee18ce8bb291e07`, SHA-256 `d53cf8ca86d4a932467313da8ac7400748511792c7da60b1d365caf246b01be7`;
- unchanged `authority_ended_bridge_v1.py`: blob `9fcfdce5229cb58b3d1a17aacbcef0cb44bd10f1`, SHA-256 `2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e`.

The original Inkscape probe already proved useful safety facts: terminal `status=expired`, zero completed steps, verified empty release, two passive post-release captures, and fresh observation sequence advancement after release.

## First outcome

Decision: `FAIL_DIRECT_UPGRADE_RETAIN_SEMANTIC_MISMATCH`.

Six required bridge fields are contradictory, ambiguous, or unavailable under the retained legacy evidence:

| New bridge field | Retained legacy evidence | Classification |
|---|---|---|
| `terminal_status` | `expired` | **CONTRADICTORY** to required `authority_ended` |
| `post_authority.captures` | `2` | **CONTRADICTORY** to exact `1` |
| `post_authority.sequence` | `[7, 8]` | **AMBIGUOUS**: old two-capture contract has no canonical one-capture selection rule |
| `post_authority.within_lifecycle_deadline` | no such retained assertion | **UNAVAILABLE** |
| `post_authority.snapshot_finished_ns` | capture/image-ready/input-state times exist, but no value carrying the newer snapshot-finish contract | **UNAVAILABLE** |
| `post_authority.lifecycle_deadline_ns` | no post-authority lifecycle deadline | **UNAVAILABLE** |

Other required facts are supported: release verified, empty keys/buttons, zero post-release input admissions in the retained slice, nonnegative `steps_completed`, no renewed input authority, no old tail resumption, sequence advancement, and no post-release observation error.

## Why the old action deadline cannot be repurposed

The legacy action had `valid_until_ns = 6,655,636,547`. It is an **action-admission deadline**, not an independent post-authority observation lifecycle deadline.

Measured ordering from retained evidence:

- verified release: `6,656,981,484 ns`, which is **1.344937 ms after** the old deadline;
- first passive post-release capture: `6,750,655,382 ns`, **95.018835 ms after** the old deadline;
- first image-ready time: `6,761,944,948 ns`, **106.308401 ms after** the old deadline;
- second passive capture: `6,862,231,317 ns`, **206.594770 ms after** the old deadline.

Therefore mapping the expired command deadline into `lifecycle_deadline_ns` would not merely be a provenance error; it would also fail the newer timing relation.

## Unchanged-bridge rejection ladder

The evidence-only receipt preserves `terminal_status=expired`, `captures=2`, and omits unavailable lifecycle timing. The unchanged bridge rejects first with:

`scheduled authority_ended status required`

For diagnosis only, two prohibited counterfactual mutations were tested:

1. relabel only `expired -> authority_ended` → `exactly one passive post-authority capture required`;
2. additionally collapse two captures to one/latest sequence → `post-authority observation outside lifecycle deadline`.

These counterfactuals are **not** accepted evidence. They show that a string rename is insufficient and that the mismatch is multi-dimensional.

## Architectural consequence

Do not directly compose the old Inkscape expiry terminal with the durable authority token + durable-submit handoff. Doing so would require semantic fabrication.

The smallest justified next candidate is versioned and narrow:

1. emit the new `authority_ended` status only at the actual authority-ending boundary;
2. after verified release, take exactly one passive post-authority capture under an independently defined bounded lifecycle deadline;
3. retain its singular sequence and explicit `snapshot_finished_ns` / `lifecycle_deadline_ns` / `within_lifecycle_deadline` receipt;
4. prove zero post-release input admission and no tail resumption;
5. only then feed that receipt to the already-retained durable token + durable-submit composition.

Do not add a model for this step.

## H / T / D / C / U

**H.** The legacy Inkscape expiry evidence cannot be directly upgraded to `authority_ended` without fabricated status/capture/lifecycle semantics.

**T.** Byte-identified retained source/artifact audit; every new receipt field classified as direct, mechanically derived, contradictory/ambiguous, or unavailable; unchanged bridge exercised on the evidence-only receipt. One first outcome, no tuning.

**D.** **FAIL_DIRECT_UPGRADE / RETAIN_SEMANTIC_MISMATCH.** Six required fields fail provenance/contract closure; unchanged bridge rejects; the old deadline is temporally invalid for post-authority observation.

**C.** A detailed legacy artifact could have contained a separately defined post-authority lifecycle deadline and singular snapshot-finish receipt not asserted by the high-level probe. The retained event stream does not contain such a contract.

**U.** CPython 3.13.5, Linux 6.18.44 x86_64. Artifact/source audit only; no live GUI, no model, no OS input, no network/runtime failure claim.

## Next smallest experiment

Implement only the missing status + one-capture lifecycle receipt in a versioned Inkscape/executor candidate, first under offline/fault controls. Gate live use on exact bridge acceptance and malformed/late/two-capture controls. If those pass, run one model-free real Inkscape expiry with the new receipt, then compose it with the already-retained durable-submit callback ordering.
