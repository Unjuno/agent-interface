# #36 native multi-format transport transfer, fixed before formal execution

Study ID: CLIPBOARD-36-X11-MULTIFORMAT-TRANSFER-20261003-01.
One candidate container followed by one separate raw-only auditor, no retry.
Source/image/launcher/auditor/cases hashes and fresh output identities are fixed
in formal/01/FREEZE.json before either invocation. Construction is separate.

H: The previously observed representation/effect distinction transfers across
separate owner and consumer processes through native X11 clipboard transport.
A text/plain digest can match intended Robin while native rich paste produces
Quinn from text/html. This is a transfer/conformance question, not a new Qt
mechanism or performance claim.

T: Four fresh, stable-payload cells, one per authored condition, in fixed order:
N01 rich matched control; N02 plain matched control; N03 rich with plain Robin /
HTML bold Quinn; N04 plain with plain Quinn / HTML bold Robin. Every cell has a
new allocation-owned Xvfb, Qt owner and standard QTextEdit/QPlainTextEdit
consumer. No writer changes occur during a cell. Actual xclip reads preserve
both MIME byte strings. Actual XTEST Ctrl+V is directed at the focused consumer;
no consumer insertion API is called. Save text, Qt HTML, screenshot, separate
owner MIME-request/consumer key-change journals, native owner/focus/keymap,
all native command results and process exits. The stdlib auditor imports no
candidate/Qt, reconstructs text/uniform bold and checks14 specific corruptions.

D: PASS_X11_MIME_TRANSFER_METHOD_SCOPED requires all4 cells with expected native
effects: Robin bold, Robin plain, Quinn bold, Quinn plain; matched controls
correct and both planted conflicting effects wrong for the intended Robin
task. Summary diagnostics admit N01/N02/N03; full-format diagnostics admit only
N01/N02. These diagnostics do not gate the four actual pastes. All14 frozen
corruptions must reject for their named reasons. Require native xcb, distinct
owner/consumer/server process IDs, exact transferred bytes and saved/hash
agreement, paste-phase expected MIME getter, actual key-release records,
unchanged native owner/focus during paste, final neutral keyboard/owner0, and
all owned process exits0. Joined hashes cover all11 per-cell artifacts; raw
row records are separate to avoid self-reference. Source hashes must remain
equal before/after. Candidate failure/timeout stops the remaining cells and is
retained; no replacement, repetition, pooling, or post-result gate tuning.
Audit mismatch or different native representation is FAIL/UNCERTAIN, not a
reason to rerun the consumed candidate. Missing infrastructure/record is STOP.

C: Ordinary widget MIME preference and exact post-effect verification explain
the result. A complete saved-state comparator may suffice; no new authority
layer is proposed. Both representations are deliberately inconsistent in the
negative controls. Source getter logging is consistent transport evidence,
not proof of exclusive consumed-MIME semantics. Post-effect checking cannot
prevent or undo the deliberately executed wrong effects.

U: Four development-known authored cases, two toolkit widgets, one Linux arm64
image and synthetic ASCII. Not native macOS, real user clipboard, arbitrary
cross-app semantics, model utility, natural races, latency/speed, security,
privacy, runtime safety or completion of #36/#2774/#57. The prior consumed
27-case #3981 same-owner admission experiment remains evidence-incomplete;
its mid-admission mutation/serialization schedules are not executed here.

Resource/environment: own dedicated OrbStack guest/private Engine, not a host
security sandbox. No host X socket, clipboard, GPU, model or shared GUI lease.
Container network none, read-only root/source, own output, CPU0.5,512MiB,
128pids, private /tmp64MiB. Actual cpu.max50000/100000, memory.max536870912 and
pids.max128 are recorded and required. This is a cgroup setting observation,
not a host-pressure or adversarial enforcement test. Other host workloads are
uncontrolled; monotonic timestamps are diagnostic, not comparative latency.
Each application/native command reply has a5s timeout; orderly child cleanup
has5s then recorded owned-process kill. The first incomplete cell stops the
remaining cells. Retained output cap1MiB, checked without truncating evidence.

| Symbol/field | Meaning | SI unit | Domain/type and scope |
|---|---|---|---|
| id | frozen cell identity | none | string N01..N04 |
| plain/html | supplied representation bytes | byte B | UTF-8 synthetic strings |
| display / XID | own X-server scope and native object identity | none | display string, positive integer XID scoped to that server |
| pid | observed namespace process identity | none | distinct positive integers; bool/float forbidden |
| monotonic_ns | diagnostic time on one guest clock | ns | positive integer, ordered; no latency claim |
| keymap | XQueryKeymap keyboard state | none |32-byte bitmap; final all-zero required |
| eligible/correct | metadata diagnostic / saved-task effect | none | distinct boolean facts, no authority |
| cpu.max | cgroup budget/period | microsecond |50000/100000, ratio0.5 |
| memory.max | observed memory setting | B |536870912 integer bytes |
| pids.max | observed process/thread count bound | none |128 integer count |

Construction: first command stopped before run.py because inherited Python
entrypoint was specified twice. New image explicitly clears entrypoint/CMD.
Construction02's first Setup paste and source bytes remain unchanged; it did
not have the later joined per-cell manifest. Construction03 verifies the
final recorder's joined hashes/display/cgroup additions on the same ordinary
Setup fixture. Construction cells never augment the four formal counts.

Qt clipboard transport is established behavior, including the X11 event loop:
[official Qt QClipboard documentation](https://doc.qt.io/QT-6/qclipboard.html).
This reference explains the system analogy; the pinned tested library is Qt5.
