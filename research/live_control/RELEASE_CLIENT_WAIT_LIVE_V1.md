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

## V2 repair allocation

V2 adds only the missing evidence boundary. After both server handlers register,
the runner copies their exact request IDs, requests and receipt clocks, writes an
fsync-complete `server-request-registration-v1` artifact, hashes it, and only then
requests focus transfer. The independent audit reads that artifact and requires
exactly `early-release` and `terminal-only`, both received before its snapshot,
with the snapshot before the fault. Client start clocks and the old boolean are
not accepted as substitutes.

A distinct seed210 allocation retains the same40/40/300ms timing thresholds,
same-stream comparison, passive recovery artifact,2-vs-1 exchange accounting and
zero model/cancel/retry rule. All32 source hashes and output absence verify on
Windows/WSL. Run once and retain its first outcome without modifying v1.

The allocation ran once and passed its frozen independent audit. Physical release
was verified20.519ms after focus request. The early client returned at22.369ms;
the terminal-only client returned at102.693ms, giving an80.324ms same-stream wait
advantage. The early client's second terminal exchange completed at103.641ms.
The exact two server receipts were fsynced before focus and bind to the retained
report by SHA. Twelve files/259,118 bytes before the retention receipt pass the
cross-platform retained audit.

This establishes one bounded client-visible safety-feedback benefit, together
with its2-vs-1 exchange cost. It does not establish task completion, model-token
savings, a general speedup or human-tempo control. The post-retention audit script
first failed because its author used wrong threshold key names; that script was
corrected and rerun on Windows/WSL. The live allocation was not rerun.
