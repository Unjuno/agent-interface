# Issue #5869 — bounded complementarity T0

**Disposition: PASS_METHOD_SCOPED.** A frozen, synthetic nine-case finite simulator and an independent raw-only auditor demonstrate that a two-check bundle can have positive decision value when each check alone has zero value, while cost, deadline, epoch, source, mandatory-gate, and low-decision-value controls are refused as specified.

## H / T / D / C / U

**H.** In a bounded synthetic interface-evidence class, myopic positive-marginal stopping can miss a useful pair. Whether this occurs in real GUI or verifier traces remains unknown.

**T.** Nine fixed finite cases / 36 world rows compared fixed checklist, one-step marginal VOI, exact two-step adaptive Bellman, and bounded pair gate. All policies used identical worlds, loss tables, costs, source/epoch declarations, budgets and deadlines. Candidate and auditor are self-contained Python standard-library programs. The independent auditor does not import candidate code and exhaustively checks depth-two trees.

**D.** The frozen gate required selection of the balanced XOR pair, positive oracle improvement over myopic, refusal of redundant/costly/late/stale/shared-source/mandatory-gate-failed/low-decision-value controls, correct candidate claims, and no mandatory-gate bypass. The auditor passed all requirements with zero errors.

**C.** Inputs are authored synthetic worlds, and losses/costs are stipulated. Source IDs and epochs are fixture labels. Recommendations have no external effects and grant no action authority. The run used CPU-only host Python 3.11.9. An RTX 3080 Laptop GPU is present, but this finite model-free enumeration has no CUDA workload for it; Docker was unavailable as a suitable lane and C: reported zero free bytes.

**U.** No inference about real complementarity, live correctness, safety, latency, cost calibration, or lookahead beyond depth two follows.

## Results

| Case | Myopic total loss | Bellman-2 total loss | Pair-gate total loss | Finding |
|---|---:|---:|---:|---|
| XOR complementary | 1.00 | 0.20 | 0.20 | Pair selected; +0.80 net value vs no checks |
| Redundant duplicate | 0.10 | 0.10 | 0.50 | Pair gate declines; one check is optimal |
| Diminishing returns | 0.46 | 0.46 | 0.50 | Pair gate declines |
| XOR too costly | 1.00 | 1.00 | 1.00 | Pair gate declines; fixed checklist costs 1.20 |
| Pair too late | 1.00 | 1.00 | 1.00 | No query |
| Epoch mismatch | 1.00 | 1.00 | 1.00 | No query |
| Shared source | 1.00 | 1.00 | 1.00 | No query |
| Mandatory gate failed | 1.00 | 1.00 | 1.00 | No query |
| One-bit, low decision value | 0.05 | 0.05 | 0.05 | Information gain does not justify 0.06 cost/check |

The XOR fixture uses the earlier four equally likely worlds: either observation alone has zero information about the target, while the pair determines it. This run formalizes that calibration in the nine-case comparison; it is not a fresh empirical observation.

## Run integrity

The source/fixture freeze precedes the formal runs and records exact SHA-256 and Git blob identities. Construction tests passed 11/11 against exact GitHub readbacks before freeze. One candidate process and one separate audit process ran, each with exit code 0. A preceding PowerShell redirection syntax attempt failed before Python launch, so it is recorded as a shell preflight failure, not a candidate invocation. The retained `AUDITOR_INPUT.json` is a structured reconstruction from frozen inputs and candidate output, not the original serialized stdin bytes. Exact stdout hashes and commands are in [RUN.json](RUN.json); formal outputs are retained in `results/`.

The candidate output at [CANDIDATE.stdout.json](results/CANDIDATE.stdout.json), audit at [AUDIT.stdout.json](results/AUDIT.stdout.json), frozen fixture, source, and construction notes are all retained. This experiment did not change or supersede any earlier Issue result. Issue #5869 remains open for a separately preregistered real-receipt successor with independent task/effect truth and coordinated resources.
