# Compiled GUI interface v1: deterministic local continuation boundary

Issue #56 asks whether one grounded GUI interaction can produce a bounded,
revalidatable interface that avoids a frontier-model generation between every
observation and action. `compiled_gui_interface_v1.py` implements the first
deterministic mechanics boundary. It does not replace the existing input owner,
Executor, target handles, receipt revalidation or effect scorer.

## Interface and authority

The strict v1 document contains a session/surface scope, declared predicates,
target-reference symbols, operations, explicit expected-effect conditions and
a bounded method state graph. A symbol stores only a target reference, identity
predicate and dependencies. Coordinates, steps and input authority are rejected.

On every transition the runtime:

1. obtains a fresh, monotonically sequenced observation;
2. verifies the prior action's explicit expected predicate values;
3. requires exactly one branch to match;
4. asks the admission adapter to revalidate the selected symbol against that
   observation;
5. passes the private, expiring authorization only to the execute adapter;
6. checks the execution terminal and input release;
7. observes again before deciding the next branch.

No model adapter exists inside the runtime. Unknown or overlapping branches,
unchanged evidence after an action, stale observations/symbols, association
change, unavailable/failed effects, cancellation, transition/deadline exhaustion,
delivery uncertainty and release failure stop locally with typed results.
Application task success remains separate from program completion in the future
live adapter and independent scorer.

## Deterministic result

The positive Calc-shaped test double has three observations and two actions:

```text
editing + dirty + no dialog
  -> request_save
confirming + dirty + dialog present
  -> confirm_save
done + clean + no dialog
  -> complete
```

The second action is selected only from the intermediate observation's
`confirm_dialog=present` and `confirm_target_present=true`. Both actions receive
separate fresh admission and verified release. The compact receipt reports two
observe/action transitions and zero frontier-model resumptions.

Fifteen scenarios pass on Windows and WSL: the positive path; twelve typed
safe/failed controls; and cold/warm integrations through
`adaptive_acquisition_caller_v1.py`. The cold test-double path records two model
attempts with unavailable usage, while warm records zero. These are accounting
mechanics and cannot establish savings. Four invalid interface controls reject
symbol authority, duplicate predicates, missing symbol bindings and an untyped
yield reason. The first independent audit expected eight cancellation checks
instead of the actual seven and failed; that assertion failure is retained.

Raw evidence is represented by references, but this offline adapter does not
prove that the referenced bytes were retained. Receipts therefore report
`adapter_responsibility_unverified`. The synchronous runtime also cannot bound a
misbehaving adapter that blocks past its deadline; live adapters must enforce
their own I/O deadlines.

## Decision and next evidence

Advance to a preregistered live desktop block. The candidate workflow should
ground two initially visible targets, use fresh GUI evidence after the first
action to choose the second action without another frontier-model generation,
and finish through the existing independent scorer. Include a changed/unknown
case that prevents the affected second input. Record compilation cost, every
model attempt, images, planner boundaries, local observations/actions, named
timing endpoints, releases, final correctness and raw evidence retention through
the #53 caller. Only after that mechanics gate passes should plain/current/
compiled cold and warm costs be compared.

## Evidence

- Runtime: `compiled_gui_interface_v1.py`
- Deterministic probe: `probe_compiled_gui_interface_v1.py`
- Independent audit: `audit_compiled_gui_interface_v1.py`
- Results: `results/compiled-gui-interface-01/`
