# Issue #2107 — held-out GTK release-telemetry decision block

Allocation: `issue2107-gtk-release-decision-formal-01-20260927`

This is a new, held-out GTK3/Xvfb route. It does not alter or pool the earlier
Tk/#869 observation, policy-stub allocations, or the #2107 focus/keymap rebase.
The research question is deliberately narrower than “does v11 emit a valid
receipt?”: does the interval receipt change a safe task decision when the
ordinary synchronous release-call return and a fresh application observation
are already available?

## H / T / D / C / U

**H — Hypothesis.** A valid, identity-bound v11 release interval can improve a
frozen decision-path metric over the same v10 input owner’s ordinary successful
release-call return on a held-out GTK task route, without treating release as
proof of task effect. A plausible alternative is `HOLD_NO_DECISION_VALUE`: the
call-return boundary and independently observed GTK effect already suffice,
making the extra receipt observationally redundant and strictly additional
instrumentation cost.

**T — Treatment and allocation.** Use the exact existing `InputOwner` v10 and
telemetry wrapper v11 source files on a private TCP-disabled Xvfb display started
with autorepeat disabled (`Xvfb -r`). Verify the global X-server autorepeat
setting again after the GTK process starts, before any input. Use an isolated
GTK3 app whose 400×180 image changes from a red PENDING GdkPixbuf to a green
DONE GdkPixbuf on task effect. The application event/effect log records its
internal transition, while XWD pixel capture independently gates visible DONE
before release and is the policy input. Send real XTEST F8
press/release events through the input owner. The decision procedure receives
only (a) ordinary release-call completion, (b) optional normalized release
receipt status, and (c) a fresh XWD-derived visible state plus fresh X-server
F8 keymap state. The GTK event/effect log is an independent scoring oracle and
is never an input to the decision procedure.

Conditions: `NO_RELEASE_RECEIPT` (v10), `VALID_RELEASE_RECEIPT` (v11, exact
owner/intent binding), `AMBIGUOUS_RECEIPT` (v11 receipt copied with mismatched
intent binding and normalized to UNKNOWN), and `CONTRADICTORY_EFFECT` (valid
v11 release with a GTK app that consumes the key but intentionally has no task
effect). For each of eight repetitions, run each receipt condition against
effect-before-release and delayed effect-after-release; also run one
no-effect/valid-release contradiction. This is 56 fresh app/Xvfb sessions in a
single formal runner invocation. The order of the three receipt conditions
rotates by repetition; the two effect schedules alternate order. Each
repetition's delay (120, 180, 240, 120, 180, 240, 120, 180 ms) is matched
across all receipt conditions. The `before` task effect is scheduled that many
milliseconds after F8 press; the `after` task effect is scheduled that many
milliseconds after F8 release. Thus each v10/v11 pair receives the same
input-relative effect delay instead of making one arm intrinsically faster by
changing the event on which the fixture effect occurs. There are no
model/provider calls and no user data.

**D — Decision gates.** The same deterministic policy code chooses among
`CONTINUE`, `WAIT`, `QUERY`, `RETRY`, and `ABORT` using only its declared
decision inputs. `CONTINUE` requires a fresh visible DONE state and a fresh
X-server F8-up sample; neither a receipt nor release-call success alone may
continue. The visual capture must finish before its XQueryKeymap sample; capture
start to keymap sample is bounded at 250 ms, and keymap sample to policy
availability at 100 ms, and policy availability to next consumption is bounded
at 100 ms. A WAIT interval must be at least its requested policy duration and
no more than 50 ms scheduler slack above it; the next controller decision must
follow the completed wait within 100 ms. An ambiguous receipt
is surfaced as UNKNOWN. A valid receipt with a PENDING screen must not continue.
The no-effect control may make at most one
retry, only after a fresh F8-up sample, then must ABORT if no independent DONE
effect appears. No stale F8-down terminal sample is permitted.

- `PASS_SCOPED_DECISION_VALUE` requires zero false continuations, every
  effect-present case to reach CONTINUE, every no-effect case to ABORT, zero
  stale terminal F8-down samples, and a preregistered ≥20% reduction in paired
  median caller-return-to-correct-decision latency or in policy WAIT/QUERY/
  RETRY actions for VALID versus NO receipt, without worse effect-after-release
  completion. Report all pairs and a paired bootstrap 95% interval; the small
  fixed block is not a general population estimate.
- `HOLD_NO_DECISION_VALUE` applies when correctness gates pass but neither
  decision metric improves by the threshold. Receipt RPC/instrumentation cost
  is still reported; this does not establish utility or justify promotion.
- Any false continuation, retry while F8 is down, or invalid receipt treated as
  authority is `FAIL_SAFETY_GATE`.
- Missing/contradictory provenance, fixture, image, cleanup, or independent
  audit evidence is `STOP`; construction runs are never formal rows.

**C — Controls and constraints.** Use the locally cached, immutable
`sha256:eb3ce9f5bd0cf358664b9d1ff9bce4cf2ce9f82f72ec700222046fb8fe8b96ba`
`linux/amd64` GTK/X11 image. Run with `--pull=never --network none --read-only`,
read-only source, `/tmp` tmpfs, and only the fresh evidence directory writable.
Pin the exact current-main base, source hashes, image ID and package versions in
`FREEZE.json` before formal execution. Base is latest `main` snapshot `92596bfb750be63c03d3d2906a05d5a5933651c2`. Run one construction allocation before freeze; then freeze/commit locally and run formal exactly once. A separate
container invocation performs the raw-only audit. Preserve all failures and
STOPs; never retry the formal allocation.

**U — Uncertainty.** One deterministic policy, one GTK fixture, one local Linux
X server/image, synthetic tasks, and eight repeats do not establish frontier
model behavior, model/token savings, general application semantics, physical
HID state, broad GUI reliability, or product/runtime readiness. X-server
Keymap state is not hardware telemetry. A scoped HOLD is a valid outcome and
does not close Issue #2107.

## Frozen policy semantics

The policy is task-effect-first, not receipt-authorized. It queries immediately
after a successful release call, waits 50 ms between PENDING observations, and
continues only after DONE plus a fresh F8-up observation. At 500 ms with a
PENDING state and F8 up, it issues one idempotent F8 retry; after another 500 ms
without DONE it aborts. `NO_RELEASE_RECEIPT`, `VALID_RELEASE_RECEIPT`, and
`UNKNOWN` are all retained in the decision trace; the receipt is not a substitute
for either the visual effect or the fresh keymap sample. This intentionally
tests whether telemetry adds decision value over the real synchronous call
boundary instead of manufacturing a benefit by withholding ordinary return
information from the baseline.

The runner has a separate 3 s per-case infrastructure watchdog. It is not a
policy timeout or outcome gate; reaching it is a retained STOP. The policy's
frozen no-effect retry/abort boundaries remain 500/1,000 ms.
