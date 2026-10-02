# Issue #3951 — postcondition evidence ablation

## Delivery status: HOLD / Draft only

The local experiment completed, but publication of its executable source through GitHub MCP was blocked by the tool safety check. The exact stop is `STOP_SOURCE_PUBLICATION_TOOL_SAFETY_CHECK`. This branch contains only the preformal source-hash manifest, this non-executable report, and the audit receipt. It is NOT a complete independently reproducible research bundle. Do not merge or adopt it as one. No production runtime was changed.

The successful preformal manifest commit is `d5454f37aa359f1cc6911918b8d2e882427f707e`. Its readback Git blob is `ddb8b86cb1478348d761fb5007c91d3f99ae72be`; SHA-256 is `2e818de03205f6d87e8d4ea5d077a4efff6a9b867c602a04ce66cce102336d4f`. Full source contents were frozen locally before the run but have not been delivered to this branch. The failed source-tree publication returned no successful tree or commit identity.

## Origin and intake

Base main: `b2457b746a6df06f6536585dfe2ab937aff639f4`. README, CURRENT_GOAL, ROADMAP, open/closed Issues, open PRs and branch inventory were inspected through GitHub MCP. The narrow additive namespace did not exist on main and no matching postcondition branch was found before ownership was allocated.

This is a new successor to #3048's known-postcondition idea. #3217 keeps ownership of historical source/artifact reconciliation. No old allocation, outcome or file was modified, rerun or pooled. The original verifier was reconstructed exactly from `research/verification/known_postcondition_boundary_v1/experiment.py`, 3083 bytes, Git blob `0cd6b755cf54d8c01b254b2f8ee52610a29410f2`. Its historical main() and auditor were never run.

## H / hypothesis

Transferring a label-bound verifier into a file-receipt consumer requires decisions to depend on complete typed evidence and an independently authored expected contract, not experiment metadata or equality between missing values. The successor should retain valid saves, classify complete no/partial effect as failure, and abstain on incomplete or contradictory provenance/cleanup.

## T / fixed discriminator

Allocation: `postcondition-evidence-ablation-20260922-01`. One formal orchestration launched 24 distinct child processes in the provided Linux x86_64 execution container, CPython 3.13.5. Each child operated only on its own disposable file directory and emitted one JSON-line receipt. Independent parent observations retained pre/post file bytes, exact requests/responses, terminal process status and the fixture cleanup marker. Docker CLI was absent; this is not a Docker Desktop or OrbStack replication.

Twenty-four authored cases covered valid/no/partial effects, wrong target, retained cleanup marker, missing/null/empty values, self-consistent wrong expected digest, missing or wrongly typed flags, numeric type mismatch, stale sequence, target/session mismatch and null evidence. Every retained receipt was evaluated with three metadata variants: scenario omitted, valid, cleanup_failure. Thus 72 paired deterministic evaluations came from 24 real file allocations, not 72 independent OS trials.

Both policies saw identical perturbed evidence. The successor additionally received the immutable authored contract and required explicit typed cleanup evidence; this is a protocol change, not an equal-information efficiency comparison. The independent oracle did not use scenario labels as semantic ground truth.

## D / measured first outcome

| Endpoint | Retained result |
|---|---:|
| Formal orchestrations / retries | 1 / 0 |
| Child processes with exit 0 | 24 / 24 |
| Paired consumer evaluations | 72 |
| Successor PASS / FAIL / ESCALATE | 3 / 6 / 63 |
| Successor unsupported PASS | 0 |
| Successor label-dependent case verdicts | 0 / 24 |
| Legacy PASS, under the new contract | 32 |
| Legacy unsupported PASS, under the new contract | 30 |
| Legacy valid-save refusal | 1 |
| Legacy label-dependent case verdicts | 20 / 24 |
| Independent raw audit errors | 0 |
| Rejected evidence-corruption controls | 12 / 12 |

Local successor disposition: `PASS_EVIDENCE_BOUND_POSTCONDITION_SCOPED`.
Legacy transfer disposition: `FAIL_UNSUPPORTED_POSTCONDITION_PASS`.
Publication disposition remains HOLD, separately from both local findings.

The legacy unsupported successes include cases where both expected/observed values were absent or null, cleanup evidence was absent or false, Boolean fields were strings/integers, or the expected value was not bound to the authored contract. A valid save was refused solely when labeled cleanup_failure. These are deliberately authored cases, not estimates of natural failure probabilities.

The raw-only auditor independently reconstructed file bytes, producer receipts, field transformations, exact row identity/order, typed counts and both policies' verdicts without importing the runner or either verifier. A separate corruption process rejected missing/duplicate cases, missing exit status, changed file bytes, altered consumer fields, changed candidate/legacy verdicts, a Boolean count, altered producer receipt, Boolean/integer substitution, reordered labels and changed source binding. All three formal/audit/control processes exited 0 with empty stderr.

Construction was excluded: seven unittest methods passed, including one separately identified producer smoke and synthetic-only auditor controls. No construction failure occurred. Post-run source SHA-256 checks all matched the freeze. A storage-only check also reconciled 24 sets of request/stdout/stderr and actual file directories plus the journal: 97 checks. There are 110 retained local evidence files. Storage verification did not rerun the experiment.

Raw file: `formal/postcondition-evidence-ablation-20260922-01/raw.json`, 75609 bytes.
Raw SHA-256: `ef18a94170dc7cc84170b56ff7c20eb2f75f2616cda1c6c7d66fc4721f77118e`.
The raw bundle is not present on this branch. The accompanying conversation evidence archive contains non-executable raw data only, not the missing executable source.

## C / competing explanation

The original verifier explicitly expected named synthetic scenarios. Its old scoped result may remain valid for that corpus. This transfer test does not retroactively invalidate #3048 or complete #3217. The successor has more explicit contract information; no generic superiority or efficiency claim follows. File-byte equality alone does not prove causal action attribution.

## U / limits

One trusted local file/JSON producer, one authored contract family, no effect/observation concurrency, and terminal-state checks only. No authentication, forged-receipt detection, crash durability, GUI/window identity, model usefulness, semantic task generality, latency/token saving, cross-platform support or runtime authority is established. The leftover private marker models incomplete fixture cleanup; it is not held native input or a production resource leak. The experiment made no model/provider, network or GUI/input calls; no network-namespace isolation claim is made.

This informs #2789's result/effect-verification boundary, not complete desktop integration. The broad ROADMAP remains open. The smallest remaining scientific transfer question is whether an actual producer-bound entry path supplies these fields without label leakage; a separate allocation is required for that question. Current delivery first remains blocked on publishing the complete exact source through an authorized path.

## Roadmap disposition and branch retention

Intake, source reconstruction, excluded construction, preformal freeze/readback, one formal run, raw audit and corruption controls are complete locally. Complete source/evidence delivery and main integration are not complete. Keep this PR Draft and #3951 open; preserve #3048/#3217. Retain the owned branch because it holds the only confirmed remote preformal manifest and the pending evidence record. No unrelated branch was deleted.
