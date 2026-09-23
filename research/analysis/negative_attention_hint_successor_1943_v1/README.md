# Negative-attention hint successor (Issue #1958)

This is a source-frozen, deterministic synthetic fixture for the advisory
negative-attention hint hypothesis. It does not claim model, GUI, token,
latency, or runtime results.

## Frozen contract

Controls are FULL, ADVISORY_LOW_PRIORITY, and FORCED_EXCLUSION. The fixture
contains static background, toolbar, target, effect, decorative animation, and
a deliberately changed low-priority region. Raw observation remains the
authority; advisory hints may reduce metadata only when exact reconstruction
is retained. Forced exclusion is a negative control.

Run:

```bash
python3 experiment.py
```

The runner writes only deterministic JSON to stdout and exits nonzero on any
contract failure. One invocation is the formal allocation; reruns or tuning
must use a new successor identity.
