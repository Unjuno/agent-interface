# Issue #6678 T1 A03 — strict-pixel empirical channel check

Successor to A02 `STOP_RUNNER_FAILURE`, not a rerun. A separate unregistered construction pilot exposed that the original pixel coordinates landed on text and produced `unresolved` labels. The pilot's accessibility/full equivalence was already expected by the frozen relation matrix; the decisive defect was failure to enforce the exact RGB oracle. A03 freezes text-free interior pixel anchors and an independent auditor that rejects any mismatch against the authored state RGB values.

## H / T / D / C / U

- **H:** Browser-rendered full screenshot and accessibility output encode the same three-state partition; left/right ROI channels form opposing one-vs-rest partitions, are Blackwell-incomparable, and prefer opposite routes under the corresponding losses; the post-quiescence mutation channel is uninformative.
- **T:** Allocation `BLACKWELL-OBSERVATION-DOMINANCE-6678-T1-ORB-A03-20261003-01`. One fresh 72-capture schedule (24 per state) in pinned Playwright Chromium on OrbStack linux/arm64. Candidate calculates empirical kernels, exact rational garbling certificates and Bayes risks. A distinct auditor independently decodes raw PNGs, checks exact expected RGB at the frozen text-free points, checks all raw hashes and manifest coverage, reconstructs channel relations and risks, and validates positive certificates.
- **D:** `PASS_EMPIRICAL_CHANNELS_SCOPED` only if all 72 captures and 360 artifact digests validate, all exact pixel/accessibility labels match the state oracle, empirical relations match the frozen matrix with valid exact certificates, opposing task preferences hold, mutation deltas are empty/state-invariant, and independent audit has zero errors. Oracle mismatch is `FAIL_METHOD`; incomplete evidence is `HOLD_AUDIT`; source/runtime drift before invocation is `STOP_SOURCE_DRIFT`.
- **C:** One deterministic authored fixture and one Chromium build; repeats are technical, not independent application/browser population samples. The fixture tests the measurement pipeline and finite channel order only.
- **U:** No real application, Agent Interface runtime, user data, LLM behavior, action/effect, safety, latency, attention, token, benefit, cross-browser or product inference.

The two ROI channels encode different binary partitions of three equiprobable states. Their task risks should reverse: `choose_left` prefers left ROI and `choose_right` prefers right ROI. Full-page and accessibility channels both distinguish all three states, so the frozen model predicts mutual garbling/equivalence. No post-hoc binning, smoothing, or anchor changes are allowed after freeze.

`construction/` contains diagnostic work on the earlier unregistered pilot only. It is not formal A03 evidence and is not substituted for the fresh scheduled capture. Formal result, if run, is stored once under `formal_01/`.
