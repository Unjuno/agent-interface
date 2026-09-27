# Useful-control lineage-validated interval contract v3

Decision: **`PASS_USEFUL_CONTROL_LINEAGE_VALIDATED_SCOPED`**.

This is the fresh one-mechanism successor to #946. The only candidate repair is runtime causal-lineage ID validation: `Actuation.actuation_id` is a non-empty `str`, while `EffectEvent.actuation_id` is either explicit `None` (unbound) or a non-empty `str`. Interval arithmetic, release evidence, authority intersection, effect categories, corpus geometry and the independent discrete-set oracle remain unchanged in meaning.

Formal first outcome: one invocation, seed `94620260917003`, 20,000 fresh valid cases, reruns/replacements/tuning 0. Candidate and independent oracle agree 20,000/20,000; arithmetic/invariant errors 0. All 15 frozen controls pass, including rejection of actuation IDs `None`, `''`, integer `0`; rejection of effect IDs `''` and integer `0`; explicit `EffectEvent(None)` remaining unbound; duplicate valid-string IDs/release faults fail closed; overlap/authority bounds and all four effect roles remain exact.

Independent audit regenerates the full corpus from the frozen seed and returns `errors=[]`; postformal source rehash is exact 6/6; copied-result corruption controls reject 5/5. Formal result SHA-256 `0fd2e3a64c7242c91dc4b733310b99b854d33cc2ee9180b88114cc7029d93465`; ordered case digest `1262d080a7bea744bec0b85851d9c6c6eba4d3a9b0c3e6e2fc7b836294017a69`.

Boundary: this validates runtime causal-ID admission plus interval/evidence-role arithmetic on synthetic integer traces only. It does **not** establish real X11 release timing, hardware state, causal usefulness, MAP01 control quality, human tempo, production ABI, or permission to consume #869. No X11/model/GUI/task input occurred.
