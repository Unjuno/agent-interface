# T1 formal pre-start STOP

- Issue: #6678, still open at last refresh.
- Latest main observed and incorporated before any freeze/formal call: `80e0d41b2dd6f56b0a55cd004f0ad10a6275448e`.
- Branch: `research/blackwell-observation-dominance-6678-t1-browser-20261003` (local only; not pushed).
- Proposed allocation: `BLACKWELL-OBSERVATION-DOMINANCE-6678-T1-BROWSER-20261003-01`.
- Disposition: `STOP_ENVIRONMENT_NO_EXCLUSIVE_CONTAINERIZED_CHROMIUM` before formal allocation start.

## Evidence and boundary

The local OrbStack Docker context is available, but no Playwright/Chromium Linux image is cached. The only running container visible was `unjuno-native-ci-6092` (`python:3.12-slim`, Up 29 hours), a shared CI container. It was not inspected beyond inventory or modified. No image pull/build, VM, container, WSLc, or formal candidate/audit was started. This task runs on macOS, so Microsoft WSLc is not available. A host Chromium process would not satisfy the repository's current container-backed experiment gate (#3352), and was not substituted for the formal run.

Formal T1 counts: capture 0; candidate 0; independent auditor 0; retries 0. No formal result or hypothesis verdict is claimed.

## Separate construction evidence

The initial, pre-revision browser construction capture is preserved unmodified in `construction/fail-01/`: 72 static-fixture captures, candidate exit 0, auditor exit 2 / `FAIL_AUDIT`, caused by candidate/auditor pixel-label serialization disagreement. It is a construction failure on the initial fixture, not a result for the revised left-active / neither-active / right-active fixture. No rerun was made on those same bytes.

The revised design has four host construction unit tests passing, Python compilation and Node syntax checks passing, `git diff --check` passing, analysis index passing (566 entries), and research workspace index/tests passing (156 namespaces; 21 tests). These readiness checks do not override this formal STOP.

## H / T / D / C / U

- **H:** On the revised fixed three-state fixture, left/right ROI channels produce different state partitions with opposing decision-loss preferences; full screenshot and accessibility channels distinguish all states; post-quiescence DOM mutation is uninformative.
- **T:** 24 scheduled captures/state (72 total), exact kernel estimation and Blackwell garbling LPs; raw screenshot/accessibility/mutation evidence; independent PNG/raw-only auditor. Not run.
- **D:** No D verdict: formal allocation did not start. Resume only in an exclusive containerized Chromium runtime with frozen source/image/schedule identities and a preregistration on #6678.
- **C:** Deterministic authored fixture and one browser build cannot estimate cross-browser or naturally occurring GUI noise.
- **U:** No Agent Interface runtime, real application, model, effect, safety, latency, user benefit, or product conclusion.
