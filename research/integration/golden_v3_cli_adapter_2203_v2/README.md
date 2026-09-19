# Golden v3 CLI adapter contract v2

Successor to closed #2203/#2209. This is an offline, authority-neutral adapter gate.

H/T/D/C/U: map known CLI statuses to the frozen golden-v3 result schema; reject unknown or missing status/lifecycle without silently coercing to partial; retain diagnostics, partial effects and usage; keep task success distinct from program completion; cleanup failure cannot report success. PASS requires candidate/oracle agreement for all fixtures in a Python 3.12 container. No model, GUI, input, network, live runtime or production claim.
