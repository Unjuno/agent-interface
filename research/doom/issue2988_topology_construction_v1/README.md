# Issue #2988 topology-aware subgoal scorer construction (v1)

## H / T / D / C / U

**H.** A frozen directed-topology oracle can distinguish useful route progress
from Euclidean-distance increase and coverage-only exploration in a finite
counterexample deck, while preserving `UNKNOWN` when the observed state is not
adjudicable.

**T.** Run a deterministic, standard-library-only scorer against four frozen
synthetic traces: (1) a valid route that initially moves farther from the goal,
(2) a coverage-only loop with no route progress, (3) wrong-direction movement,
and (4) an unknown node. Independently audit expected classes and mutate the
goal/graph input identity and decision records.

**D.** `PASS_CONSTRUCTION_SCOPED` requires all four classes and all frozen
integrity mutations to be distinguished exactly. Any semantic mismatch is
`FAIL_CONSTRUCTION`; missing topology or unknown state must stay `UNKNOWN`,
never be imputed as progress. This is a method construction rung only.

**C.** Synthetic directed graph, hand-authored coordinates and known traces;
no Freedoom geometry, VizDoom, model, GUI, game, input, or user desktop.

**U.** This cannot establish that a real MAP01 topology can be safely extracted,
that a useful subgoal can be frozen without controller leakage, or that the
deoptimization arm improves navigation. Formal #2988 remains untested.

## Execution record

The frozen deck contains four 5-node-or-shorter traces. It is executed once by
`run.py`; `audit.py` independently recomputes decisions from the frozen graph
and trace inventory. No container was used: the shared X11/container lane is
explicitly occupied by another allocation, so this isolated pure-Python method
test is host-only and makes no claim about a container gate.

