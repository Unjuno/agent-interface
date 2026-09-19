# Native key repeat integration — pre-execution plan

Source idea: #2867, thin extension of the existing batch path. Base:
8576c0fd1d43aec861d0d7c9761c1a3bbc545caf. Scope excludes sensor development.

H: explicit repeat counts reduce repetitive caller JSON while compiling to the
same ordered native key operations, without changes to admission or input timing.
T: add optional repeat=1..126 to key_chord in the guarded native tail. Remove it
before dispatch and expand to independent ordinary operations. Reject invalid
counts/types, repeat on other operations and expanded tails over 123 operations
for click or 126 for keyboard (128-op native bound minus existing wrapper ops)
before input. Test exact equality to an independently built flat list, mutation
isolation, invalid/overflow cases and existing bridge refusal/release tests.
D: retain source snapshots, test output, flat/compact requests, expanded raw
program, primary-assistant images, saved SVG, release/cleanup, source hashes and
byte counts. Use one fresh Inkscape seed 991105 allocation with a viewed target,
50ms leading wait, repeat 18 Right, 50ms wait and Save; then explicit finish.
C: local compile gate passes only on exact operation equality and all refusal
controls. Live gate passes only with correct expanded order/count, reviewed image,
independent saved geometry, neutral release and terminal cleanup. No retry of an
unknown or failed input. Source changes after tests are construction changes and
must be revalidated before use. Infrastructure failure is STOP, mismatched
expansion/refusal is FAIL; absent model cost/latency evidence remains HOLD.
U: actual model token benefit, generalized usefulness, cross-app accuracy,
human-tempo or latency improvement. Byte reduction is not a token claim. This is
explicit within-program repetition, not retries, held input, a persistent queue,
scheduling, cancellation or completion of #2867.

Pre-test construction correction: source inspection found the native core's
128-op bound; use its remaining capacity rather than a separate 256-op limit.
