# Result — bundled optional-effect admission check (T0b)

**Disposition: `METHOD_PASS_SCOPED_WITH_RESIDUAL_RACE`.**

Across eight paired synthetic cases, the clicked primary target ID and geometry are unchanged. In the four pre-admission effect-state cases, `TARGET_ONLY` still clicks and produces four unauthorized add-ons. The source-current `FRESH_EFFECT_BOUNDARY` blocks the readable newly selected unauthorized add-on and yields UNKNOWN for unavailable, stale-generation, and digest-invalid state; it produces zero unauthorized add-ons in those four cases.

The gate also completes the stable unchecked-default primary task and permits the deceptive-looking add-on when it was explicitly authorized. Across all eight cases, unauthorized add-ons are PLAIN 5, TARGET_ONLY 5, FRESH_EFFECT_BOUNDARY 1. That remaining fresh-gate event is the deliberately injected transition after admission but before click. The gate does not make the final read and click atomic; the one unauthorized residual is retained, not counted as solved.

The SHA-256 read digest binds target ID, effect-option ID, current selected bit and generation in the finite fixture. This is fixture-level source binding, not proof of any live application source. The independent scorer/auditor had access to click-time effects; candidate decision rows contain no scorer-only fields. Ten contract/mutation tests pass.

This is a finite synthetic method check only. It is not evidence of a current Agent Interface vulnerability, real GUI safety, broad authorization correctness, purchase protection, accessibility, atomicity, or product readiness. The original #5881 T0 result and earlier #965 target-swap evidence remain unchanged; this T0b tests the distinct unchanged-target/bundled-effect timing path.

Docker Desktop was unavailable: the Windows service and WSL distro were stopped and the Ubuntu Docker CLI could not connect because `/var/run/docker.sock` was absent. This no-model finite fixture ran on host Python 3.12.10. No container, model, GUI, site, user data, or network was used.

