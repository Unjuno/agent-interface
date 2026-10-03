# One pre-input recovery with semantic role retention

This standard-library prototype moves the qualified #57 role controller into a
normal Python package. It replaces experiment-path module loading with relative
imports. The line-parameter guard uses the document parser's `splitlines`
grammar. The recovery entry owns a shallow copy of the original request and
passes a separate shallow copy to each subject callback. The pipeline owns an
exact builtin response dictionary before validation and journaling. Other function/class
bodies retain the qualified version. Source line endings become LF.
It does not automatically start a browser, model, native input, or experiment.

```python
from finite_role_recovery import run_with_one_recovery
label = run_with_one_recovery(task, editor, subject, record)
```

The caller supplies a task with `id`, `document`, `old_person`, and `new_person`.
The subject returns exactly five strings: `updated_text`, `changed_role`,
`previous_person`, `new_person`, and `untouched_title`. The preserved prototype
contract requires `untouched_title == "sibling.txt"` and CRLF documents. It only
changes one unique complete role/person line and preserves all other text.
Syntactic validation does not establish that the subject selected the right
semantic role. An independent effect oracle must check the task result.

Request copies prevent synchronous callbacks from rewriting the original
validation parameters for the intended builtin dictionary of string values.
A callback output contradicting those owned parameters refuses before input.
This is not an atomic snapshot of concurrent writers or a deep copy of nested
mutable/custom objects. It does not make the subject a semantic oracle.

The editor provides `read_current()`, `replace_once(text)`, `save_once()`, and
monotonic `replacements` / `saves` attempt counters. Reads must establish the
selected target and complete current body. Inputs must increment their counter
before dispatch, including when their outcome becomes unknown. Wrong targets
and unknown native outcomes must raise. The backend owns fresh references,
input authorization/release, finite observation limits, containment, and Save
semantics; the package does not implement or certify those backend obligations.

The controller reobserves after inference and before input. It admits at most
one recovery on a typed stale-document failure before any input, with a
validated subject answer. Reuse recomputes the edit against the complete fresh
body. A changed/missing role invalidates retention before another subject call.
A second stale body, wrong target, or unknown input/Save outcome stops without
resending the action. Set `reuse_label=False` for the one-fresh-inference replan
baseline. A returned label or Save call is not independent on-disk success.
There is no atomicity guarantee against outside writers.

Run the twenty-six public-state regressions from repository root:

```text
python -I research/live_control/test_finite_role_recovery.py -v
python -I -O research/live_control/test_finite_role_recovery.py -v
```

The checks use inline synthetic editor state: exact effects, annotation
preservation, second-change stop, wrong target, unknown observation,
role invalidation, unknown replacement, unknown Save, collateral rejection, and
the simple replan baseline. They send no native input and call no model. Their
assertions use unittest and remain active under optimized Python.
Initial target/body mismatch also refuses before a subject call. Typed stale
errors after replacement or Save cannot authorize recovery after input.
The line-parameter checks refuse CR/LF and all eight additional Python line
boundaries in every parameter, including at the start/end. Unicode, spaces,
and tabs retain exact forward/reverse behavior. Malformed new-person values
must stop the controller before replacement or Save.

Before repository delivery, a copied package ran in a new dedicated stock
JupyterLab environment: three exact saved effects; a fourth case changed again
during recovery and stopped with zero controller edits/Saves. A separate
saved-data reader checked file bytes, raw native receipts, event order, source
identity, and empty dedicated Job without forced termination. The run used
134 native launches, three Saves, four controlled fixture edits, five
deterministic subject calls, and zero actual model calls. Native/private raw
remains in the author's local retained evidence; this PR is not a complete
public native evidence capsule or an independent reproduction of that run.

The prior consumed actual-model comparison is separately recorded at
[the #57 result](https://github.com/Unjuno/agent-interface/issues/57#issuecomment-5973271804).
This package does not replay it or claim a new resource advantage. Its limited
observation does not prove physical desktop control, provider costs, natural
fault rates, or arbitrary-writer concurrency. Adoption in a shared caller
requires concrete backend composition and current-tree nonauthor review.

Six request-custody regressions cover entry/argument aliases, first and recovered
inference, explicit external-alias output, and a positive exact-effect control.
The original eighteen regressions and their definitions are preserved. Ordinary
synthetic comparison found entry-only and callback-only copies insufficient;
both copies either preserve the requested exact effect or stop before input.
This is no new model/native/performance qualification.

Two response-custody regressions preserve the validated returned role when a
journal callback mutates the original response and retain refusal for dict
subclasses. Response copying applies only to exact builtin dictionaries; the
existing exact-string/schema checks remain unchanged. No concurrent response
snapshot or new native/model qualification is claimed.
