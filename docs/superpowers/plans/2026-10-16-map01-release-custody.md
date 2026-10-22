# MAP01 unverified native-I/O custody

Base `8961cc8f61e0dbf65f832f6e7a067c79dce4bbaa`. Fake X only; no live resource.
Continue the repository convergence/control goal under existing user delegation.

Question: when native input send/sync/readback stalls and the owner request wait
ends unverified, does the actual selected backend/Executor retain that obligation
and refuse a later admission? A failed terminal is not verified physical release.

1. Inject four finite stalls on actual V12 primitives through selected backend,
   V4 and Executor: first press send, release send, release sync, release readback.
   Preserve first RED. Distinguish fake-held from fake-neutral/unconfirmed state.
2. If demonstrated, retain a deep-copied unverified release obligation in Executor
   before terminal publication and refuse subsequent work before validation,
   source binding, ID consumption or accepted publication. Do not auto-replay,
   clear from an unrelated observation, or synthesize successful recovery.
3. Check original failure/custody and late completion without new positive input;
   healthy verified cleanup must still permit ordinary subsequent work.
4. Run affected normal/-O checks and available read-only review, retain conditions,
   raw and limitations; integrate exact source and clean only own refs.

Limits: this fences reuse of this Executor, not a new process/session on the same
display. It neither interrupts native I/O nor bounds physical release. No task
effect/recovery/efficiency result follows. Preserve backend/owner custody for
cleanup; stopping the caller must not be reported as releasing input.
