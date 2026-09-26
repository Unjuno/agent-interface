# #2311 first live rung: measured text-replacement fallback obligations

Allocation: `fallback-selection-2311-20260925-s8r2-01`.
Source/intake main: `4a1f3957e91b412a64769199f78f2c4b0102d28b`.
Proposed additive path: `research/integration/fallback_selection_s8r2_v1/**`.
Proposed branch: `research/fallback-selection-2311-20260925-s8r2`.
Local work only until a supported GitHub write route exists. This plan is a
conversation/local preregistration, NOT GitHub preregistration or a remote claim.
No other agent's branch, historical allocation, source or decision is modified.

## Motivation and lineage

Closed #1919 proved a synthetic snapshot/fallback selector while assuming that
an edge preserves its obligation. Open #2311 asks for actual fallback semantics.
Here the obligation is exactly replacing the entire intended editable widget's
contents with one supplied digit, while preserving a separate protected field.
Selecting a route named replacement or completing native input is not that effect.

#2245's prior 15/21 allocation remains HOLD_FORMAL_INCOMPLETE. It is not rerun,
filled in or pooled. Only its two uploaded reports are available in this runtime;
the old 61-member raw package is not reconstructed from prose. Its claimed remote
namespace returned 404 in this continuation. #2494 had already noted a Control-a
construction failure; this study does not claim discovery of that binding. Its
new intervention is measured selection coverage, one bounded document-extent
refinement, and exact effect validation across single- and multi-line widgets.

This is neither #4367's validation-callback lifecycle nor #4040's suffix recovery:
no validation callback is installed, and the requested operation is full replacement,
not continuation of a partially delivered prefix. No blocked publication is reused.

## H — falsifiable hypothesis

Under the recorded standard X11/Tk 8.6 bindings, Ctrl+A is not a generally valid
select-all recipe. Home then Shift+End may cover an Entry or a one-line Text but
only the active display line in a multi-line Text. A selection-aware caller can
retain the first native recipe, inspect its actual coverage, and perform at most
one Ctrl+Home / Ctrl+Shift+End refinement before deciding whether to type. It must
refuse a noneditable target before sending input and never report success without
exact final-value plus protected-state scoring.

This tests known API semantics and their measured composition. It is not a new
Tk theorem, a production bug allegation, or a security/exploitation experiment.

## T — source-first finite test

Six conditions: ENTRY_FILLED, ENTRY_EMPTY, ENTRY_PARTIAL, TEXT_LINE, TEXT_MULTI,
TEXT_DISABLED. Three independently initialized policies: CTRL_A, LINE_EXTENT,
VERIFIED_EXTENT. Two prospective repetitions per cell: 36 fresh private app/Xvfb
pairs. This is the minimum declared complete matrix, not a statistical sample-size
claim. Policy order is Latin-rotated by condition/repetition; SCHEDULE.json is exact.
The formal strings differ from construction, and the replacement is `7` instead
of construction's `8`. These are authored tests, not held-out real-app distributions.

CTRL_A: Control+a then text. LINE_EXTENT: Home, Shift+End, then text.
VERIFIED_EXTENT: current readonly app receipt -> refuse if not editable/focused;
otherwise Home, Shift+End -> current selection receipt -> either type or refine
once with Control+Home, Control+Shift+End -> current selection receipt -> type only
when full document coverage is established. No erase, Undo, automatic retry, focus
repair, new semantic target or external action is invented. Correct refusal is not
successful task completion. No direct semantic API replacement arm is claimed.

Each case is a bounded foreground supervisor invocation. Formal outputs have an
exclusive consumed marker; source/environment hashes are checked first. A case
has a 14-second supervisor limit plus at most 3 seconds for owned-group cleanup;
application barriers are bounded to 2 seconds, RPC reads to 4 seconds. Execute at
most three case invocations per 45-second container call, in schedule order. On
first nonzero/incomplete case, stop the allocation and retain all partials; never
advance, retry, replace, drop or tune it. Final output only after all 36 terminal
supervisor receipts. Bound values are engineering limits, not hard-real-time promises.

