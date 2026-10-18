# A01 result-audit correction v3

This additive audit checks the complete retained A01 RESULT.json against the
frozen source records. It preserves the original v2 result and audit unchanged;
it does not rerun the allocation.

The v2 independent validator recomputed core coverage, interruption rows,
latency ranges and task outcome, but accepted edits to main_commit,
allocation_id, prior_audit_formal_pass, all_cancellation_rows,
per_key_release_measurement_events, independent_useful_feedback_timestamp,
and decision. The correction derives the full expected result from the
accepted/terminal/cancel/release rows, owner records, report, prior audit, and
pinned freeze, then compares every field using canonical JSON so type changes
and extra/missing keys also fail.

The loader independently checks the original freeze Git blob and SHA-256, then
each frozen raw input's Git blob, SHA-256 and byte length. It also enforces
cancel request ≤ verified-empty terminal release ≤ terminal timestamp, including
cancellations without an interruption receipt. Per-key detection recognizes
the V12 fields key_release_attempts, key_release_intervals_ns, and explicit
keyup server_keyup_attempts. This is telemetry validation; it does not establish
physical key duration or application consumption.

The allocation ID is cross-checked against the frozen preregistration. The
result's main_commit field refers to the Git container holding the retained
evidence; the original run's source identities remain those listed in that
preregistration, rather than being inferred from the container commit.

## H / T / D / C / U

- **H:** The retained v2 result can be bound field-for-field to its frozen raw
  trace and source provenance, rejecting all seven previously accepted claim
  mutations.
- **T:** Run the v3 independent loader and validator over the original retained
  inputs. Mutate each of the seven claims separately, exercise V12's actual
  per-key field names, and reverse the no-interruption cancellation chronology.
- **D:** Pass only if the unchanged result validates, each mutation is rejected,
  the loader verifies all five frozen inputs, and the original v2 files remain
  byte-identical.
- **C:** This is a posthoc audit correction over one historical allocation.
  It does not improve runtime instrumentation or turn aggregate empty-state
  receipts into per-key physical measurements.
- **U:** No live threat exposure, physical-key duration, independently useful
  feedback, recovery efficacy or task-completion result is added.

## Reproduction

From the repository root:

    python -m unittest -v research.doom.v39_release_trace_completeness_posthoc_a01_20261008.test_audit_result_v3
    python -m research.doom.v39_release_trace_completeness_posthoc_a01_20261008.run_audit_v3

AUDIT_V3.json is the versioned output. RESULT.json and AUDIT.json remain
unchanged.
