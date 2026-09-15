# Early release client wait comparison v1

The runtime now publishes physical release before terminal in keyboard and pointer
cases. This experiment asks whether a real client can consume that distinction,
rather than merely finding it later in the raw log.

A private Unix socket exposes a bounded non-consuming event cursor. Two read-only
clients register before the same actual Inkscape held-click focus fault. The
early client waits for `input_released|terminal`; the baseline client waits only
for `terminal`. Both see the same accepted action and runtime stream. After its
early reply, the first client makes one second exchange for terminal. Therefore
the comparison retains both the safety-feedback wait and the explicit two-versus-
one exchange tradeoff.

After owner release, the backend performs one actual passive X11 screenshot,
exact encode/reconstruction and PNG publication before terminal. This represents
recovery evidence that may be useful but must not delay knowledge that input is
already safe. It grants no authority and does not infer readiness or task success.

The client tracker binds accepted token to verified empty release and requires
the later terminal interruption record to match. Wrong token, unverified release
or conflicting terminal enters reconciliation instead of a safe state. Unix
socket construction passes under WSL; pure state validation passes on Windows.

One seed211 held-click allocation is frozen with both reads waiting before focus
transfer, zero model/cancel/retry, one passive recovery observation, exact shared
boundaries and response-byte accounting. Frozen limits require the early client
within40ms, at least40ms before the terminal client, with terminal delivery within
300ms. All31 source hashes and output absence verify on Windows/WSL. Run once and
retain its first result without retry.
