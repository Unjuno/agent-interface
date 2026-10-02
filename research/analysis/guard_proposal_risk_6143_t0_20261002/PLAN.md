# Issue #6143 — guard-induced proposal risk T0

Allocation: `GUARD-PROPOSAL-RISK-6143-T0-20261002-01`
Frozen main base: `981ba1ee20259ff36465d25aceef62fd3554a7e9`

## H / T / D / C / U

- **H:** A guard can retain high conditional rejection efficacy while truthful guard exposure induces a riskier proposal distribution that materially raises end-to-end task harm versus a fixed conservative policy. This is a planted-mechanism finite-model hypothesis, not evidence about any actual model.
- **T:** Exact-enumerate one finite two-attempt episode tree. Three quarters of task worlds make a risky proposal harmful and one quarter make it benign; a safe proposal always completes without harm. Conservative proposal risk is 1/4; the guard-disclosed compensation policy uses 3/4. A guard rejects harmful proposals with TPR 3/4 and nonharmful proposals with FPR 1/4; without a guard no proposal is refused. A refusal permits one fresh proposal; a second refusal leaves the episode unfinished. Enumerate the four cells (conservative/compensated × guard on/off), plus null-adaptation (same proposal distribution) and protective-adaptation (risk 0) controls. Use exact rational weights; no sampling, model, GUI, network, game, or external effect.
- **D:** `PASS_METHOD_SCOPED` only if the independent raw-fixture replay matches every candidate field exactly; total launched probability is conserved in every cell; guard TPR/FPR and proposal refusal rates match the frozen table; the planted compensated guard-on policy exceeds the fixed-conservative guard-on task-harm fraction by the frozen 1/10 absolute materiality margin while TPR remains 3/4; and null/protective controls are not labeled compensation. Mutated candidate output must be rejected.
- **C:** The result depends on authored world proportions, confusion probabilities, independent per-proposal guard draws, proposal-risk rates, a two-proposal cap, and the encoded rule that a safe admitted proposal completes the task. Different dependence, task feedback, disclosure salience, learning, or outcome oracle can change the comparison.
- **U:** No current Agent Interface proposal behavior, model adaptation, real guard efficacy, user/task risk, empirical net-safety change, human behavior, latency, token cost, or product/runtime effect is established. `proposal_work_units` count one abstract unit per proposal and are not tokens, money, or wall time. T1/T2 remain separately gated.

## Frozen run policy

Construction suite: `python3 -m unittest discover -s . -p 'test_*.py' -v` and `python3 -m py_compile simulator.py runner.py audit.py test_simulator.py test_audit.py`. Formal candidate once and independent auditor once, each in a separate process/container, zero retries. Container uses a digest-pinned Python image, no network, read-only root/source, output-only write mount, one CPU, 256 MiB, 64 PIDs, all capabilities dropped, and no-new-privileges. Formal inputs and implementation are SHA-256 frozen in `FREEZE.json`; raw output and audit are not placed in the source mount.
