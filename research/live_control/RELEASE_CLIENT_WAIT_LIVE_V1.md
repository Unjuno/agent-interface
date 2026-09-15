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
300ms. All31 source hashes and output absence verified on Windows/WSL before the
allocation ran once.

The runtime result is descriptive but the formal allocation fails. The early
client returned2.672ms after focus request; terminal-only returned113.116ms, a
110.444ms difference. Early terminal reconciliation completed113.895ms after
focus. The same release/terminal records, one real post-release observation,
smaller early response and2-vs-1 exchanges were retained.

However, the runner checked both server reads were registered before focus using
an in-memory request list and saved only the boolean outcome. It did not serialize
the server request receipts or their `received_ns`. The frozen independent audit
therefore raises `KeyError: 'received_ns'` and cannot reproduce that preregistered
ordering. Client start times cannot substitute for server acceptance. The first
result is retained as `server_request_registration_receipt_not_serialized` with
14 files/253,759 bytes and no retry. Cross-platform failure-retention audits pass.

The repair is narrow: persist the exact request receipt list before focus, bind
both request IDs, and make the independent audit consume that file. Freeze a new
allocation; do not reinterpret or rerun this one.
