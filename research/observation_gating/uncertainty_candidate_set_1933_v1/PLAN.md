# #4146 exact-max candidate-set cueing

H: exact detector-score ties are ambiguity, not evidence for exclusive top-1 truth. Preserve all exact maxima as inspection candidates.

T: 48 deterministic four-region byte cases: 12 unique maxima, 24 two-way ties, 12 three-way ties. Compare TOP1_HARD against EXACT_MAX_SET. Raw bytes retained; fixture truth is scoring-only. Standard library only; no GUI/model/network/input.

D: PASS_AMBIGUITY_PRESERVING_CUE_SET_SCOPED only if candidate equals the independently reconstructed exact-max set 48/48; unique controls are singleton true 12/12; all 36 ties contain truth with exact cardinality; top1 omits truth in exactly 21/36 ties; zero input-authority flags; independent audit errors0 and >=8 corruption controls reject.

C: authored exact ties and region truth; no natural tie-rate, perceptual detector quality, model benefit or production-code allegation.

U: near-ties, confidence calibration, live GUI, multimodal model behavior, tokens/latency, task outcome and production integration.
