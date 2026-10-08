# Analyzer release-order boundary — WSLc A02

Status: preregistered construction test; no live-control claim.

## H — Hypothesis
The retained-input analyzer must reject an input-release trace when the release-call bracket starts before the input-admission acknowledgement. Otherwise it can report measurement_ready=true with a negative retained-time lower bound.

## T — Test
Run the complete test_analyze_map01_direct_retained_input_v1.py unittest module under WSLc/Linux using the read-only checkout mount and pinned cached image python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f. Network is disabled. Declared limits: one CPU, 512 MiB. The candidate regression is test_release_before_input_ack_is_rejected.

## D — Decision
PASS only if the full module exits zero with all six tests passing and no failures/errors. A setup/mount/image/runtime failure is STOP retained under this ID. Any failed assertion is FAIL. Neither outcome establishes real X11 behavior.

## C — Competing explanations
A parser/order rule can be correct on Windows but behave differently under Linux Python; container/runtime differences may prevent source mount or execution. Synthetic traces may not cover all event orderings.

## U — Limits
This is a pure analyzer construction test with synthetic timestamps. It does not establish actual input-admission or release timing, physical key state, application feedback, threat handling, recovery, task effect, or live latency. CPU/memory limits are declarations only unless independently proven enforced.

## Frozen provenance
- Source checkout commit: dc7b2f478fd00181b36789920bd96bc0e8254330
- Candidate analyzer SHA-256: 73d32c1d1a520f26daa6abce458d2fdbb9d19267d3c3387a9b53a9947a90a011
- Candidate test SHA-256: c24d7a734624423f5bebb4592bebb8cb25f9e1cd0288647f85f04c3306749320
- Image digest: python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f (cached locally before this run).
- Command: wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --mount type=bind,source=C:/w/keyupr3,target=/src,readonly python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python3 -B -m unittest discover -s /src/research/doom -p test_analyze_map01_direct_retained_input_v1.py -v
