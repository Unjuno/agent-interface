# Actual cross-host live construction, not a provider/scientific allocation

Parent #5260; original A12/A13/A14 results remain immutable. Latest GitHub MCP
main observed c730c06adee0b9e6fd6d02226e5d71e313ea5299, incorporated locally in
8e0cbff10668e026cdf8485f62a00f48073d083b. Scoped comparison from c58f through
c730 found no changes in selected shared X11/CLI implementation, current goal,
or roadmap. This owned additive path has no competing remote branch/open PR.
Refresh ownership/source again before the formal freeze.

## What now actually ran

`file_exchange.py` adds an actual standalone host service and client. Container
requests contain only allocation/freeze/slot/nonce/image/prompt hashes, never
commands or host paths. The trusted host plan selects argv. Actual --image
file, prompt, schema, executable and argv hashes are retained before and after
the process. First process stdout/stderr and parsed answer remain unchanged
even on later artifact drift. A returned original response is re-parsed by
the client, then joined to the host parser result. The client records receipt
in its own monotonic domain; Windows host clock values are never used as Linux
app freshness boundaries.

Exclusive payload writes close/fsync before a complete ready marker. Readers
wait on absent/incomplete markers and check length/hash before consumption.
This is validated once-only cooperative publication, not atomic filesystem,
crash-durable, authenticated sensor, or hostile-peer isolation proof. Completed
invalid request seals consume/STOP the whole host phase. Completed invalid
response seals consume the client slot even if original bytes are restored.
Finite host polling and existing bounded owned-tree process cleanup remain.

Cross-host construction c01 used a real Windows standalone host with an
explicitly synthetic Python response process (2.8s artificial wait), and a
WSLc client/private live Tk app. Image came from exact RGB handoff of the actual
shared native capture, not a generated substitute. The host read the actual
PNG and exact prompt, returned original process bytes through the mounted
directory, and the client used its local response_seen_ns for a NEW app
snapshot and TaskSession admission. Actual shared guarded Ctrl+S produced one
exclusive ordinary task file, with matching text qmd/PID/token, target-directed
Control/S press+release events and empty decoy. No source/API changed the task
text or called the Save callback directly. The cooperative initial qmd state
is controlled construction stimulus, not native typing or model semantics.

Both host and container processes exited0; external-host test PASS. Actual
synthetic process time2.8988258999888785s is not provider latency or speed.
PNG/capture PNG SHA256 f9942edb9b53f0f0734b0a03372173b32ed38def87baea720bf4d5d8838bf3ba.
File SHA256 a4d870f2943f4be0612c2695d45081ff24484ee66628e1b9c4acdd24a707ff15
matches the app's saved receipt and independent direct hash of file bytes.
Client response_seen_ns10550338297; first review app acquisition starts later;
first native-save check starts10612849228. These are same-container clocks.
Outcome SAVE_DISPATCHED and task_complete=False; candidate is not the final
formal task scorer. All73 original c01 files retained byte-for-byte under
cross-host-construction/c01, including process logs, actual image, original
response, app event/save trace, native capture/admission/release records and
file. Copied original absolute /tmp paths remain historical; the retained
relative directory mapping does not claim those paths still exist.

c01 ran BEFORE both later seal lifecycle fixes. No frozen source archive was
made at c01 invocation, so do not relabel it as final-source/formal provenance
or reconstruct an alleged original source capsule. Its actual first outcome
and bytes remain unchanged. Final source validation is the later unit/native
construction suite, not an invented c01 rerun.

## Failure-first checks and independent review

First six exchange tests failed because implementation was absent. Standalone
host test then failed because a successful no-op script published no response;
finite service implementation corrected it. Read-only reviewer Godel identified
completed request-seal failure outside STOP handler. Actual filesystem RED
confirmed stopped=False; new handler and same/different-slot regression fixed
it. Analogous client response-seal RED confirmed received=set after rejection;
exceptions now consume before propagating, with restoration/retry denial test.
No failed formal/provider allocation was rerun or discarded.

Fresh Windows28/28 PASS (9 exchange +11 host +8 predicate). Final pinned Linux
qualification08:42 tests,41 PASS +1 explicit external-host SKIP, exit0;
13.420s unittest time and18.2103743s outer wrapper are separate clocks/scopes.
The external-host case was actually run separately as c01, not counted as
passed in this default suite. qualification06 and07 preserve earlier38 and
40PASS+1SKIP checks respectively, with original attempt/receipt/raw streams.
Related existing shared regression02:79/79 PASS across mcp_guarded,
input_dependency, deadline and post_dispatch_capture; existing doubles/stdio
checks are not another model/game trial. Pillow getdata deprecation warnings
and original WSL swap/cgroup warning remain retained. No full-repository suite,
memory enforcement/OOM relief, hardware atomicity, or production adoption claim.

Same read-only reviewer inspected corrections and selected c01 originals,
concluding Critical0/Important0/Minor0 and ready for next construction. Reviewer
did not independently execute Windows/Linux suites. Its verdict preceded final
qualification08, now independently captured by the coordinator. Actual model,
matched pairs, semantic recovery and full independent formal raw audit were
explicitly declined as future work, not dropped requirements or stop reasons.

## Next required actual scientific step

Keep DESIGN.md's matched image-only versus current-task guard comparison, with
the same first actual model answer shared across independent pixel-identical
arms, rather than replacing it with only a transport study. Construct the
finite paired schedule and independent result auditor: intact, missing-prefix,
wrong-recipient and post-model focus drift; fresh payloads, source/dependency
closure, actual desired files, initial images, exact requested model/effort,
prompt/schema/argv, conditional changed-evidence recovery and stop rules.
Choose an actual end/skip protocol for unneeded optional recovery slots before
formal service use; the current service waits for every configured slot and
therefore is not the complete conditional-pair driver. Preserve first answers,
count shared first cost once and recovery separately. Freeze and prospectively
record H/T/D/C/U before the first actual provider call. Audit original input,
release, freshness, file, false-completion/wrong-target and safe-unfinished
outcomes independently, then review/CI/PR/main as one meaningful delivery.
No A15 formal freeze/allocation/provider call/PR exists yet; full roadmap open.
