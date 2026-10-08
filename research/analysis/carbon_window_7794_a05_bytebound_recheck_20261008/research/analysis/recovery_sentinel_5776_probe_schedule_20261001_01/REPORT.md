# Issue #5776 schedule/amplitude construction experiment

**Disposition: `PASS_EVENT_COMMITMENT_REPLAY`; no zero-harm detection condition found in the frozen grid.** This is a host-only deterministic construction experiment, not formal Docker/OrbStack or live-system evidence.

## H/T/D/C/U result

- **H:** Lower pulse count or amplitude might reduce measurement-induced loss while preserving an earlier service-loss endpoint.
- **T:** The preregistered 14 amplitudes × 7 schedules × 90 matched pairs were executed once: 98 conditions, 8,820 pairs, 17,640 arms, 1,693,440 reconstructed event rows (96 ticks per arm). The 3 loads, 5 mechanisms, 6 phase IDs, capacity/demand schedules, and loss criterion were held fixed.
- **D:** The independent auditor reconstructed all event rows from separate equations. Every arm's event SHA-256 commitment and endpoint fields matched; exact inventory, 98/98 conditions, 8,820 pairs, zero errors. The result below is a deterministic tradeoff description, not a deployment decision.
- **C:** Matched no-probe arms share load, mechanism, and phase tick. All 54 no-loss control pairs per condition are retained. Probe-created loss means the probe arm crossed the frozen loss threshold while its matched no-probe arm did not.
- **U:** Analyst-authored queue fixture, finite deterministic phases, host-only macOS ARM64 / Python 3.14.5. No probability, external validity, safe-dose, adaptive policy, or runtime claim. Per-tick traces are commitment-hashed and independently reconstructed; the compact raw ledger does not retain lossless event rows.

## Result

Across the entire 98-condition grid, **zero conditions** produced positive median target loss advance with zero probe-created losses. Every target cell had both-arm target losses in all 18 pairs, so median advance is defined.

Among conditions with positive median advance, the least control harm was 18/54 probe-created losses at 16 units with a single pulse at tick 48: 28-tick median advance. The two-pulse schedule [16,48] at the same dose matched those metrics but used an extra pulse. Schedule [32,48] at 16 units produced 32-tick median advance and 19/54 control-created losses. At 20 units, [16,32] produced 48-tick advance and 30/54 control-created losses. Stronger conditions increased or retained large harm: every 40-unit schedule caused 54/54 control-created losses, regardless of using one, two, or three pulses.

Thus pulse count alone does not make the high-dose intervention benign. In this fixture, the earliest observed positive-advance/lowest-harm point still damages one third of the no-loss control pairs. No “safe” policy follows; a separate model of acceptable perturbation or an observational, non-intervening detector would be needed before any live transfer.

## Reproduction

See `RUN.json` for the exact commands, execution environment, base main and source/output identities. The independent replay is `audit.py`; its output and compact endpoint/commitment ledger are retained as `AUDIT.json` and `raw.json`. SHA-256 identities are in `SHA256SUMS`.

No OrbStack/Docker candidate or auditor was run: the shared OrbStack lane was reserved by another task and the unresolved shared-resource ownership gate remained in force. This separate construction does not consume or reopen the stopped formal allocation-02.
