# Issue #8185 A02 — STOP before candidate

**Disposition: `STOP_PRE_CANDIDATE`.** At the frozen base `2c1c90c80389dc6aab6a950c7058528272979f2d`, the required OrbStack runtime responded as Docker 29.4.0, but its read-only image inventory failed on containerd blob `sha256:82177ab70cdeaf9c0298399ef3e274963de595372dfc46186dc1b74703f132ff` with `operation not supported`.

The protocol requires this macOS experiment to use OrbStack. The candidate and auditor were each invoked zero times; construction suite invocations and retries were zero. No image pull, store repair, host fallback, or scientific inference was made. Full preflight output and exit codes are retained alongside the experiment protocol and run receipt.

Resume only in a fresh allocation after read-only OrbStack image inventory succeeds and the issue's source/oracle/comparator freeze is complete. This STOP is not evidence for or against the transform-graph hypothesis. A01 remains immutable in its own package and PR.
