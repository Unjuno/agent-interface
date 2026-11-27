# V39 cancellation failure boundary

Base `4215f75112c406fa4c6d57c8b7768c4f7ca6e4e0`. Fake X/local checks only.
The previous Executor custody repair does not qualify the outer controller wait.

1. Reproduce a matching failed terminal or unverified release being consumed while
   waiting only for `input_released`. Preserve first RED.
2. Consume matching cancellation/release/terminal boundaries explicitly. Preserve
   early release until cancellation ACK can validate it; never discard a terminal.
   Keep healthy token/clock/empty-state/lifecycle validation unchanged.
3. On unverified/invalid/wait/send failure, retain original matching events and
   guard receipt in a copied failure object. Save an exclusive failure receipt in
   the current run output before raising; secondary save failure preserves primary.
   No automatic resubmit, new authority or successful recovery is inferred.
4. Compose the helper with actual selected backend/Executor/V4/V12 and a stalled
   fake KeyRelease. Require failed-terminal classification and persisted custody
   while the key is still held and the native primitive has not resumed.
5. Run focused and affected normal/-O checks, review, preserve source/raw/limits,
   integrate exact source and clean only own refs.

This bounds neither write/flush nor platform I/O or physical release. An absent
event still uses the existing caller wait policy. Synthetic guard evidence and
Fake X do not establish perception, independent task effect or task recovery.
