# Receipt binding for early and combined lifecycle reports

Receipt v4 required state=terminal and exactly two exchanges, so the actual early/combined Calc reports remained unverified even after terminal_received. decision_receipt_v5 adds a separate validator for that state. Pending states stay pending; it does not simply rename them or infer a terminal.

The validator checks a bounded 2..64 exchange history, contiguous received slices, read-only own-terminal followups, no interleaved command, reconstructed PendingAction equality, original terminal/final-reply copies, and a valid <=30-second admission horizon. It then creates an explicitly internal projection of the validated contiguous slices and reuses the existing clock/submit binding checks (exact command echo, distinct requests, source sequence, admission identity/count/deadline, final terminal and completed step count). The original source bytes, hash and indexed paths remain unchanged. The internal projection is not presented as an actual socket response.

On success, only the two root-level legacy warnings 'program binding unverified' and 'caller unresolved or reports reason' are removed, and the verified binding includes the recorded exchange count and projection meaning. Existing interruption, focus mismatch, nested errors, unknown event/report fields and task-success uncertainty remain. Lifecycle/outer-operation metadata still requires detail review; this is not a complete new report schema or authenticity/whole-image semantic validator. Input permission is unchanged.

## Evidence

results/receipt-lifecycle-01 contains eight archived live reports from calc-early-live-01 and calc-combined-live-01. Six completed lifecycle histories obtain verified bindings; the two early-only pending reports retain no binding. The probe checks unchanged source hash and terminal listings and retention of all other prior attention entries.

Twelve controls cover a command-bearing followup, cursor gap, foreign action, recorded read error, wrong terminal copy, invented lifecycle terminal status, missing source sequence, changed submitted steps, out-of-horizon deadline, missing admission, contradictory final reply, and preservation of an unknown nested error. The first eleven fail binding; the last retains a valid program binding plus visible error/unknown-field attention. Tests validate recorded consistency, not external provenance. No live source or prior measured result was edited.

## Adoption boundary

The result fixes binding compatibility for the completed early/combined reports. Client payload duplication and full report-field schema remain separate work, and existing live clients still explicitly import v4. Next use v5 in a new explicit client on a different desktop task/transition, keeping the same bounded followup behavior and preserving raw reports. Avoid another identical Calc timing run just to turn warnings green. No model speed, input token or cost saving is claimed by this offline change.
