# PR #9320 standard-caller supervisor Xvfb result

**Disposition: scoped end-to-end positive outcome; runtime receipt remains UNKNOWN.**
This is one GitHub Actions run of the public standard MCP caller against private
Xvfb. It is useful evidence for one blocked-owner schedule, not a reliability
estimate or product-wide release guarantee.

## Frozen source and environment

- PR: [#9320](https://github.com/Unjuno/agent-interface/pull/9320), head
  `86cea576dfedd5ec44804d67c9fa783308868c17`, merged as
  `f55c061d0f82b0dc85736d7bd7161acbda5ae0f8`.
- Workflow run: [39660663702](https://github.com/Unjuno/agent-interface/actions/runs/39660663702),
  job `prestarted-cancel-xvfb`; raw `GITHUB_SHA`
  `b09136e61c94facf9983c06c6e92a625a38ce36d` is the workflow merge ref.
- Ubuntu GitHub runner, CPython 3.12.15, Xvfb
  `2:21.1.22-1ubuntu1.3` (binary SHA-256
  `97623d8c3972051fa29db5a91f64439b418a1ebc63ce449193556fc33900048e`).
- Conditions and full result are embedded in
  [`prestarted-cancel-xvfb.json`](prestarted-cancel-xvfb.json). The PNG and
  Xvfb log were downloaded from the same named workflow artifact without
  modification.

## Outcome

The synthetic app committed exactly one `a` effect while its owner was blocked
inside `python-xlib Display.sync()`. The public cancellation call returned in
60.629 ms, retired the owner process (exit `-15`), and retained generation
`(session 2f89dc96b391411da0bf023cc8e274c8, PID 2488, resource base 6291456,
binding revision 0)`. The prestarted supervisor PID 2491 was observed at that
same XRes base, producing
`owner_client_disconnect.status=disconnected` with reason
`resource_base_reused_by_supervisor`. It issued one KeyRelease for keycode 38
and recorded its own X11 readback as verified. A separate parent X client read
all keys up; after the injected 8,000 ms delayed-keypress horizon (observed at
8,501.336 ms after cancellation start), the separate readback still showed all
keys up and no late `b` press. The independent synthetic task oracle passed
its exact-effect and horizon checks.

The public runtime result deliberately remained
`cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, and
`replay_allowed=false`, because `late_server_request_possible=true` remained
in the cancellation receipt despite the test's later independent horizon
observation. Thus this run demonstrates a bounded caller response, a
supervisor-owned resource-base reuse case, a release/readback transition, and a
separate finite-horizon task oracle through the standard caller. It does not
promote runtime release confirmation, authorize replay, prove recovery on a
fresh target, or establish reliability. Keep the distinction between the
test's independent task score and runtime `task_success`.

## Raw integrity

`SHA256SUMS` covers the three downloaded artifact files. Preserve this first
outcome as-is; a future variation must use a new run and packet.
