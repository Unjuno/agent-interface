# X11 repeated-key observation: release events, current state and text effects

## Disposition

**PASS_X11_REPEAT_RELEASE_BOUNDARY_SCOPED**, supplied execution-container evidence.
One locally source-frozen allocation,15 fresh Tk Entry sessions,30 paired observer
views, three predeclared batches. Formal retries/replacements/source changes:0.
This is research evidence, not a current-runtime fix or product acceptance.

**Publication: STOP_GITHUB_WRITE_ACTION_UNAVAILABLE.** No GitHub Issue, branch,
commit or PR was created, and nothing was merged or deleted. Account metadata
reports push/admin permissions; the limitation is this session's48 exposed
read-only MCP operations, absent gh CLI and failed container GitHub DNS. The
complete patch/archive is for later retrospective publication, not a claim that
GitHub holds these bytes. See PUBLICATION_STATUS.json.

## Primary result

Counts below are totals over three fresh sessions per condition. Both observation
connections saw exactly the same physical XTEST input and Entry target in each
session. “Down” means the server keymap at the explicitly bracketed query sample,
not a hardware switch measurement or a reconstructed event-time state.

| Condition | Authored down/up pairs | Native presses per connection | Legacy KeyRelease / sampled DOWN | Detectable KeyRelease / sampled DOWN | Actual Entry characters |
|---|---:|---:|---:|---:|---:|
| No input | 0 | 0 | 0 / 0 | 0 / 0 | 0 |
| Short20ms hold | 3 | 3 | 6 / 3 | 3 / 0 | 3 |
| Long320ms hold, repeat on | 3 | 33 | 36 / 33 | 3 / 0 | 33 |
| Long320ms hold, repeat off | 3 | 3 | 6 / 3 | 3 / 0 | 3 |
| Two short taps | 6 | 6 | 12 / 6 | 6 / 0 | 6 |
| **Total** | **15** | **45** | **60 /45** | **15 /0** | **45** |

In each enabled long hold, a single authored down/up pair inserted exactly11
'a' characters. Detectable-repeat mode changed the observer's release-event
representation; it did not suppress repeated presses or the application's
ordinary text insertion. All45 characters remain real effects after every key
was released; physical neutrality is not “one requested character” or rollback.

The45 DOWN release witnesses must not all be called periodic repeats. Fifteen
are onset-compatible release/press pairs, including short and disabled-repeat
controls, in this XTEST/Xvfb stack. Thirty are later same-hold repeat pairs.
Every DOWN release precedes the authored release, has a same-server-time following
press, and has an actual current-keymap DOWN reply. The root cause of the onset
compatibility shape is not isolated here. No novel X11 defect is alleged.

## H / T / D / C / U

**H:** legacy release-event counts need not represent physical neutralization;
per-client detectable negotiation changes that observation boundary, while
application effects remain separate. Known X.Org semantics motivate the test.

**T:** private authenticated TCP-disabled Xvfb; Tk Entry stock class bindings;
one controller and two native libX11 observer processes per session; five input
conditions ×three repetitions with cyclic condition order. Delay80ms and repeat
interval25ms explicitly configured/read back. The app supports only read-only
snapshot and close IPC. Whole allocation is finite and synchronous. No previous
#1001/#651 experiment, shared runtime, real model, provider or user desktop used.

**D:** complete15 sessions/30 views; all paired press times and actual Entry values
reconcile; no detectable release sampled DOWN; all controls discriminate;
all final/cleanup keymaps empty and buttons neutral; all45 app/observer exits,
15 config exits,3 runner exits and3 Xvfb exits observed0. Final read-only check
finds all66 recorded owned PIDs absent. This is not arbitrary-tree containment.
Raw audit v2 passes3773 checks, errors=[];13/13 semantic/provenance corruptions
reject after each unmodified relocated baseline first passes. The frozen original
audit passes3767 checks on its original path; see the retained limitation below.

