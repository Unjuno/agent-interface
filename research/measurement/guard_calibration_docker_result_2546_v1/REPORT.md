# Docker A3 guard calibration result — successor #2546

## Formal disposition

**PASS_GUARD_POLICY_RECOVERABLE_X11_CALIBRATION_A3_SCOPED**

This is a fresh execution of the frozen #1793/#1811 source in a disposable Docker container. The historical #1793/#1811 result is not modified or pooled.

## Environment and execution

- container: `python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`
- installed: `python3-tk`, `xvfb`, `xauth`, `python-xlib`
- route: private Xvfb/Tk/XTEST recoverable stale-action fixture
- construction: 64 calibration groups, 192 policy rows
- formal: 128 calibration groups, 2048 policy rows, bootstrap n=10,000
- formal invocations / reruns / replacements / tuning: 1 / 0 / 0 / 0

## H/T/D/C/U

- **H:** a fresh support-complete same-route execution can test the A3 calibration without historical-row pooling.
- **T:** frozen source, construction gate, one formal invocation, independent raw-row audit.
- **D:** raw JSON hashes, audit hashes, source hashes, container digest and stdout were retained locally; compact evidence is committed here.
- **C:** recoverability, terminal neutrality, positive cost CI lower bounds, support, no leakage, and independent audit must pass.
- **U:** one synthetic private-X11 route only; natural stale incidence, deployment economics, general GUI reliability, model/token benefit and human tempo remain unknown.

## Results

| metric | result |
|---|---:|
| construction | PASS_CONSTRUCTION_ELIGIBLE |
| formal | PASS_GUARD_POLICY_RECOVERABLE_X11_CALIBRATION_A3_SCOPED |
| c_y_stale | 5.784590 ms; 95% [5.633548, 5.935140] |
| c_y_fresh | 6.101006 ms; 95% [5.905561, 6.302130] |
| c_f | 9.791569 ms; 95% [9.642038, 9.938545] |
| sensitivity s / false reject f | 1 / 0 |
| negative cost samples | 0 for all three families |
| stale-noop recovery | PASS |
| terminal button neutrality | PASS |
| resolved held-out tiers | q=1/5, q=1/2 |
| selector disagreements among resolved tiers | 0 |
| unresolved tiers | q=1/100, q=1/20 (CI crosses zero) |
| independent audit | PASS; 128 calibration groups, 2048 policy rows, 336 stale-noop episodes |

The formal process exited successfully. No model, provider, network, user desktop, or authority call occurred.

## Evidence boundary

The complete formal JSON is 2.1 MB and is retained by hash rather than duplicated in this compact repository artifact. Reproduction requires the exact frozen source, container digest, command, and retained raw artifact. This PR is an evidence ledger, not a general guard-policy or production claim.
