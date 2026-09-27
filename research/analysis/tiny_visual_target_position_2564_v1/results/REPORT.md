# Tiny local visual model target-position support — formal result

**Decision: `PASS_TARGET_POSITION_SUPPORT_SCOPED` (the preregistered pooled gate passed).** This scoped result must not be summarized as robust translation handling: the treatment's entire pooled ACCEPT gain came from one of the two held-out translations.

## Protocol and execution

- Successor to #2564; original issue/results remain unchanged. See [Issue #4752](https://github.com/Unjuno/agent-interface/issues/4752).
- Frozen protocol: [FREEZE.json](https://github.com/Unjuno/agent-interface/blob/research/tiny-visual-target-position-2564-20260927/research/analysis/tiny_visual_target_position_2564_v1/FREEZE.json), SHA-256 `4b4996dcf7e71900c6fac3938126654ecfb4be5efd95b7ec7ccb4f5197bb1b05`.
- One local Docker invocation, exactly 10 NumPy fits (five paired seeds × control/treatment), 250 full-batch updates each. Container was pinned by image ID, linux/amd64, Python 3.11.2/NumPy 1.24.2; CPU 1, memory 2 GiB, PIDs 64, read-only root filesystem, network none, no GPU, no package pulls/installs. Formal exit 0, stderr 0 bytes, all 2,400 evaluation predictions retained. Formal wall time including data construction/evaluation was 5.73 seconds; sum of fit timers was 5.4772 seconds.
- Four no-fit protocol tests passed before training. A separate container audit regenerated inputs, checked source/weight/prediction bindings, recomputed all predictions and verified the receipt/freshness fixture: complete, `errors=[]`.

## Results

At the preregistered model-ACCEPT threshold `p >= 0.75`, treatment pooled held-out positive acceptance was 200/400 (50%), versus 0/400 for control: +0.50 absolute, treatment better on all five paired seeds. Both arms preserved base positives at 200/200. The treatment made zero false ACCEPTs on 600 negative cases. The separate fixture accepted a current matching positive and rejected stale, digest-mismatched, and negative cases.

The per-translation results are sharply different:

| Held-out positive location | Control ACCEPT / YIELD / REJECT | Treatment ACCEPT / YIELD / REJECT |
| --- | ---: | ---: |
| translation_a `(20,25)` | 0 / 175 / 25 of 200 | 0 / 200 / 0 of 200 |
| translation_b `(8,15)` | 0 / 157 / 43 of 200 | 200 / 0 / 0 of 200 |

Thus translation_a improved 0.5-threshold classification substantially (mean 0.9225 vs 0.5) but yielded on every positive instead of ACCEPTing. The pooled confidence-gate pass is entirely driven by translation_b. Negative rows were rejected in both arms; there were no negative YIELD/ACCEPT outputs in these formal runs.

## Interpretation and handoff

Within this authored synthetic task, exposing the tiny model to several positive positions helped one unseen location family while retaining the base and negative controls. The result does not establish location-invariant learning: an equally unseen translation remained below the ACCEPT threshold. Keep this finding separate from the receipt/freshness gate result and from any real X11/GUI claims. A useful follow-up would preregister a denser direction-balanced position grid and independent tile family, while preserving a per-location minimum ACCEPT gate so pooled gains cannot mask a failed shift.

Machine-readable details: `RESULT.json`, `AUDIT.json`, `DECISION_RATES.json`, raw prediction/manifests/receipts, final weight packages, and formal stdout/stderr records in this directory.

