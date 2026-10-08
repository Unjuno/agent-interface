# V39 interruption/cancel composition — A03

**Result: `PASS_CONSTRUCTION_SCOPED` (10/10 cases independently audited).** This deterministic probe composes the current-main V39 `cancel_invalidated_cover` helper with the current `PersistentPlannerAdapter`. It is one narrow integration boundary, not the #59 live threat-exposure experiment.

## Frozen question and method

At source main `f72cd82d62c9d9f3860d4fa40980c56618bf5aaf`, the hypothesis was that invalidation sends the matching planner interrupt and cover cancel, accepts only a permitted terminal disposition with verified empty release, discards any answer from the invalidated turn even if a completed answer arrives later, and allows a subsequent fresh same-thread observation turn.

The one-shot candidate used the real repository functions and deterministic in-process fakes. It covered three neutral terminal dispositions (`cancelled`, natural `completed`, natural `expired`), one interrupt-transport error, and six negative terminal/release conditions. Candidate output is [`candidate.json`](candidate.json); independently written reconstruction is [`audit_result.py`](audit_result.py). The original freeze is [`FREEZE.md`](FREEZE.md).

## Outcome

- All four eligible paths issued one exact turn-bound planner interrupt and one cover cancellation.
- The interrupted turn's deliberately late completed answer was ineligible and absent from the returned answer.
- Each eligible case admitted only the next same-thread answer produced from the fresh observation.
- All six invalid terminal/release controls were rejected.
- Independent auditor: `PASS: independently reconstructed 10/10 cases; 6/6 invalid terminals refused; stale turn rejected; fresh turn isolated`.

The preceding A01 and A02 attempts each stopped before candidate logic due to incomplete Python import-path bootstraps; their separate records are preserved unchanged under the sibling A01/A02 directories. Neither STOP was rerun or relabeled.

## Environment and scope

The host is macOS. Docker reported no running containers. `docker image ls` failed because containerd could not read a content blob (`sha256:6274b31351429a9cd2385f76c75c2df9f817c3dca6d285f4cd8ccceb88d8d1ad`, `operation not supported`), so no container started and no image was pulled. A03 ran once in the bundled Python runtime. The two earlier runner STOPs occurred before case execution and do not count as candidate outcomes.

This proves only deterministic Python control-flow composition. It does not test installed App Server behavior, external models, Doom, a GUI, OS input, physical key-up, useful task feedback, bounded recovery, ammo/progress, live threat exposure, or terminal gameplay. PR #8380's App Server mock result is separate evidence and was not replayed. Issue #59 remains open; its current-main live allocation and private game lane remain unassigned.

## Reproduction and integrity

From repository root, use the exact one-shot command in `FREEZE.md` for the candidate. The candidate uses exclusive output creation and refuses overwrite. The independent auditor can be rerun read-only against the retained JSON. `SHA256SUMS.txt` covers the package files and retained predecessor STOP records.
