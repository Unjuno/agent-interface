# #5156 Allocation 06 — owner-thread key-up X11 fixture

Status: **successor source frozen to `9fc98fe`; 30/30 host contract tests pass; Allocation 06 STOP before runner because main advanced to `2fdeca6`; no X11 result**.

Task: `MAP01-OWNER-KEYUP-BRACKET-5156-20261001-06`  
Current-main freeze after #5537 T10 additive merge: `9fc98feb617c26fe1baa7ecc4decd43b69df8601`  
Allocation 05 pre-run STOP is retained separately at [its STOP record](../owner_keyup_formal_x11_5156_20261001_05/results/formal-01/STOP.json); do not retry or rewrite it.

## H / T / D / C / U

- **H:** For explicit per-key client key-up, an owner-thread `KeyRelease` request-to-`XSync` interval is identity-bound and nested inside its caller bracket, without changing admission, cancellation, or release behavior.
- **T:** After an exact exclusive Docker Desktop assignment, run one disposable Xvfb fixture: (1) one key down/up; (2) two keys down/down then sequential up/up with no intervening owner-state query; (3) cancel after one admitted key and reject the second. Independently audit the retained raw stream once, only if the runner exits 0.
- **D:** PASS only if the exact release inventory/order and key/owner/intent identities match, every explicit owner interval nests in its caller interval, X keymap observations show down then up and a neutral terminal, cancellation cleanup is verified, authority flags stay false, and the owner/container exit cleanly. Source/image/lease/preflight gaps are STOP; changed authority or release behavior is FAIL.
- **C:** `XSync` completion brackets server processing, not application delivery or task consumption. One Xvfb fixture cannot estimate a population distribution.
- **U:** No MAP01 occupancy, useful task effect, recovery efficacy, safety rate, production reliability, human tempo, or cross-domain performance conclusion follows.

## Source identity

At current-main freeze, these runtime dependency blobs were equal to the retained #5156 source family:

| Path | Git blob |
|---|---|
| `research/live_control/input_owner_v10.py` | `341b3c01649943ddaad5f28431a792c4889cc36e` |
| `research/live_control/input_transition_owner_v3.py` | `0ea631abcf6272f0538a9ef9198ad8069b47b464` |
| `research/live_control/executor_v3.py` | `2b072454fd81c41bf9e025217afc78020c7059de` |
| `research/live_control/lease.py` | `b9dac6bb4063928354733d79bf371909a288a3d1` |
| Allocation 04's pinned owner-thread `dependencies/input_owner_v11.py` (retained on main) | `c40db07e596b31557590cec5e90f6ab651573476` |

The latest #5156 update reports that Allocation 04's input cases ran, then the runner failed while serializing release rows (`dict(event="joined_release", **row)`, duplicate `event`). That raw result is immutable. Allocation 05 calls the merged #5594 `join_explicit_release` helper (source blob `097125fc1aad8b931e3a3fbe99ee9009add247d4`) and requires its `owner_event` provenance field in the formal raw auditor; it does not maintain a parallel serializer implementation. Base runtime blobs remain equal to latest main. The selected owner-thread v11 dependency blob `c40db07e596b31557590cec5e90f6ab651573476` is retained at `research/live_control/owner_keyup_formal_x11_5156_20260930_04/dependencies/input_owner_v11.py`; it is distinct from the current root `research/live_control/input_owner_v11.py` caller-bracket wrapper (blob `842071284156d3ccc647f47135ee62a9e512cb56`). The corrected runner/auditor/expected inventory are copied into this new path. The earlier pre-Xlib STOP also remains unchanged as a distinct retained record.

The retained #1276 v12 physical-edge source SHA-256 is `b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508`; its independently audited live composition is a related predecessor, not code imported by this fixture. Allocation 05 specifically exercises the already integrated v11 owner-thread KeyRelease/XSync bracket over v10 and transition-owner v3. It does **not** measure true physical hold duration, useful task feedback, bounded recovery, human tempo, or MAP01 performance. It is one prerequisite for the broader r133 measurement direction, not its completion.

