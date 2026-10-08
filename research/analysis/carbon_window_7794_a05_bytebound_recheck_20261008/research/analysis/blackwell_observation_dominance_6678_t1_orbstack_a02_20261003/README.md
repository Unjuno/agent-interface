# Issue #6678 T1 A02 — containerized browser observation sampling

Fresh successor allocation after the separate T1 pre-start STOP and construction `FAIL_AUDIT` retained at `research/analysis/blackwell_observation_dominance_6678_t1_browser_20261003/`. Neither predecessor record is revised or reused as a formal result.

## H / T / D / C / U

- **H:** Browser-rendered full-page PNG and accessibility snapshot distinguish all three fixture states; left/right ROI PNGs produce distinct one-vs-rest partitions and are Blackwell-incomparable with opposing frozen Bayes-risk preferences; post-quiescence DOM mutation is uninformative.
- **T:** Fresh allocation `BLACKWELL-OBSERVATION-DOMINANCE-6678-T1-ORB-A02-20261003-01`. Playwright 1.62.1 Chromium in an isolated Linux/arm64 OrbStack container renders an authored 960x640 fixture for 24 scheduled captures/state (72 total). A pinned Python container derives empirical kernels and exact-rational garbling LPs. A separate pinned Python container independently decodes the retained PNG pixels and reconstructs hashes, kernels, relations, and all frozen decision risks from raw evidence only. Source, image, schedule and commands are preregistered before formal execution. Each formal stage at most once; retries 0.
- **D:** `PASS_EMPIRICAL_CHANNELS_SCOPED` only if all 72 captures and every artifact digest are present, pixel and accessibility labels match all source states, all kernels sum to one, the full relation matrix agrees with the preregistered matrix and positive certificates validate exactly, left/right task preferences reverse, mutation output is state-invariant, and the independent audit reports zero errors. Missing/contradictory captured output is `FAIL_METHOD`; incomplete audit is `HOLD_AUDIT`; source/image/schedule/runtime drift before stage 1 is `STOP_SOURCE_DRIFT`. Container/launcher failure is retained as infrastructure `STOP`, not a scientific result.
- **C:** Repeated draws use the same authored DOM, browser build, OS image, viewport, theme, scale and capture code; they are technical repeats, not independent samples from a browser/app population. Accessibility semantics are specific to this Chromium/Playwright version. The hand-authored finite state oracle makes labels unambiguous.
- **U:** No Agent Interface runtime, real application, user data, LLM behavior, action/effect, safety, latency, attention, token, benefit, cross-browser or product claim. Empirical kernels describe only this fixture under this frozen browser/container configuration.

## Frozen channel and decision model

The hidden states are S0 (left target active), S1 (neither target active), and S2 (right target active), with uniform exact prior. `left_roi_png` partitions S0 from {S1,S2}; `right_roi_png` partitions {S0,S1} from S2. `full_png` samples the two fixed card-center pixels. The accessibility channel joins the two exact accessible names. The event observer starts after the rendered DOM settles and watches a frozen 500 ms quiescence interval. The four frozen losses include choosing the left target, choosing the right target, exact-state selection, and safe abstention. No smoothing or post-hoc output binning is allowed.

## Execution record

The pinned Playwright image construction smoke is recorded under `construction/`. Formal output is written once to `formal_01/`. `run_formal.sh` refuses a nonmatching source HEAD, changed package hashes, missing pinned images, or any pre-existing output directory. The browser, candidate, and audit run in three distinct network-disabled containers. Candidate/audit outputs are never overwritten or rerun.