Only the dedicated Xvfb receives native XTEST input. TCP is disabled and a fresh
MIT-MAGIC-COOKIE protects each server. The authentication file is removed afterward
and its secret bytes are not archived. No host display, user files, installation,
model/provider or experimental network is used. Every process ends in this turn.

### Exact runtime surface and implementation assumptions

vendor/backend.py is the entire exact upstream file, Git blob
`9cae101a219348077668c8fc086acf8e13154afe`, reconstructed from MCP text and verified
before import. backend_loader.py removes exactly one unused core-manifest import
from the AST, leaving every executed method unchanged. It invokes the actual
constructor, execute/preflight/key/text/release methods. Manifest, full core
admission/leases, public CLI/MCP and production task-success reporting are NOT
exercised. No stub substitutes for an executed backend dependency.

The app uses unmodified standard Entry/Text class bindings. An appended bindtag
logs native key events after the normal classes; IPC offers readonly snapshots and
shutdown only. Initial fixture text, selection and editability are configured
before ready. No IPC helper inserts/deletes text after ready. A snapshot barrier
waits for the expected real key releases, so X-server request completion alone is
not treated as application processing completion. This is not a generic app fence.

The pure candidate runs as a separate isolated stdlib process on exact allowlisted
JSON, without DISPLAY or scenario labels/paths/oracle/future state. It receives
current actual content/selection/editability/recipient and expected identity/current
sequence floor. IDs are opaque UUID hex. It returns authority=false throughout;
only the explicit frozen experiment orchestrator performs the bounded fixture input.

The two widget classes are two application-like surfaces IN ONE TOOLKIT, not two
independent application domains. Tk observation is a cooperative app contract, not
semantic authentication. The current content is stable between each receipt and
input; there is no concurrent writer, IME, customized binding, hidden embedded
object or external clipboard dependency. Text's implicit terminal newline is
excluded from authored contents; selection endpoints are clamped to that content
extent while original Tk selection indices are retained. Entry's observed final
inverted zero-width selection after empty-input replacement is retained as raw
metadata, not supplied to the pre-input policy and not silently repaired.

### Retention

Retain exact request/response wires, candidate stdin/stdout/exit, app-native key
journal, all stages and backend release receipts, actual app/Xvfb/case exits,
independent X-server keymaps/button state, initial/final raw pixels, app-written
final value, fixed sources, construction and environment hashes. Clock brackets
are diagnostic CLOCK_MONOTONIC nanoseconds; no performance benchmark is inferred.
The separate raw-only auditor imports no backend, runner, candidate, Tk or Xlib.

## D — frozen decisions

PASS_SELECTION_OBLIGATION_SCOPED requires all 36 ordered first cases, source and
record identities, all actual exits/cleanup, no evidence errors, and >=12 effective
raw corruption controls with a passing unmodified baseline.

Expected exact final effect counts per 12-case arm:
- CTRL_A: 2 exact empty-entry positives, 8 wrong full values, 2 disabled no-effects.
- LINE_EXTENT: 8 exact, 2 wrong multi-line full values, 2 disabled no-effects.
- VERIFIED_EXTENT: 10 exact editable effects, 0 wrong full values, 2 disabled refusals
  with zero key events. Exactly two one-shot refinements, both TEXT_MULTI; no other
  recovery input. Protected field remains `keep-42` in every case and stage.

Native event totals are secondary bookkeeping (72 / 96 / 100), not task progress.
The knowingly deficient comparators remain FAIL_FULL_REPLACEMENT_OBLIGATION for
their wrong-value cells even if the boundary study passes. A missed expected cell
is a retained scientific FAIL/HOLD, not a reason to retune. Missing source, process,
raw or terminal evidence is HOLD/STOP. Component PASS does not close #2311, #2245,
#2789 or the global roadmap, and does not prove an optimal or production fallback.

## C — competing explanations

Current selection telemetry is an added cooperative observation capability and has
real cost. This is not an equal-information efficiency comparison or proof of fewer
model boundaries. An unavailable selection source must cause YIELD, not inferred
coverage. The unknown-source, wrong-focus/scope/generation, changed-content,
Boolean-as-integer, malformed-range and exhausted-refinement tests are separate
unit controls, not extra live cases. Cross-platform and custom bindings may behave
differently. Initial text is ordinary fixture preparation, not candidate progress.

