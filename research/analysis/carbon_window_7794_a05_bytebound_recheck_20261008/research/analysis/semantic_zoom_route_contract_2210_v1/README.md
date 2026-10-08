# Semantic zoom route contract audit (#2210)

## H/T/D

The hypothesis is that semantic route choice must use verified capability and task-effect dimensions, not visible scale alone. Six frozen states are passed through the executable policy in `run_check.py`; observed decisions are compared with expected decisions.

Reproduction: `python3 research/analysis/semantic_zoom_route_contract_2210_v1/run_check.py`.

## C

Visible scale equivalence does not prove cursor anchoring, focus, selection, modal state, document semantics, or input neutrality. A deterministic policy check cannot establish live application behavior or model utility.

## U / stop

Disposition: `HOLD_PRE_MODEL_SEMANTIC_ZOOM_TRANSFER`. No model, GUI, input, network, or live application was used. A future live successor must preserve this matrix, add an independent document/effect scorer, and test a held-out application-like route.
