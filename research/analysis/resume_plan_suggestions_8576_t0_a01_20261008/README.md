# Issue #8576 T0 A01 — grounded optional resume suggestions

## H/T/D/C/U

- **H:** In a finite public task contract and fresh observable state, a deterministic selector can suggest a next checkpoint only when all admissible contract orderings support the same one; ambiguity, stale/mismatched state, terminal states, unresolved effects, or missing contract should cause abstention.
- **T:** Evaluate 12 authored cases: unique initial/after-receipt, two ambiguous alternatives, stale state generation, wrong window, changed task, completed task, cancelled predecessor, unresolved effect, absent contract, and two identical public states paired to different hidden labels. Candidate receives `input.json` only; hidden labels are sealed in `truth.json` for the auditor.
- **D:** `PASS_METHOD_SCOPED` only if the independent topological-order oracle and sealed expected labels agree on all cases; every suggestion has version/task/window/generation/source provenance; all ambiguous/unsafe cases abstain; authority remains `none`; freshness is explicitly `snapshot_requires_revalidation`; and six frozen mutations are rejected.
- **C:** User-authored cues may be more accurate; review/edit friction may erase any convenience; even a public, unique checkpoint can anchor a person or become stale immediately after display.
- **U:** Synthetic method evidence only. No participants, human-preparation-effort result, cognitive-benefit or harm result, model, GUI, app state, action, task continuation, or product claim. Any human benefit requires a separately reviewed and approved study.

## Frozen procedure

T0 candidate computes ready checkpoints from a versioned active contract, typed dependency graph, exact task/window binding, fresh observed generation, completed/cancelled receipts, and an empty unresolved-effect set. It suggests only when the public graph has exactly one possible first checkpoint. The auditor independently enumerates all topological continuations and reconstructs the set of possible first steps; it does not import the candidate. Outcomes include only `SUGGEST`/`ABSTAIN`, a scoped checkpoint identifier, source provenance, no-action authority, and a revalidation warning.

The pair `paired_hidden_a` / `paired_hidden_b` has byte-identical public input but different auditor-only hidden labels. The candidate is invoked only on `input.json`; no hidden label is passed to it. Public output must remain equal modulo case identity.

Preformal construction tests run normally and under `python -O` in a network-disabled WSLc Python 3.12 container. After source/data/docs hashes and image identity are frozen and committed, formal candidate runs once; only exit 0 permits one auditor run. Output paths are exclusive-create. Any first launch, candidate, audit, mutation, or checksum failure is retained; no retry, pooling, label substitution, or threshold adjustment.

## Runtime and scope

Microsoft WSLc 3.0.1.0, local `python:3.12-slim` image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, Python 3.12.14, linux/amd64, network disabled. Docker Desktop is not required or used. This experiment makes no host resource-enforcement claim. The result applies only to this finite authored schema and fixture.