## Corrected invocation contract

`launch_contract.py` builds argv only and never invokes Docker. Read-only Docker Desktop inventory/history identified `agent-interface-issue4712-onset:20260927@sha256:f41b02e63fc3964f9bb831167ae42bce6d6ffa50fbda122d22deaa39736637bb` as a cached `linux/amd64` image whose recorded layers install Xvfb, xauth, and python-xlib. Its original ENTRYPOINT starts Xvfb/openbox; the candidate command explicitly replaces that with `/bin/sh` and runs `xvfb-run` itself. This image is a request candidate, not yet coordinator-approved. The argv builder requires a digest-pinned image, `linux/amd64`, the exact dedicated allocation source and existing `results/formal-01` output directory, `--pull=never`, `--network none`, one CPU, 512 MiB, 64 pids, read-only source/root with a separate writable results mount, dropped capabilities, no-new-privileges, and explicit entrypoint override. The raw-only auditor has a separate isolated invocation, and the caller must gate it on runner exit 0.

The intended container-side sequence is an Xlib import and `xvfb-run` presence check before the fixture runner. The Allocation 04 STOP showed why the explicit entrypoint override is required: the image's default `python3` entrypoint interpreted `sh` as a Python script. Missing digest/platform, image, Xlib, Xvfb, or a failed preflight means STOP before runner/input; no retry or fallback image.

The named owner had a 15-minute Docker Desktop `desktop-linux` allocation proposal for **2026-09-30 17:40–17:55 UTC**. This was ten minutes after #5550 successor's then-visible 17:15–17:30 UTC request and did not overlap #5413's requested 2026-10-01 window; #5081 remains queued behind #5156. The #5156 coordination head-up explicitly identified main drift before this window. As assigned, this therefore STOPped and is consumed. It did not inherit Allocation 05, and no new slot is implied.

**Outcome:** before the proposed window, #5156 reported that main had advanced to `2fdeca6badf9a3e4803272a88a4ff62f98f19ef3`; the #06 freeze remains `9fc98feb617c26fe1baa7ecc4decd43b69df8601`. Accordingly #06 is consumed as `STOP_MAIN_DRIFT_BEFORE_RUNNER`. No Docker command/container, Xlib/Xvfb, fixture, input, or auditor was invoked. Retain the STOP record in `results/formal-01/STOP.json`; no retry. A distinct successor requires a fresh main freeze and a fresh, non-conflicting exact assignment.

## Construction evidence (not an X11 experiment)

- Allocation 05's TDD red phases reproduced the missing builder, rejection of full digest-pinned OCI references, stale main SHA, duplicate-`event` TypeError, duplicate admission/terminal overwrite, missing owner-event provenance, and nonexistent bind-mount source acceptance. Allocation 06 reran its copied suite plus host one-shot/window-guard tests: 30/30 pass. This is construction evidence only.
- Checks cover entrypoint argv placement, Xlib-before-Xvfb/runner order, no-pull/network-disabled bounded invocation, exact image digest/platform pin, current-main freeze parity, actual source/results path existence, refusal to mount outside the dedicated allocation directory, provenance preservation and rejection of duplicated admission/terminal identities.
- Host `py_compile` passes for the helper and runner/auditor.
- No Docker CLI, container, Xvfb, Xlib import in a container, X11 input, model, GUI, or game was invoked for Allocation 06 preparation. Allocation 05 stopped before these operations.

## Preserved predecessor disposition

Allocation 04 (`MAP01-OWNER-KEYUP-BRACKET-5156-20260930-04`) remains consumed and unchanged. Two distinct records are retained: the `formal-02/STOP.json` setup STOP before Xlib/Xvfb/input because the supplied command did not override `ENTRYPOINT ["python3"]`; and the later `allocation-04-fail/` outcome in which X11 input cases ran but joined-release serialization raised the duplicate-`event` TypeError, leaving no formal audit. Keep both records; do not retry or relabel Allocation 04. Allocation 05 is a new request with a repaired runner and requires a fresh exact assignment.
