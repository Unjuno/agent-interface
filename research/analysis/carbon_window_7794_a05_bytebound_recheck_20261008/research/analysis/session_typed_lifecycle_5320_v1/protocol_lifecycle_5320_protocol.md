# Issue #5320 finite lifecycle protocol experiment

## Registration / H-T-D-C-U

- **H:** A deterministic protocol monitor rejects illegal lifecycle transitions that convention-only checks accept, while retaining the explicit UNKNOWN/recovery/release path and creating neither authority nor external-effect truth.
- **T:** Run the same six frozen event traces through `CONVENTION_ONLY`, `RUNTIME_AUTOMATON`, `LINEAR_PROTOCOL`, and `MULTIPARTY_PROTOCOL`: release-before-acquire; expiry-before-commit; unknown outcome followed by absent resolution and release; duplicated linear capability; role mismatch; unknown event. Expected classifications are independently enumerated in the test assertions rather than derived from the monitor's transition map.
- **D:** Scoped PASS requires (a) illegal ordering rejected by automaton policies, (b) valid UNKNOWN recovery path accepted, (c) capability replay and wrong-role events rejected by their respective stronger policy, and (d) no authority/effect claim emitted. Any missed illegal event, broken valid recovery, or authority/effect claim is FAIL. This is an abstract protocol-fidelity gate only.
- **C:** No model, GUI, input, GPU, external service, or persistent runtime change. Baseline is intentionally a weak convention-only comparator, not an assertion about the repository's existing production checks. One deterministic process; Python standard library only.
- **U:** This finite toy automaton does not establish extraction fidelity, liveness under arbitrary schedules, effect truth, runtime integration, or general GUI safety. The live shared OrbStack daemon had an unrelated running container and no fresh exclusive allocation was visible; Docker was therefore not used.

## Frozen identity and command

- Repository: `Unjuno/agent-interface`
- Main observed before execution: `c4735cfd27bfca057d9c1fca9a7ea19866f77259`
- Issue: [#5320](https://github.com/Unjuno/agent-interface/issues/5320), proposed/unverified.
- Test command: `python3 -B -m unittest -v test_protocol_lifecycle_5320`
- Decision: continue only if all six tests pass; otherwise preserve first failure and stop this rung.

## Interpretation

This package is a synthetic, authority-neutral discriminator. The convention-only arm accepts known events without validating lifecycle order; it intentionally represents a lower-bound comparator. The other arms share the monitor transition semantics, with capability and role checks layered on top. A PASS only shows that this small encoded matrix distinguishes those policies as specified. It does not show that protocol typing is superior to all current repository contracts or that any external effect happened.
