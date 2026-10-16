# #5156 Allocation 07 — owner-thread KeyRelease/XSync X11 fixture

Status: **source preparation only; no container/X11 invocation and no scientific result**.

- Allocation: `MAP01-OWNER-KEYUP-BRACKET-5156-ORB-20261001-07`
- Proposed owner: Unjuno / this Codex task
- Proposed engine/window: local OrbStack, 2026-10-01 02:00–02:15 UTC
- Proposed source freeze: main `72f2acdbdd5da3c490873e5efda213f3a55ff210`
- Additive path: `research/live_control/owner_keyup_formal_x11_5156_20261001_07/`
- New branch: `research/5156-owner-keyup-x11-a07-20261001`
- Prior #5156 A03/A05/A06 and completion-sentinel A03/A04 STOP records remain unchanged; none is reused as authority or scientific evidence.

## H / T / D / C / U

- **H:** For explicit per-key client key-up, an owner-thread `KeyRelease` request-to-`XSync` interval is identity-bound and nested within its caller bracket, without changing admission, cancellation, or release behavior.
- **T:** Following a fresh exact OrbStack grant and clean start gate, run one disposable Xvfb fixture with (1) one key down/up, (2) two keys down/down then sequential up/up with no intervening keymap query, and (3) cancellation after one admitted key with second admission rejected. Verify keymap-down before releases, keymap-up after, neutral terminal state, and owner shutdown. If and only if candidate exits 0, run the pinned raw-only auditor once in a separate bounded container.
- **D:** `PASS_OWNER_THREAD_KEYUP_BRACKET_SCOPED` only if the exact expected admissions/releases and order reconcile, identities match, each explicit interval satisfies `caller_start <= request_start <= request_return <= XSync_return <= caller_return`, autonomous cleanup has no fabricated caller receipt, XQueryKeymap confirms down/up and neutral terminal state, cancel cleanup is verified, authority/physical-key claims remain false, owner/container exit cleanly, and the independent audit has zero errors. Changed release/authority behavior is FAIL. Queue/source/image/preflight/integrity failures are STOP, not scientific failure. One candidate invocation, no retry; one conditional separate audit.
- **C:** XSync completion brackets server processing, not application delivery/consumption or the exact physical release instant. One Xvfb server and a handful of scripted cases cannot characterize scheduling distributions. No user desktop input, game, model, GPU, or network.
- **U:** No MAP01 occupancy, useful task effect, recovery efficacy, safety rate, production reliability, human tempo, latency distribution, or cross-domain performance conclusion.

## Pinned implementation and runtime

The candidate is the additive Allocation 05 Xvfb runner/auditor/expected inventory, copied byte-for-byte before this plan's allocation-specific edits. It includes the merged `join_explicit_release` helper; predecessor raw data and STOP records are not copied or edited. Expected inventory is three cases: single explicit up, two sequential explicit ups, and partial cancel/autonomous cleanup. The initial freeze at `40885011a5d8e15ab10bb6cc0e8eef65661718ee` was refreshed before container invocation to `72f2acdbdd5da3c490873e5efda213f3a55ff210` after a README-only main commit; that intervening commit changed no runtime source or dependency blobs. This allocation-specific re-freeze is recorded append-only on #5156 and #5085 before any candidate run.

At the proposed freeze, these current-main Git blobs are required and locally parity-checked against the candidate's vendored copies:

| Main source | Git blob |
|---|---|
| `research/live_control/input_owner_v10.py` | `341b3c01649943ddaad5f28431a792c4889cc36e` |
| `research/live_control/input_transition_owner_v3.py` | `0ea631abcf6272f0538a9ef9198ad8069b47b464` |
| `research/live_control/executor_v3.py` | `2b072454fd81c41bf9e025217afc78020c7059de` |
| `research/live_control/lease.py` | `b9dac6bb4063928354733d79bf371909a288a3d1` |
| Allocation 05 retained owner-thread `dependencies/input_owner_v11.py` | `c40db07e596b31557590cec5e90f6ab651573476` |
| Allocation 05 merged helper `dependencies/serialize_release.py` | `097125fc1aad8b931e3a3fbe99ee9009add247d4` |

Container candidate: `agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, `linux/arm64`, known from prior OrbStack read-only inspection. This is only a proposed pin: the start gate must confirm exact local digest/platform and preflight Xlib plus `xvfb-run`; no pull, build, or fallback image. Launch uses `--pull=never`, `--network none`, 1 CPU, 512 MiB, 64 PIDs, read-only source/root, a dedicated results mount, dropped capabilities, no-new-privileges, explicit `/bin/sh` entrypoint, and Xlib/Xvfb preflight before input. Candidate/auditor argv builders only construct commands; they do not execute them.

## Start gate / queue contract

The 02:00–02:15 UTC proposal is a fresh exact request, 75 minutes before the currently visible #5521 request 03:20–03:35; it inherits neither that nor any withdrawn slot. Before any Docker command at start, refresh #5085, #5156, relevant peer Issues/tasks and branches/PRs; require explicit terminal/release evidence for preceding lanes and a fresh exact named grant for this allocation. Read-only inventory must show no running unrelated container and no nonterminal `Created` container with unknown ownership. Attribute ownership only from explicit queue/task/Issue evidence; do not inspect, stop, remove, or alter unrelated containers; leave Exited containers untouched. Revalidate exact current main, vendored source identity, image digest/platform, OrbStack health, and source/harness hashes. The dedicated `results/formal-01/` directory must contain only its tracked `.gitkeep` marker before candidate; see `OUTPUTS.md`. Any ambiguity, conflict, drift, or failed preflight means a retained STOP before candidate=0/auditor=0. No window or earlier STOP is reusable.

## Construction checks versus formal evidence

Host command `python3 -B -m unittest -v test_launch_contract.py test_serialize_release.py test_audit_formal_x11.py`: **23/23 passed** after adding strict completion-sentinel/row-count controls. `python3 -B -m py_compile launch_contract.py run_formal_x11.py audit_formal_x11.py` and repository `git diff --check` also passed. These checks validate only the launch contract, serializer, expected inventory, and mutation rejection. They do not call the Xvfb candidate and do not count as an experiment. Formal evidence exists only if the exact candidate and separate auditor run under the granted container slot and their outputs, exit codes, hashes, and limits are preserved. Report FAIL only for a valid execution contradicting H/D; report STOP for provenance/resource/setup failures.
