# X11 relevant-region coordinate-frame move boundary — #4439

Decision: **PASS_X11_REGION_FRAME_MOVE_BOUNDARY_SCOPED**.

This is a source-first, observation-only X11 fixture. It does not change shared runtime semantics and does not establish a product or integrated desktop PASS.

## H

For one fixed target-relative 120x80 region in the same live X11 window, converting that region to reusable root/screen coordinates creates a separate geometry-validity lifetime. Reusing the initial rectangle should become stale after a move. Refreshing root coordinates should repair a move that happened earlier, but a move after the refresh and before capture should reopen the check/use gap. Direct `window_client` capture from the same XID should remain target-relative across a pure move.

## T

Provided Linux x86_64 container, CPython 3.13.5, Tcl/Tk 8.6, Python-Xlib 0.15, authenticated TCP-disabled Xvfb. No Docker/OrbStack image attestation, model/provider, external experiment network, task input, user desktop or user data.

Policies: `PINNED_SCREEN`, `REFRESH_SCREEN`, `WINDOW_CLIENT`. Schedules: `STABLE`, `MOVE_BEFORE`, `MOVE_BETWEEN`. Three fresh repetitions per cell: 27 application/Xvfb sessions in three immutable nine-case batches. Initial geometry (20,20); moved geometry (220,160), fixed 120x80 content on a 400x300 display. Candidate capture precedes scoring-only current window/root captures. No formal retry, replacement, pooling or post-freeze tuning.

Exact source and gates were published/read back before formal case 0. Freeze SHA256: `70153430eeecbfbee6c7a631b2439a0e0aca97aea115398c9be696e0bd276ab2`.

## D

| Policy | Stable | Move before acquisition | Move between acquisition and capture |
|---|---:|---:|---:|
| PINNED_SCREEN | 3/3 match | 0/3 match | 0/3 match |
| REFRESH_SCREEN | 3/3 match | 3/3 match | 0/3 match |
| WINDOW_CLIENT | 3/3 match | 3/3 match | 3/3 match |

All nine mismatching root/screen cases have an explicit stale-coordinate witness: the candidate rectangle differs from final window geometry, while the target XID and target-relative pixels remain unchanged. All 27 scoring window captures equal the corresponding current root rectangle. The negative result is therefore stale coordinate evidence in this fixture, not target disappearance.

Raw-only audit: 27 cases, 979 checks, errors=[]; 12/12 well-formed evidence mutations rejected. All 27 application exits and 27 Xvfb exits are zero; all three outer batch exits are zero; owned X sockets are absent after cleanup. Candidate outputs retain `authority=false` and `task_success=null`.

## C

A cooperative override-redirect window, stable size/content, same XID, same display and quiescence after the declared move are required. The screen-space comparator is not defective as an API; it is deliberately using a coordinate value outside its demonstrated validity lifetime. `WINDOW_CLIENT` avoids only this geometry conversion for this support envelope.

Construction was excluded. An exploratory observer initially omitted XAUTHORITY. Auditor construction v0 crashed on a policy-relabel mutation; v1 rejected 11/12 because schedule-event order was not checked. Both were preserved before the final auditor was frozen. No formal case was consumed by those corrections.

## U

Not established: semantic XID authenticity, destroy/recreate identity, resize, occlusion/compositor/Wayland behavior, content changes, atomic capture, model-visible freshness, action admission, task correctness, latency/token benefit, natural move frequency, or production promotion. Same-author separate audit is not independent human review.

## Integration decision

When evidence is semantically window-relative and the backend supports `window_client`, avoid unnecessarily converting it into reusable screen coordinates. When screen coordinates are required, treat the geometry resolution as independently expiring evidence and retain the residual check/use interval. This constrains O3/relevant-region composition; it does not complete O3, #57, #2789 or the repository ROADMAP.
