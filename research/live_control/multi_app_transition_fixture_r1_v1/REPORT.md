# Mixed-app finite transition fixture — R1 retained result

Issue #1705. Successor to retained integration-gap audit #1690.

## Decision

**PASS_MULTI_APP_TRANSITION_FIXTURE_SCOPED**

One exact-frozen formal invocation ran four fresh private-X11 sessions. All four sessions exposed the same five required mechanics:

1. Chromium geometry change from 1280x800 to 900x650 after explicit maximize-state removal;
2. actual cross-application input focus change from Chromium to XTerm;
3. a second Chromium profile/window launched while the old window remained live, with distinct X11 IDs, followed by verified disappearance of the old window;
4. a Chromium built-in Clear browsing data modal transition whose root-framebuffer SHA-256 differed before/after;
5. terminal keyboard/pointer neutral state after Escape.

Formal result: 4/4 sessions passed every gate. Audit PASS/errors[]; corruption controls7/7. Formal1/reruns0/replacements0/tuning0.

## Integrity

Before formal, all seven frozen GitHub files were read back and matched local `git hash-object` exactly. Source identities are retained in `SOURCE_FREEZE.json`.

The excluded construction history is intentionally retained. It includes setup failures for private Xauthority, X resource-ID reuse when replacement ordering was wrong, unavailable LibreOffice/Inkscape window candidates in this container, maximized-window geometry suppression, and an unreliable local-JavaScript alert discriminator. These were fixture-development stops before source freeze and are not pooled with formal evidence.

The construction command also emitted Python-Xlib xauth warnings on stdout before JSON. The scientific construction object was normalized losslessly from the JSON payload and source bytes were unchanged.

## What this establishes

The previously missing *fixture mechanics* are reproducibly available in one finite multi-app session. A later Agent Interface controller experiment can therefore test integrated stale-state/refusal/recovery behavior against a fixed perturbation schedule rather than separately assuming each perturbation can be produced.

## What this does not establish

This is not an integrated controller PASS. The fixture itself injects/observes transitions and does not score an Agent Interface task. It does not show:
- correct task continuation/recovery;
- wrong-target prevention by the shared caller;
- useful latency or fewer planner/model boundaries;
- human-like tempo;
- cross-backend behavior;
- production readiness.

The ROADMAP item "Run longer multi-app sessions with focus drift, window replacement, modal transitions, and geometry changes" remains open until a real controller/task run uses such a schedule with independent correctness and release accounting.

## Next rung

Reuse this exact finite schedule with an Agent Interface caller/controller. Require:
- a task/effect oracle independent of controller state;
- no wrong-target input after each perturbation;
- explicit refusal or bounded recovery where stale;
- verified release at each interruption and terminal;
- one controller/session lineage across Chromium and XTerm;
- retained failures and transition timestamps.

Do not widen to an unbounded endurance run before this finite integrated controller gate closes.