## U — uncertainty and measurement discipline

Technical repeats cover the fixed matrix, not a natural error probability. Exact
strings, native event counts and predicate truth set the gates. CPU frequency/load
are uncontrolled; no timing speedup, latency percentile, model/token/cost benefit,
calibrated combined standard uncertainty u_c or coverage factor k is estimated.
u_c and k are NOT_APPLICABLE to the exact discrete acceptance gate; timing has
unquantified scheduler and observation delay and is explicitly non-benchmark data.
X-server logical key state is not physical HID telemetry. Implementation/process
independence is not independent human review.

## Conditional argument and variable table

| Symbol | Meaning (Japanese) | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| s | 入力前の編集対象の全文 | 1 | readonly receipt's authored content | finite ASCII, includes authored LF; no concurrent writer | string |
| r | 要求する置換文字列 | 1 | formal payload `7` | one allowed ASCII digit | string |
| n | 元の文字数 | 1 | len(s) | nonnegative integer | scalar integer |
| a | 選択開始位置 | 1 | first selected character offset | integer, 0 <= a <= n | scalar integer |
| b | 選択終了位置 | 1 | exclusive selected end | integer, a <= b <= n | scalar integer |
| c | 挿入カーソル位置 | 1 | insertion offset if no selection | integer, 0 <= c <= n | scalar integer |
| s' | 通常のキー処理後の全文 | 1 | app-observed result | same target and standard editable binding | string |
| u_c | 合成標準不確かさ | not assigned | not estimated here | exact discrete gate; not a timing estimate | unavailable scalar |
| k | 拡張係数 | 1 | not estimated here | no calibrated uncertainty model | unavailable scalar |

Under ordinary editable replacement semantics with a nonempty selection,
`s' = s[0:a] || r || s[b:n]`, where `||` denotes concatenation (not arithmetic).
If `a=0` and `b=n`, both retained substrings are empty, hence `s'=r`.
If no nonempty selection exists, ordinary input gives
`s' = s[0:c] || r || s[c:n]`; an empty source is the legitimate no-selection special
case. A partial selection retains outside content and does not generally imply
full replacement. Therefore the pre-input coverage test is necessary for this
chosen key recipe, and the independent exact final string is still required to
validate actual execution. Selection operations themselves must leave s unchanged;
otherwise the candidate yields. This proof is conditional, not an empirical claim
about arbitrary toolkits or concurrent editing.

Dimension check: a, b, c and n all use the same dimensionless character-offset
unit; no pixel coordinate or time value appears in this string relation. Diagnostic
nanosecond differences remain within a single monotonic clock and are not compared
to X11 millisecond event timestamps. No mixed-unit threshold is used.

ERROR CHECK: no selection is not equivalent to full selection on nonempty text;
line end is not document end; disabled no-effect is not completion; full selection
is not proof of effect, identity authenticity, future stability or action authority.

## Roadmap and stopping boundary

Intake/known-mechanism separation -> excluded 18-case construction -> exact local
source/gate freeze anchored in conversation -> 36 first-outcome cases -> raw-only
audit/negative controls -> full additive evidence and apply-tested patch -> GitHub
Issue/PR/main only if supported write and review gates are available. Do not create
a new scientific Issue for missing tools or publication mechanics. Local phase
completion is not global-roadmap completion.

## Primary sources

- Repository #1919 (closed analytical assumption) and #2311 (open live obligation).
- Exact backend source at the pinned main and Git blob above.
- Tcl/Tk 8.6 Text manual (default bindings):
  https://www.tcl-lang.org/man/tcl8.6.13/TkCmd/text.htm
- Tcl/Tk Entry default-binding documentation:
  https://www.tcl-lang.org/man/tcl8.0/TkCmd/entry.html
  (historical documentation only; installed 8.6 binding files and live query
  responses are retained to establish this actual environment).
- Tk bind manual:
  https://web.tcl.tk/man/tcl8.6/TkCmd/bind.htm
