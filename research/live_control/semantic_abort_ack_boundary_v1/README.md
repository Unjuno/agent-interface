# Live application abort acknowledgement boundary — Issue #3930

**Result: `PASS_LIVE_ABORT_ACK_BOUNDARY_SCOPED`.** One frozen allocation, 18/18 live cases, zero reruns. The deliberately unsafe request-received reporting policy separately **fails false-abort reporting in 3/3 controls**. This is an application-specific Tk/XTEST research result, not a production runtime or model result.

Origin: closed [#771](https://github.com/Unjuno/agent-interface/issues/771); related [#706](https://github.com/Unjuno/agent-interface/issues/706) and [#2197](https://github.com/Unjuno/agent-interface/issues/2197). All predecessors remain unchanged. Full model/live-transfer acceptance in #2197 remains open.

## What was actually tested

A separate Tk process exposes an ordinary Button whose unmodified class-bound command increments a private counter and changes a black marker to white. Its explicit **application-specific** cancellation operation disables that button. This is not a generic Tk Escape/cancel capability or document rollback.

The controller sends real XTEST pointer events to a fresh, authenticated, TCP-disabled private Xvfb server per case. A separate X connection observes server button/key state and exact marker pixels. Pipes carry application request-received and applied acknowledgements. Barriers deliberately order application cancellation before or after ordinary button release; no natural race probability is inferred.

| Scenario (3 fresh cases each) | Callback counts | Candidate at release |
|---|---:|---|
| Normal completion | 1, 1, 1 | Completion unverified until effect observation |
| Current application-applied ACK before release | 0, 0, 0 | Abort applied; final abort also requires zero effect |
| Request-received ACK; apply only after release | 1, 1, 1 | Query effect |
| Applied-ACK timeout | 1, 1, 1 | Query effect, release still mandatory |
| Unsupported abort, refused before input | 0, 0, 0 | Refuse; zero task presses/releases |
| Genuine applied ACK from another session | 1, 1, 1 | Query effect, release still mandatory |

All 15 input-bearing cases released; all 18 terminal/cleanup server queries were neutral. All 18 application and Xvfb processes exited zero. Exact pixels and callback journals agree. The independent raw-only auditor reconciled the full denominator, identities, response-before-release ordering, effects, source hashes and exits; errors empty, 14/14 corruption controls rejected.

## H / T / D / C / U

**H:** An application-received cancellation request does not establish applied cancellation. A current application-applied acknowledgement before release distinguishes the cancellable case; absent or foreign proof must not become semantic-abort success, and must never suppress mandatory input cleanup.

**T:** Fixed repetition-major order of six conditions, three fresh processes/servers per condition (18 cases). Exactly one formal invocation. The six-case construction and all preceding construction STOPs are excluded. Source, schedule, environment and audit hashes were posted on #3930 before invocation.

**D:** The full frozen gates are in `PLAN.json` and #3930. Require correct positives, zero callback after applied-before-release, committing request-only controls, no false candidate abort, preserved mandatory release, zero input for unsupported abort, exact independent evidence and corruption-control agreement. Integrity failure or partial execution cannot be promoted to PASS. The unsafe control's FAIL remains distinct from the scoped boundary PASS.

**C:** Application-specific disable; default Tk Button release handler retained. Barrier-selected order, not random racing. XTEST, not XI2 touch or kernel HID. The standalone auditor is a separate implementation/process, not a separate human or independently instrumented machine. Journal and pixels expose the same fixture command, not real-document rollback.

**U:** No model calls or decision-quality test, production runtime integration, token saving, latency benefit, broad GUI rollback, Docker/OrbStack equivalence or cross-platform support. There is no attested container image/network-none boundary. Only the owned private Xvfb servers receive input. The full repository roadmap remains open.

## Evidence and reproduction

- `study.py`: exact frozen controller/receiver source.
- `audit.py`: exact frozen standard-library-only independent auditor; does not import the study, Tk or Xlib.
- `PLAN.json`, `FREEZE.json`, `ENVIRONMENT.json`: fixed schedule and source/environment identities.
- `AUDIT.json`, `EXECUTION.json`: formal audit and actual command/exit.
- `CONSTRUCTION.md`: retained first STOPs and pre-freeze corrections.
- `EVIDENCE.part01` through `EVIDENCE.part04` (one XZ archive split only for byte-exact MCP publication): byte-preserving formal aggregate raw JSON (including every per-case receiver journal, request/response wire, pixel buffer, state and stderr), construction raw/source snapshots, and stdout/exit evidence. Duplicate per-case ROW serializations are omitted from this archive; the aggregate embeds their full evidence. Active authentication files are not research evidence and are excluded; all owned servers have terminated. `EVIDENCE_MANIFEST.json` hashes every part, the reconstructed archive and every archived member. The extractor joins the parts automatically.

Verify and unpack the retained evidence into a **new** directory with `unpack_evidence.py`. It rejects links, absolute/traversal paths, duplicate names and overwriting an existing directory. Then audit without GUI, model or input:

```sh
python unpack_evidence.py --out /tmp/issue3930-retained
python audit.py /tmp/issue3930-retained/results/semantic-abort-ack-20260922-01/RAW.json --freeze FREEZE.json
```

A future live replication needs a new Issue/allocation ID and a fresh source/environment freeze. Do not invoke the frozen formal command again or overwrite its output. `freeze_environment.py` is the retained one-shot metadata collector, not a replication setup command. No dependency installation is performed by these files.

## Bounded roadmap / integration handoff

Intake and predecessor reconstruction → excluded live construction → public hash freeze → one 18-case formal allocation → raw-only audit and corruption controls → additive evidence PR → main readback when merged.

The concrete integration requirement is to separate **cancel requested**, **application abort applied**, **physical input neutral**, and **effect observed**. Only a current action/session-bound application-applied acknowledgement can support the applied state, and the semantic outcome still needs effect evidence. Timeout or stale proof must yield/query effects after mandatory cleanup. Adoption requires a separately reviewed real-runtime mapping; this PR changes no production behavior and closes no broad parent issue.

Formal raw SHA-256: `2c7c7aedcc9d933d7d2159fea0cc3750abf94b332baa7d4440f4694d831112c2`.
Freeze SHA-256: `bf11795b5dfb52785d0ddf7c3b9d212ae6861eca9acb7b7879804e21721f2586`.
