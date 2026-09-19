# Typed deadband successor v1 — formal result

## Execution

- GitHub Actions run: `35442937498` (latest repaired runner commit `5ad4f2c04d2ef92954d9a51c5bf7534bf4a60029`).
- Isolated Ubuntu/Xvfb container; Python 3.13; preregistered parameters: 3 matched pairs, 6 decisions/arm, planner wait 0.34s, cover budget 0.24s, deadband 0.06.
- The first run stopped before execution on a runner SyntaxError. That construction failure is retained in PR history. This result is from the repaired runner and is the single preregistered scientific allocation.

## Result

- `formal_mechanics_pass: true`.
- 3/3 matched coast/recovery pairs completed.
- Recovery produced 3 typed guard/deadband events; median guard-to-app release was 0.271327 ms and maximum 0.290920 ms.
- Recovery-minus-coast unsafe time: `[-178.776687, -289.620195, -292.066644] ms`; median `-289.620195 ms`.
- Stale represses before planner: 0.
- All key events balanced; all terminal input states empty.
- Six controller logs and 38 press events were independently checked.
- Raw artifact: `typed-deadband-successor-v1-35442937498`.

## Decision

`PASS_TYPED_DEADBAND_MECHANICS_SCOPED`.

This supports only the declared container/X11 mechanics scope. It does not establish DOOM efficacy, GUI generality, human tempo, model quality, token savings, production safety, or transfer. The finite sample is not a universal safety guarantee. No model calls or user data were used.