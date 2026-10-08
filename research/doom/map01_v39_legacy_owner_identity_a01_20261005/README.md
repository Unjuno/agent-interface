# Legacy owner identity projection A01

This additive experiment checks whether the current #7602 V39 measurement projection fails closed when a legacy release row contains conflicting owner identities.

On exact PR head `958dbe99bd27e916ba22a523a1c2c7bbbaf4fc35`, an unchanged retained V39 admission/release pair projects to `paired`. Mutating the release transition and/or nested `owner_thread_keyup_receipt` to another owner still produces `paired` with a non-null `input_ack_to_owner_keyup_start_ms` of `106.742801`. A small successor projection guard rejects four explicit-conflict/partial-ID mutations and leaves a wholly ID-free legacy fixture compatible.

Run 01 stopped at a bad path after starting the container but before invoking the candidate. Run 02 executed the case matrix but failed while collecting hashes and retained no candidate JSON. Run 03 is the recorded result: six cases in the pinned offline OrbStack container; candidate exit 0 and separate raw-only auditor exit 0, zero mismatches. The exact source and witness event pair, two prior failure records, command, logs and hashes are retained under `SOURCE/` and `results/`.

The candidate guard is a scoped diagnostic successor, not yet applied to PR #7602. The evidence reuses one retained V39 event pair and does not establish a new runtime event, physical key state, application feedback, recovery, threat control, or MAP01 progress. The per-key live allocation remains separately unassigned.
