# T0S5 audit-only successor

Allocation `INTENT-SLOT-6081-T0S5-20261002-AUDIT-01` is an audit-only continuation of S4. It does not re-run S4's candidate or its failed auditor. Its sole input raw is S4 `results/formal-01/raw.json`, SHA-256 `81e8e0f9d34de42272744a3793162fe0cb857c77b8e67f28108f28dfc4bc8e49`; its fixture is the byte-identical S4 frozen `fixture.json`.

The new auditor independently reconstructs all A/B/C/D rows with rational arithmetic; validates the refusal schema separately from scheduled-result schema; checks exact A/B stationary equivalence; admits only nonrepresentable, in-hull cases where both baseline and candidate schedule are safe; checks every C prefix, switch cap, legal action and release; and reports the preregistered win threshold. Formal budget: this new auditor one invocation, zero retries; candidate invocations zero by design.

Construction checks test refusal handling, result reconstruction primitives, and mutation rejection on synthetic mini-fixtures. They do not load or audit S4 formal raw. Formal S5 reads the S4 raw read-only and writes only S5 output.