**C:** one software X server, one ASCII key, one Tk Entry, actual synthetic XTEST
input. The negotiated repeat flag belongs to each client connection, not all
clients. Tk's own flag was not read. The experiment neither changes production
runtime nor establishes a general release collector. Current queries remain
samples; event-only detectable observation is not promoted to timeless authority.

**U:** no hardware keyboard, arbitrary grabs/focus change, reconnect, other
backend/application, real model/task utility, tokens, speedup, natural error rate,
power failure or product reliability. Three repetitions are finite coverage.
Software clocks and host scheduling are not calibrated; no statistical or
hard-real-time inference is made.

## Retained construction and auditor failure

Construction01 configured repeat before a persistent client existed and observed
no periodic repeats during250ms. Possible server-reset attribution was not
independently proved. Construction02 configures after Tk startup and observes8
characters from one250ms hold, with80/25ms readback on both observers.
Construction03 repeats excluded setup under the final supervisor and has a clean
raw audit. All three remain excluded. Original source versions and raw records
are retained, including missing external monotonic brackets in construction01/02.
No retrospective timestamps were fabricated.

After the formal experiment, moving intact evidence exposed a bug in the frozen
auditor: it compared historical absolute command paths against the extraction
location. The original failed relocation and original passing audit remain intact.
That same path check also confounded the preformal12 mutation rejections, so those
are NOT counted as validated mutation sensitivity. The separate postformal
`audit_v2.py` changes only path/command provenance validation, retaining every
scientific gate. `test_audit_v2.py` now requires each clean relocated copy to pass
before mutation; all13 changed copies then fail at their expected semantic or
provenance boundary. No formal case or frozen source was changed or rerun.
See AUDITOR_CORRECTION.md and retained FROZEN_AUDIT_RELOCATION.*.

## Concrete integration decision

For #57/#2789-style bounded-hold/release reporting, retain at least three distinct
claims: client event evidence and its negotiated mode; server key state at a
recorded sample; application result/effect evidence. Do not count every received
KeyRelease as neutralization or infer a single effect from one final release.
Enabling detectable repeat on an auxiliary observer does not alter the app or
another legacy connection. Before a runtime proposal, inspect the actual current
collector/client mode and revalidate through the integrated guarded-input path.
This result neither closes #57/#2789 nor completes ROADMAP.md.

## Source, provenance and offline reproduction

Intake main1f798cbb60b929e738c6bf8a5912470b38b45ff4; final main readback
4f87a5f1339b71476cb753694389eea64fa016b4. The proposed namespace returned404 there.
Branch/Issue reconnaissance is bounded and non-atomic; unpublished parallel work
is unknown. No older or other-worker branch/path is touched.

Freeze:2026-09-21T21:17:43.239208Z (September22 06:17:43 JST), before batch0.
FREEZE SHA256:1823c4e0e34c4d72b1e4dced1d1f0b0ad7579ae851ad9c21a92d67b9c660de59.
The freeze was LOCAL ONLY, not publicly registered on GitHub before measurement.
Full source/environment/plan hashes are in FREEZE.json; complete raw file hashes
in FORMAL_MANIFEST.json. No claims of a full repository checkout, whole-repository
CI, outside human review, or Docker/OrbStack image replication.

From the restored study directory, run only read-only verification:

```sh
python -B verify.py
```

It checks the delivered SHA256 manifest and formal raw manifest, invokes the
portable raw-only audit and compares its output byte-for-byte, then checks13
negative controls. It never imports the GUI/controller/native experiment.
Do NOT rerun consumed `run.py`/`execute.py` formal allocations. Any new experiment
needs a separate explicitly justified allocation and newly frozen contract.

Primary protocol source: X.Org libX11/XKB specification, RepeatKeys and
DetectableAutorepeat sections:
https://xorg.freedesktop.org/releases/X11R7.6/doc/libX11/specs/XKB/xkblib.html
Known per-client semantics are context, not a discovery claim or an endorsement
of event-only release as a production authority boundary.
