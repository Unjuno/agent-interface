# V39 pending-planner handoff through a native synthetic child

The actual V39 controller, PersistentPlannerAdapter, real child JSONL/stdin pipes, measured V15 Backend, ExecutorV13 and X11 owner completed a bounded synthetic handoff. In the repaired pair, an unchanged health pixel allowed the delayed second answer; changing the pixel from90 to60 during a native `a` hold interrupted that pending turn, released the input, discarded its later `completed` answer and started the next turn from the matching red frame. **Scoped saved audit:128/128 PASS; copied-evidence corruption controls:8/8 rejected.** This establishes the exercised control path, not game perception, model quality or task benefit.

Source is #8261 head `4190104d0c72a025093c8569fdbd216b5929de0b`; main at freeze was `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. All67 selected files match author-side virtual merge tree `d85c4354d8fdff6065733f9fc60b4252af64737b`. Parent/child loaded19/39 matching source modules. No runtime source changed for this package. #59 claim: [6035251520](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6035251520). Existing root and bugbot only; coauthor spot-check is not a nonauthor vote or main merge approval.

## Results and retained first failure

| Construction | Result | Evidence |
|---|---|---|
| Original stable/drop pair | FAIL42/49. Stable exited0 but both active actions were rejected; drop exited1 on scripted planner timeout. Neither generated native key events. | `audit-v1.json`, `runs/`, original freeze/code |
| Repaired v2 stable | Two admitted/completed `d` actions, two `a` cover holds,8 native key events; zero policy invalidations. | `construction-v2/runs/stable/` |
| Repaired v2 drop | One `d` and one `a` DOWN/UP pair,4 native events; one pending-turn interruption, no `plan-1` submission, verified empty release before cancelled cover terminal, next source health60. | `construction-v2/runs/drop/` |
| v2 saved audit |128/128 pass; all43 typed/full epochs reconcile independently against saved RGB pixels. | `construction-v2/audit-v1.json` |
| Saved corruption controls |8/8 detected by substantive predicates: missing pending wait, leaked stale plan, unverified/late release, missing native UP, wrong typed value, stale next source and reordered pixel change. No native calls. | `construction-v2/negative-controls/` |

The first failure was a fixture interface error: the synthetic reader invented a format name, but `build_contract` requires `observable-signal-v1`. V2 changes that fixture field and retains `synthetic:true` plus a separate fixture-format label. Source67, native driver, controller harness, action/timing thresholds and semantic audit predicates are unchanged; the launcher/auditor paths identify the separate v2 directory. An actual `build_contract` preflight was added before v2. Each arm ran once per version; no native rerun was used to repair an auditor result.

The original drop cleanup helper reports `cleanup_complete:false` because the synthetic child lacks the production `score.json`/`owner-events.json` files. Preserve that aggregate result. Its saved input-terminal/release checks, child exit0 and separate child raw show physical/input-process cleanup; no application scoring was established.

For the v2 target, the observed invalidation-to-interrupt interval was0.052501ms, to cancelled terminal2.717076ms, and to next planner turn25.892996ms. These are same-guest monotonic intervals from one specimen, not timing guarantees, inference speed or an efficiency comparison. The native a press caused the programmed200ms pixel change; an independent keymap witness confirms a was down before that change. The next source is sequence12/capture5028471502407 and has the invalidation RGB hash. Production permits a later epoch with identical binding/RGB; the audit checks that actual non-older contract rather than inventing an exact-sequence requirement.

## Scope and resource evidence

The planner client is an in-process scripted transport; the actual PersistentPlannerAdapter still performs schema validation and cancellation eligibility. The child is an explicit synthetic replacement for `session_map01_v15`, using actual native measured Backend/Executor/owner operations. It does not exercise the production V15 session launcher, ViZDoom, scorer, app-server or model inference. Health is a known pixel; ammo30 is a synthetic constant. There is no game HUD/threat exposure, host-display input, task-success or useful-feedback/latency-saving claim.

Unmodified V39 `report.json` includes hardcoded fields `claim`, `game_continued_during_model_calls`, `fixture_contract`, `measurement_session` and `planner_contract` describing real MAP01, IWAD/engine/map validation, V15 scoring and an app-server. Those descriptions are **inapplicable to this fixture**; use outer `RESULT.json`, driver seams and raw synthetic `post_control_score` (`game:false`, `task_success:null`) for provenance. Terminal `exit_or_transition` is a scripted fixture stop, not observed game completion.

The owned isolated Debian12 arm64 VM ran Python3.11.2, Xlib0.33 and Pillow9.4.0 with private Xvfb. Effective limits were one CPU,1GiB memory, zero swap,64 tasks,60s per arm, private network/tmp, read-only source/harness and only owned run directories writable. No nonloopback interface was UP/addressed/routed, no host mounts or SSH-agent forwarding. Parent/child sources and both freezes were read back unchanged. Each Xvfb exited0, owners stopped, Executor inactive, watcher/thread lists empty; post-run inspection found no probe processes/units and VM stop was read back. An earlier stopped→running VM-state difference during preparation has an explicit retained reconciliation; its startup cause is unknown. No shared Docker state was changed.

## Saved-only reproduction and archive custody

Four passive files comprise this package: this README, `RESULT.json`, `MANIFEST.json` and `evidence.tar.xz`. The archive has387 members,4,246,248 uncompressed bytes,179,248 compressed bytes; SHA-256 `673a4022b1bcc5f5718e1cb90b42b6a7ed91f3b3c20634a67c94eee718ba7927`. Every member was read back byte-for-byte. The manifest lists original/published hashes. Only `host-disk-request.json` has a private host workspace path projected to a placeholder; original remains privately retained. Frozen files and raw are exact. Duplicate transport tar containers and generated bytecode are omitted; their extracted evidence is retained.

Extract into a fresh directory, enter it, then run with Python/Pillow:

```bash
python3 construction-v2/audit_saved.py construction-v2 --out /tmp/v39-audit-new.json
```

The output path must not exist. This saved audit never imports the producer or creates input. `construction-v2/corrupt_saved.py` defines the retained eight copied-evidence controls. Native launch scripts are historical frozen inputs inside the archive, not auto-discovered tests or permission for another live run. #8094's historical native FAIL, #8261's alias first-audit FAIL, the unassigned live #59 lane and the overall computer-control goal remain unchanged.
