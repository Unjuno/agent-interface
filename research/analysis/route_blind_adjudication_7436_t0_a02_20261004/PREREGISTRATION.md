# Preregistration — ROUTE-BLIND-ADJUDICATION-7436-T0-A02-20261004

## Lineage and identity

- Successor to A01, whose immutable first outcome is `FAIL_SETUP_ENTRYPOINT` (`ModuleNotFoundError` under `python3 -I`) with candidate logic not reached, auditor 0, retries 0. A02 changes only the isolated-import entrypoint and uses a distinct random seed; it does not reuse A01 output.
- Repository: `Unjuno/agent-interface`; base main and source hashes are in `PRELAUNCH_FREEZE.json`.
- Additive path: `research/analysis/route_blind_adjudication_7436_t0_a02_20261004/`.
- Output path: `research/analysis/route_blind_adjudication_7436_t0_a02_20261004/results/`, must be absent before candidate invocation.
- Separate allocation: `ROUTE-BLIND-ADJUDICATION-7436-T0-A02-20261004`; seed `7436002` (different-order control seed `7436003`).

## H / T / D / C / U

- **H:** For six finite synthetic records across three paired strata, the explicit canary routes/candidates/branches/predicted winner will be omitted from the blinded packet view while evidence/rubric are retained; reveal will be denied before a complete commitment; seeded order will reproduce and differ under the adjacent control seed; all eight effective mutations will be rejected.
- **T:** One candidate invocation emits six packets and synthetic score commit; one independent raw-only auditor reconstructs packets and mutation controls without importing candidate/presenter code. Source directory/file names, metadata and summaries deliberately contain route canaries. Candidate adds its package path explicitly under isolated Python mode. No human, model, network, GUI, provider, GPU, or task execution.
- **D:** `PASS_METHOD_SCOPED` only for exact 6/6 packet reconstruction, evidence/rubric preservation, zero explicit route canaries in blinded packet and output filenames/paths, repeatable order, denied precommit reveal, verified complete commit and exact postcommit escrow, and 8/8 effective/rejected corruptions (metadata, filename, output path, summary, order, committed score, pointer, missing packet). Any no-op mutation, canary leakage, premature reveal, mismatch, nonzero candidate, or auditor rejection is FAIL. Stale main, occupied output, or provenance mismatch is STOP before candidate. Candidate nonzero means auditor is skipped; no retries.
- **C:** Same-process files are not a security boundary. Synthetic paired evidence may underrepresent natural route-identifying cues; label removal does not establish human blinding.
- **U:** No human-bias effect, adjudicator variance, route guess, false-positive/false-negative difference, user preference, or product claim is measured.

## Frozen commands and environment

1. Construction: `python3 -I -B -m unittest discover -s research/analysis/route_blind_adjudication_7436_t0_a02_20261004 -p 'test_package.py' -v`.
2. Candidate, exactly once: `python3 -I research/analysis/route_blind_adjudication_7436_t0_a02_20261004/candidate.py`.
3. Only after candidate exit 0, auditor exactly once: `python3 -I research/analysis/route_blind_adjudication_7436_t0_a02_20261004/audit.py`.

The A01 OrbStack containerd content-store STOP remains the host's current container limitation. No new build/pull or repeated image-store probe is part of A02. The deterministic stdlib experiment is host-only; no isolation claim.
