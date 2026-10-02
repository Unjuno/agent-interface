# Issue #6081 T0 — frozen finite schedule comparison

## Scope

Offline exact-integer comparison of four methods that compile a bounded rational directional intent into legal 4-way or 8-way unit input slots. This is a synthetic actuator model only: no GUI, model, game, physical input, or runtime integration.

## H / T / D / C / U

- **H:** Error carry distributes rounding residual and improves worst-prefix and terminal position error over a horizon-wide nearest direction for nonrepresentable intents, without violating the integer safety envelope or increasing illegal commands, missed release, or deadline failures.
- **T:** Freeze two alphabets (cardinal and cardinal+diagonal), 12 rational per-slot intent vectors (including exact directions, shallow/near-axis, diagonal, reversed axes, and zero), horizons 1, 2, 3, 4, 5, 7, 8. Each intent is represented as `[x_numerator, y_numerator, common_denominator]` and remains constant per slot regardless of horizon. Compare A horizon-wide nearest legal direction; B independently round each desired slot; C choose the legal next slot minimizing exact squared cumulative position error at that prefix (fixed alphabet-order tie break; this is the precise error-carry rule); D safe no-continuation. Record exact squared prefix/terminal errors, switches, releases, refusals, and path-envelope breaches. Mutation controls cover unavailable combos, a one-slot deadline, omitted final release, calibration mismatch, and held-out nonlinear collision/acceleration.
- **D:** `PASS_METHOD_SCOPED` only if C strictly improves preregistered nonrepresentable linear-case aggregate worst-prefix error against A and B, has no envelope/release/deadline/illegal-command regression, and exact-representable/zero controls remain exact. Otherwise retain the specific `FAIL_METHOD`, `STOP`, or `NOT_IDENTIFIABLE` reason. No transfer claim follows.
- **C:** Improvement may be generic scheduling rather than error carry; the chosen horizon-wide baseline may not represent an optimized constant mix; switching costs are only a proxy; safety envelope is a declared synthetic integer bound.
- **U:** No actuator calibration evidence, OS latency, acceleration/collision realism, focus/authority epochs, key dwell, concurrent input, perception, or human safety. Exact endpoint/path geometry is not application evidence.

## Frozen execution controls

Construct all inputs and the independent exact-arithmetic auditor before formal execution. Candidate sees only public cases and policy definitions. Truth-side expected trajectory and oracle results are withheld until candidate raw output is written. Candidate invocation maximum 1; auditor invocation maximum 1; no retries or parameter changes. Hash plan, source, public cases, and truth oracle before candidate execution. Preserve process failures and outputs without replacing them.

## Environment

Prefer disposable Docker. At intake Docker Desktop Engine was not responding; no shared owner/lifecycle authorization exists for starting it. Use host Python only if that remains true at formal execution, and record this deviation explicitly.
