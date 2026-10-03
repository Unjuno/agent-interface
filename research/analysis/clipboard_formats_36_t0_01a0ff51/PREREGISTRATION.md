# #36 multi-representation paste T0 — prospective protocol

Worker `01a0ff51-d447-7cb3-bb02-36d7e1d30b28`, policy FINAL-v5.
Allocation `CLIPBOARD-FORMATS-36-QT-T0-20261003-01`.
Dedicated branch `research/clipboard-formats-36-01a0ff51-20261003`.
This tests #36's 2026-10-02 refinement; it retries no historical allocation.

**H.** A plain summary digest plus a resource epoch cannot distinguish every
wrong saved rich/plain effect. Per-format metadata catches representation
changes, but cannot alone establish target formatting. A format-request trace
plus a saved-effect check may discriminate remaining cases. The strongest simple
alternative is the same manifest gate plus an exact saved-effect check alone.

**T.** Twelve frozen cases, one actual Qt `paste()` per case in an offscreen
QApplication. QTextEdit/QPlainTextEdit are real toolkit targets; deliberate
plain preference and bold stripping are two declared fixture subclasses.
No OS keyboard/pointer input is emitted. Each case starts with a new widget
and QMimeData. Ordered UTF-8 text/plain and text/html representations, owner,
generation, target policy, attempted paste, task text/style contract and format
visibility are in cases.json; oracle.json additionally names the scenarios.
Save both `toPlainText()` bytes and `QTextDocument.toHtml()` bytes immediately.
Candidate measures document formatting through Qt. An independent stdlib auditor
parses saved HTML and reconciles text, digests, roster, metadata and judgments
without importing Qt, candidate.py or gates.py.

Four *diagnostic judgments* share each actual saved fixture outcome: summary
metadata; complete format manifest; manifest plus request-trace/effect; manifest
plus effect only. These are not four live controllers and their judgments do
not suppress the diagnostic paste. ELIGIBLE is a pre-effect dependency result,
never a task-success verdict. Post-effect rejection cannot undo a wrong paste.
Requested MIME data is not independently proven to be the exclusively consumed
representation: the recorder check and the saved-state oracle are distinct.

**D.** PASS_METHOD_SCOPED requires the exact 12-case roster, zero independent
audit errors, and all ten mutations rejected for their *specific* required
reason, rather than any pre-existing error. The mutations are omitted case,
HTML digest corruption, boolean epoch, fabricated format request, fabricated
bold effect, promotion with missing format visibility, fabricated paste attempt,
synthetic content in the planner view, saved hash corruption and owner relabel.
All five seeded wrong-content/style cases must be refused or detected by the
manifest/effect judgments; C09 has NO_EFFECT, C12 has HOLD_RESOURCE. An unseen
format request is HOLD_FORMAT for the strict request/effect judgment, even when
the saved effect is correct. The effect-only alternative may accept that effect.
If it detects every seeded wrong effect and accepts at least as many valid
effects, do not require extra format visibility in this fixture. Any changed
source/image, output collision, process failure or audit disagreement is retained
as STOP/FAIL; the formal candidate and auditor each have at most one invocation.
No post-result threshold changes or rerun. Construction is separate and retained.

**C.** Full effect verification may already be sufficient, and plain-only paste
can be the appropriate task policy. QByteArray retrieval does not prove semantic
suitability or exclusive format consumption. The planted subclasses make the
failure modes known; this is conformance evidence, not a natural failure rate.

**U.** One Qt 5.15.13 / PyQt 5.15.10 Linux arm64 offscreen fixture, one item with
two known UTF-8 representations and uniform styling. No native/X11/macOS
clipboard-manager behavior, browser paste, focus/race/expiry/handoff/duplicate
delivery, physical release, model utility, latency benefit, general privacy or
production authority claim. Synthetic content is intentionally present in local
fixture/evidence files; only the specified planner metadata view omits its bytes.
Low-entropy digests can still leak information. No live format-consumption receipt
or safety guarantee is established. The full #36 promotion gate remains open.

## Environment and invocation

The final image ID is
`sha256:9e9b1a232f08b8c437834f8a40a5b39ca4be9c66b953833170930c70fdc66d89`.
Dockerfile pins the Ubuntu base digest. Final package versions, full image
inspection, Docker/guest and macOS hardware records accompany the run.
Dedicated guest/Engine: `research-clipboard-36-01a0ff51-docker`.
This is an ordinary OrbStack guest with standard macOS integration, not a host
security sandbox. Its private Engine is separate from the shared engine and
every existing worker machine. The experimental container has network none,
read-only root/source, a private 32 MiB /tmp, only this task's output bind, no
privileged option, 0.25 CPU, 256 MiB memory and 64 process limits. Construction
observed cgroup files memory.max=268435456, cpu.max=`25000 100000`, pids.max=64;
these are guest/container settings, not a measured host memory-pressure guarantee.

Freeze the source commit plus SHA-256 for candidate, gates, auditor, cases,
oracle, tests, Dockerfile and this protocol before invocation. The external
FREEZE.json is a run record and is not part of its own source hash.
Fixed source pins remain the execution authority when unrelated main changes;
do not refreeze or rerun because the fleet adds unrelated evidence. Refresh
dependencies and ownership before any later integration.

Run the candidate once in a fresh named container and then, only on candidate
exit 0, run the auditor once in another named container with candidate output
mounted read-only and a separate writable audit directory. Preserve raw,
saved documents, stdout/stderr, command arrays, process/container exits,
pre/post source checks, ISO UTC start/end records and artifact hashes.
Elapsed_ns uses Python monotonic_ns solely as a diagnostic duration; no
comparative performance endpoint is inferred. No randomness or sample pooling.
All ten local tests must pass. Check the existing analysis index using its
sparse-aware entry point, add exactly one sorted retained-result link, and run
diff/compile checks. No workflow or runtime source is changed.

## Construction history and continuing gates

The first image build stopped on the isolated guest's BPF/cgroup restriction.
The separate ordinary guest built the final image. Construction01 emitted 12
rows but the initial auditor incorrectly predicted no MIME request for empty
data; Qt actually queried text/plain before inserting nothing. Preserve that
audit FAIL and the exact old sources. The final-source construction02 reconciles
all 12 rows with ten specific-reason mutation rejections. These are development
checks, not extra formal allocations. Formal outcome is initially unobserved.
Common fleet deadline remains unconfirmed; this finite allocation neither sets
nor extends it. Main publication requires FINAL-v5 nonauthor content agreement,
current-base integration review, actual protection rules and conditional apply.
