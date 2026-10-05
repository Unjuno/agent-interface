# Lost-receipt cancellation archive rescue

Source: PR #6894, `79fd2fc18ea7f2ff97adab37db33641554f22cd1`.
Integration base: `1356385fa8f0fab788be2a4efac2e311f88b5c24`.

All 95 original files under `runtime/results/kernel-cancel-effect-01a0ff2c`
are restored with exact Git bytes. Historical failures, Windows execution records,
V3/V4 source context and independent public projections remain unmodified.
The restored staged packet was compared against the source commit (exit 0).

Fresh macOS Python 3.14 saved-record oracle runs, normal and optimized, both
exited 0 at 2026-10-03 19:09:49 UTC: two missing-possible-effect gaps before,
zero after, six directed corruptions rejected. This reruns the JSON-only oracle,
not the original producer or historical Windows/source-context tests. Private
originals and native input/effect evidence are not authenticated by this check.

No production code is replaced. Main already retains the possible-effect repair
and accepted-begin floor, plus newer nominal and effect-start guards absent from
the old lifecycle. The older branch's five in-module tests are covered by main's
`runtime/kernel/test_nominal_cancel_effect.py`. The three V4 joint reviewer tests
remain executable in their exact historical `.py.txt` source: fresh normal and
optimized executions against this integration tree both pass 3/3, with explicit
source-origin checks. They cover stale NONE rejection, refused cleanup then
lost-receipt cancellation, accepted explicit occurrences, and rejected expired
begin at origins 0, 2**53+17 and 10**24+17. They are not added to automatic test
discovery; their original source and invocation remain available below.
This packet rescue is not deletion authority without ref/dependency checks.

Current-tree kernel discovery passes 62/62. Local analysis-index CI runs 43 steps
with no failures. Formal experiments and native cancellation are not executed here.

```sh
REVIEW6894_SOURCE_ROOT="$PWD" python runtime/results/kernel-cancel-effect-01a0ff2c/context-v4/reviewer-test_review6894_joint.py.txt -v
REVIEW6894_SOURCE_ROOT="$PWD" python -O runtime/results/kernel-cancel-effect-01a0ff2c/context-v4/reviewer-test_review6894_joint.py.txt -v
python -m unittest discover -s runtime/kernel -t . -v
```
