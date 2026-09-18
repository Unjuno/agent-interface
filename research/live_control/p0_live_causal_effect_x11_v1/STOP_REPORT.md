# #1287 preformal setup stop

Disposition: `PREFORMAL_SETUP_STOP_TK_XSERVER_TEARDOWN`; scientific disposition **NONE**.

- Exact source/dependency static gates passed before live.
- Finite #60 lease granted construction budget2, formal1/reruns0.
- Construction invocation began, but no aggregate construction result was written.
- Python/Tk emitted XIO fatal on display `:1900` during multi-session teardown/transition.
- Two case directories existed; `:1901` Xvfb remained after process termination and was explicitly cleaned.
- After cleanup: related process0, private display socket0.
- No memory-only session row was reconstructed or promoted.
- Formal invocation0; reruns0.

Source inspection suggests server/client lifetime coupling between sequential Tk sessions is the next harness discriminator. A successor must preserve same-process owner/effect/scorer semantics *within each session* while changing only session isolation/teardown so all X clients exit before the private Xvfb server is terminated.
