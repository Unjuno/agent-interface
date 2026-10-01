# Explicit native window review across the Calc dialog

The existing bridge now exposes `review_window(window_id)` on its persistent
connection. The caller explicitly chooses the next focused window for read-only
review. The method invalidates its old handle store and in-memory mint sources,
increments binding revision, captures and verifies a new native image, and
returns that exact observation. It never focuses the requested window or grants
input authority. Window/focus/capture failure leaves mint/click disabled until
a later explicit review succeeds. Alias names cannot be reused across reviews,
preventing an old alias string from silently rebinding to a new target.

The Calc harness reuses the returned observation for the next assistant request;
it no longer closes/reopens a bridge and takes a separate stage-start image.
The assistant still views each new scene and explicitly chooses the action.
The previous feedback error from the destroyed dialog remains retained alongside
the successful parent-window review; it is not rewritten as a successful cue.

## Actual primary-assistant use

With seed 991084 and the already opt-in 2 ms text policy:

1. View source 1 and enter A1=116/A2=476, then Save.
2. Observe changed focus, explicitly review the dialog on the same connection.
   Scope rotates; binding revision goes 0→1. The returned source 7 is delivered
   unchanged for the assistant to select Use Excel 2007-365 Format.
3. After that input, the dialog no longer exists. Preserve the BadWindow cue
   error, review the focused sheet window, rotate scope and advance revision
   1→2. Source 13 is delivered unchanged for final visual review and finish.
4. Independent saved-workbook scoring and a second openpyxl read verify
   [116,476]. Both completed input programs verify empty key/button release.

The controlled `--probe-old-target` checks issued each previous alias after its
review. Both returned refused with zero input emissions. They add read-only
captures to this run; neither selected a new target or replayed prior input.
The two executed native programs carry source binding revisions 0 and 1; the
final observation has revision 2. There is one bridge constructor invocation
in the executed harness and one continuously used native backend connection.
Setup still owns its own X11 connection.

## Verification and scope

Fifteen focused tests pass, including old-source/alias invalidation, wrong focus,
focus changes, capture-delivery failure and subsequent fresh review, no mutation
during active input, plus the existing guard and feedback controls. The initial
pre-revision live result is separately retained in native-window-review-01.
This final version was rerun on a fresh private Calc fixture; it is not inferred
from the earlier version's success.

The 60-file manifest covers raw data, workbook and the three changed source
snapshots, excluding itself and this README. Fourteen PNG/hash links were
verified, including equality between each returned review and next-stage source.
Unchanged dependencies are pinned by base commit
`0381a575cf940f91e72564b5f3805cfa32a53749`. All tracked processes were terminal at
teardown (Xvfb 0, Openbox 1, LibreOffice launcher 255), not all successful exits.
No helper model was called; primary model tokens and cost remain unknown.

Local review operations took about 96 and 73 ms, including capture/verification.
These exclude primary-assistant wait, are not matched to the former path and do
not establish lower end-to-end latency. Read-only identity checks are not atomic
with future input; ordinary guards still recheck at execution. The research
harness chooses focused windows only within its private desktop. This does not
implement cross-application authorization or a public multi-client session API.
The retained alias-name set grows with the bridge lifetime; this bounded harness
is not a long-session resource claim.

Reproduce with the existing Linux/X11 Calc setup:

```
PYTHONPATH=. python3 research/live_control/run_native_calc_self_use_v1.py --out results-local/my-window-review --text-gap-ms 2 --probe-old-target
```

View the returned source before each explicit request; do not reuse coordinates
without checking the scene. Semantic task scoring remains separate from title
cues, program completion and window review.
