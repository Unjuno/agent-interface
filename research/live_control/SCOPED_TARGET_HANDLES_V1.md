# Scoped target handles v1

Issue45 proposes runtime-owned target references that survive safe layout changes
without silently becoming cached coordinates. The pure v1 registry keeps the RGB
region private and scopes it to a session, focus, surface, source geometry,
coordinate frame, observation sequence and expiry. Only exact `VALID` or
`REVALIDATED` results are eligible for later ordinary admission. `AMBIGUOUS`,
`MOVED`, `MISSING`, `STALE` and `SCOPE_MISMATCH` fail closed.

Ten deterministic controls pass on Windows and WSL. They cover stable use,
window translation, permitted and refused local translation, ambiguity, missing
pixels, expiry, changed session/surface and unknown handles. Resolution grants no
input authority.

The first retained OpenTTD archive replay failed. It selected a visually flat
16x16 region that matched both translated and untranslated positions. This shows
that exact equality is insufficient when the source region carries too little
information. The result remains in
`results/scoped-target-handle-archive-01/failure.json`; v2 refuses a source patch
whose maximum channel standard deviation is below8.

The first preregistered same-session live run then minted a textured OpenTTD
toolbar handle, moved the surface, acquired a fresh observation and clicked using
only the runtime handle plus `[8,8]` offset. The window manager turned the
requested move `[16,0]` into observed client-geometry translation `[17,20]`.
The runtime matched the region exactly at `[829,63,16,16]`, returned
`REVALIDATED`, derived point `[837,71]`, and passed that point through the normal
owner. The program completed in280.790ms from submit to reply and release was
verified. Four exact frames audit cross-OS; the tooltip area changed by3383
pixels.

The preregistered primary endpoint expected the requested delta and point
`[836,51]`, so the study is a retained failure and the candidate is not promoted.
The independent road-task score is also false as planned because only the toolbar
opener was targeted; the changed tooltip is not a semantic completion oracle.
This result does establish that the observed binding, rather than the requested
window-manager move, must define a safe handle transformation.

Next use a different desktop task with an independent semantic effect. Its
endpoint should derive the point from the observed binding delta without fixing
the window manager's realized displacement in advance. Add a changed-target
negative in the same allocation and do not weaken the exact matcher.

That matched follow-up now passes on a fresh private Chromium form. Both cases
use seed991005, enter `t991005`, mint the same textured Save-button region and
move the client from `[10,10,1050,780]` to `[30,18,1050,780]`. The caller then
supplies only the runtime handle and `[20,9]` point relation.

In the positive case, exact revalidation returns `REVALIDATED`, derives
`[290,251]`, and ordinary owner admission submits exactly
`value=t991005`. The independent HTTP/file oracle succeeds. Button-down ack to
the first useful changed-frame capture is60.016ms; ack to independent semantic
completion is192.643ms; click operation submit-to-return is324.506ms. The whole
episode uses12 durable calls and15 exact frames.

In the negative case, the same Chromium surface navigates to `about:blank` after
minting. Revalidation returns `MISSING`; the handle action has zero pointer
admissions, returns `needs_decision`, creates no submitted file and independently
scores false. Its click operation submit-to-return is201.229ms. The episode uses
14 durable calls and21 exact frames. All36 frames and both source sets audit on
Windows and WSL.

Decision: retain v2 for a matched cross-domain replication, not as the default.
The result proves one exact textured desktop target across window translation
and one missing-target refusal. It does not prove semantic identity under
restyling, scrolling, duplicate widgets or internal object movement. The agent
still authors the mint box and frame, and this no-model study measures no planner
boundary or token reduction. Next compare repeated model grounding against a
handle condition on a different desktop task with fixed model/task/order and an
independent oracle.

Issue45 proposes runtime-owned target references that survive safe layout changes
without silently turning into cached coordinates. The first pure candidate stores
an exact RGB region privately with its session scope, focus, surface, source
geometry, coordinate frame, observation sequence, expiry and explicitly allowed
transformations. The agent receives a handle and digest, not the retained pixels.

At each use, `resolve_point` requires a current RGB observation and binding. It
predicts the region through the handle's stored frame, checks the exact pixels,
and optionally performs a bounded local search. It returns one of `VALID`,
`REVALIDATED`, `AMBIGUOUS`, `MOVED`, `MISSING`, `STALE` or `SCOPE_MISMATCH`.
Only `VALID` and `REVALIDATED` return an eligible point. That point still grants
no authority and must pass ordinary focus, surface, geometry, lease and pointer
admission checks.

The deterministic probe covers ten cases on Windows and WSL: unchanged region,
window translation, permitted and forbidden local translation, duplicate exact
matches, missing pixels, expiry, session mismatch, surface mismatch and unknown
handle. All expected statuses pass. Caller-supplied numeric coordinates are
replaced by a point relation within the handle region after minting.

One archived OpenTTD replay uses retained initial frames at1024x720 and1152x720.
A16x16 centered-toolbar region bound as `window_content` revalidates at the
recorded `[-64,0]` geometry translation and resolves its center from `[632,14]`
to `[568,14]`. Binding the same source region as `screen_chrome` is a negative
control and returns `MISSING`. The replay normalizes clocks and sequences across
separate processes, so it establishes pixel/geometry feasibility only. It is not
a valid cross-session handle or a live-input result.

Decision: retain the strict pure contract as a candidate. Do not integrate it
into the default interface yet. The next experiment must mint inside one live
runtime, move or resize the same surface, acquire a fresh observation, resolve
the opaque handle and submit one independently scored action. A same-binding
pixel mutation must refuse with zero pointer admissions. Measure mint,
revalidation, first-input feedback, wrong-target actions and any planner boundary
saved. Exact RGB matching will likely be too brittle for animated regions; do
not relax it without a preregistered negative set.
