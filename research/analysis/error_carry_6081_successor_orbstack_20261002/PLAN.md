# Error-carry action compilation — fresh T0 successor

Issue #6081 proposes distributing a fixed directional intent across finite legal input slots. Prior records remain unchanged: #6087 `FAIL_UNSAFE_SCHEDULE`, the S1/S2/S3 runner/materialization STOPs, and #6091 `STOP_METHOD_INVALID_BASELINE`.

## H / T / D / C / U

**H.** For a constant rational intent and explicit constant-displacement action alphabet, deterministic error carry can reduce worst-prefix squared displacement error relative to a valid Euclidean-nearest fixed action while respecting every prefix safety box and switch cap. In a stationary model, “horizon-wide nearest action held for all slots” and “independent per-slot nearest action” may be mathematically identical; the experiment tests that baseline identifiability rather than presuming two independent comparators.

**T.** Frozen `fixture.json` has 4-way and explicitly stipulated 8-way action dictionaries and eight exact-rational cases: exact cardinal, shallow slope, near-axis duty, diagonal, zero, reversed diagonal, finite-horizon lattice mismatch, and an envelope-limited case; plus out-of-hull and unknown-calibration refusal controls. Compare A (whole-horizon Euclidean-nearest constant action), B (per-slot Euclidean-nearest, no error state), C (greedy cumulative-error carry), and D (release/no continuation). Score every prefix, terminal error, switches, envelope breaches, refusal, and release. An independently implemented exact-rational auditor reconstructs all rows from the fixture and raw output. All allocation execution is in disposable OrbStack containers, network disabled, read-only source, separate output mount.

**D.** `PASS_METHOD_SCOPED` only if (1) A and B equivalence is established for all valid stationary cases; (2) C strictly reduces worst-prefix squared error versus the common A/B baseline in at least three preregistered feasible nonrepresentable cases; (3) C adds no envelope, switch, deadline, illegal-action, or release violations; (4) exact/zero/refusal controls pass; and (5) independent audit reproduces all rows. Otherwise report the exact `FAIL_*` or `HOLD_*`; never infer runtime transfer.

**C.** Exact rational constant-displacement model; legal diagonal vectors are stipulated in the fixture, not inferred from key labels. Python stdlib only. OrbStack/Linux ARM64 image identity and resource limits are frozen. No GUI, model, game, host input, GPU, or external network.

**U.** No calibration or empirical actuator semantics, acceleration/collision, focus, timing jitter, concurrent keys, task effect, human performance, or live control. Prefix boxes are synthetic and do not establish real-world safety. Any scoped PASS only supports this finite mathematical fixture.

## Freeze protocol

Pre-freeze container construction tests may execute code and are not formal candidate/audit runs. After freeze, invoke candidate once and auditor once in separate fresh containers, no retries. Preserve raw files, process receipts, image/source hashes and exact commands. STOP on any source, mount, output, or process integrity problem.
