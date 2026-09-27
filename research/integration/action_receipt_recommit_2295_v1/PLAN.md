# Issue #2295 — live recommit receipt boundary v1

## H
A stable/rebindable commit identity can revive a stale prepared GUI action after invalidate/recommit. A fresh epoch prevents that ABA path but does not by itself cover target/session/authority replacement or duplicate delivery. A compound non-rebindable receipt with one-shot operation consumption should reject the directed stale/replay cases while retaining fresh current actions.

## T
Private Xvfb + ordinary Tk Button effect, real XTEST click, separate receipt prepare/validate subprocesses. Policies REUSED_ID, FRESH_EPOCH, COMPOUND. Scenarios STABLE_CURRENT, RECOMMIT_SAME_CLAIM, DOUBLE_RECOMMIT, TARGET_REPLACED, AUTHORITY_CHANGED, APP_RESTARTED, DUPLICATE_DELIVERY, TRUNCATED_RECEIPT, FRESH_AFTER_RECOMMIT. Two repetitions = 54 formal cases. Construction is separate/excluded.

## D
PASS_RECOMMIT_RECEIPT_RUNTIME_BOUNDARY_SCOPED only if all 54 cases/processes/effects reconcile; REUSED exposes the directed stale/replay witnesses; FRESH rejects old epochs but retains its residual non-epoch failures; COMPOUND has zero stale/cross-target/cross-session/authority/duplicate/truncated unsafe effects and admits both stable and freshly re-prepared positives. Separate raw-only audit and all corruption controls pass.

## C
Fixture-supplied exact target geometry/identity; COMPOUND has more identity information than controls. This is a receipt/runtime boundary experiment, not a model comparison or production patch.

## U
No model policy/tokens, hostile forgery, power-loss, arbitrary toolkit, cross-platform, natural race rate, latency benefit or integrated desktop acceptance.
