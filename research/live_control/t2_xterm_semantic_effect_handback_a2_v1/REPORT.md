# XTerm semantic-effect handback A2

Issue #1541. Additive private-X11 successor to #1537 using the proven #1539 raw-PTY readiness/focus rule.

## Construction

Disposition: `PASS_CONSTRUCTION_ELIGIBLE`.

Four excluded construction rows completed with exact top-level focus readback and exact PTY byte `0x78`:
- baseline delay10: semantic receipt present, helper/XTerm exit0;
- candidate delay10: semantic receipt accepted before the absolute 8 ms post-release deadline;
- candidate delay13: semantic receipt accepted before the same deadline;
- candidate NO_EFFECT: exact `x` consumed, no semantic receipt, safe timeout, helper/XTerm exit0.

The predecessor #1537 delivery stop therefore does not recur when READY-after-`tty.setraw()` and exact top-level focus are required.

## Formal execution stop

The first formal invocation was started immediately after construction in one monolithic outer process. The environment's 45 s outer execution limit terminated that invocation before `FORMAL.json` serialization. No formal aggregate exists and no formal row is pooled.

At termination, 38 per-session directories existed in total: 4 construction sessions plus 34 later session directories. These later side-channel artifacts are retained locally only as evidence that the invocation had begun; they are not interpreted as a partial scientific result.

Disposition: `STOPPED_OUTER_EXECUTION_TIMEOUT_NO_RESULT`; scientific disposition `NONE`; formal invocation consumed1; reruns0.

A successor may change only execution packaging to immutable batches, preserving the A2 science/gates and excluding all A2 partial sessions from pooling.

## Scope

Private Xvfb/XTerm/python-xlib/XTEST only. No model/provider/network/user desktop/MAP01/shared-runtime mutation. No semantic-effect PASS/HOLD/FAIL is claimed.
