# Text-delivery payload-aware routing v1

Question: does binding direct-key eligibility to the full payload and live keyboard map repair the coarse `ASCII -> direct_keys` decision without hiding clipboard side effects?

Finite formal candidate after development: 4 fresh private Xvfb arms in fixed order US, German, French, US-Dvorak. Per arm evaluate 13 payloads under transparent and explicit clipboard-side-effect budgets: representable control `office`; the full union of the German/French Group1-level0/1 ASCII gap (`#@[\\]^` + backtick + `{|}~`); and Unicode control `βeta`. Total 4 × 13 × 2 = 104 trials. The prior #328 result already retains exhaustive 95-printable-character direct-key coverage; this experiment does not duplicate that matrix.

Hard gates: payload-aware route selected before input; direct routes exact; no-route cases zero input/effect; clipboard route only when all three clipboard side effects are authorized, with direct emissions still zero; representable payloads prefer direct even if clipboard is allowed; applied map invariant during candidate execution; terminal physical input empty. Coarse selector decisions are retained only as a comparator, not an execution oracle.

H: payload-aware preflight exposes every retained German/French ASCII gap and allows safe pre-input fallback negotiation. D: PASS only if every trial gate passes and all four arms pass. C/U: Group1 level0/1 projection only; clipboard mutation is explicit and nontransparent; no full XKB/IME/Office/Wayland/Windows/macOS/model-token/product claim.
