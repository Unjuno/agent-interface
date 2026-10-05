# Issue #8185 T0 result

**Disposition: `PASS_METHOD_SCOPED`** for the finite authored transform model. Candidate invocation 1/1, exit 0; independent oracle auditor invocation 1/1, exit 0; retries 0. The candidate and audit raw outputs are retained and hash-bound. The prior #4323 and #6684 evidence is unchanged.

## Result

The 18-row corpus contains eight valid-affine cases and ten stale, incomplete, malformed, identity, non-affine, or uncertainty-boundary controls. Independent oracle comparison found 0 row mismatches and 0 false admissions. The graph admitted all seven valid-affine cases whose uncertainty region fit wholly inside the target and refused the independent-error boundary case. It also refused all ten invalid/unmodeled controls.

On the eight valid-affine cases, the single-offset/last-known-scale baseline returned `UNKNOWN_REFUSE` on 5; the graph returned `UNKNOWN_REFUSE` on 1. This is an 80% reduction in false UNKNOWNs (4/5) and exceeds the frozen 20% gate. The shared-uncertainty case was admitted only when the action and target region carried the same correlation identity; changing that identity in a construction control caused refusal. The one baseline false admission was the swapped target-identity control; the graph refused it.

The checked rows include stable identity, window translation, uniform scale, a mixed-monitor affine chain, a two-epoch composition, a small-residual composed chain, common-mode uncertainty cancellation, independent uncertainty crossing a boundary, stale epoch, missing/reversed/duplicate edges, unit mismatch, input-DPI context change, target identity swap, non-affine reflow, target-boundary crossing, and forbidden-region overlap.

## Execution and integrity

Frozen base `2c1c90c80389dc6aab6a950c7058528272979f2d`; Python 3.14.5 on macOS arm64. OrbStack's read-only image inventory failed on a missing content blob with `operation not supported`; no image pull, container start, or store repair was attempted. The finite CPU-only Issue protocol was run host-only; no container isolation is claimed. No model, GUI, native OS coordinate API, user data, input, application effect, or external side effect was used.

The construction suite passed 7/7 before the freeze. Exact formal commands: `python3 -B candidate.py` once, then `python3 -B audit.py` once. See `FREEZE.json`, `RUN.json`, `candidate_output.json`, `audit_output.json`, and `SHA256SUMS`.

## Scope

This demonstrates arithmetic and fail-closed behavior only for the declared finite affine graph and uncertainty contract. It does not validate Windows DPI virtualization, any OS/backend transform, the accuracy of declared residual bounds, native hit testing, semantic grounding in an application, live task effects, latency, safety, or product benefit. The improvement is fixture-specific, not a population estimate or evidence that a general transform graph is needed in production. Any native feasibility test remains a separate gate with explicit disposable-session ownership.
