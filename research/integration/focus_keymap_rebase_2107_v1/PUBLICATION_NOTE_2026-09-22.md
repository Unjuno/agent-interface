# Retrospective evidence delivery — 2026-09-22

This continuation publishes the already executed local allocation `focus-keymap-rebase-2107-20260922-01`. The local source/gate freeze predates all formal cases but was **not** a GitHub preregistration. The historical `REPORT.md`, including its then-true GitHub-write STOP, is preserved rather than rewritten.

## H / T / D / C / U

- **H:** complete key-edge history is sufficient only while its observation coverage remains continuous. A focus-bound X11 observer can miss modifier changes while focus is elsewhere; a current `KeymapNotify` rebase on focus return plus subsequent edge updates should recover the tested Shift state without a separate observer `XQueryKeymap` call.
- **T:** 24 fresh authenticated private Xvfb/Tk sessions, two policies (`KEY_EDGES`, `FOCUS_KEYMAP`), six directed schedules, two repetitions, two immutable 12-case batches. Real XTEST task input; one ordinary Entry effect. No model/provider or user desktop/data. Formal reruns/replacements: 0.
- **D:** `PASS_FOCUS_KEYMAP_REBASE_SCOPED`. `KEY_EDGES`: exact lowercase `b` 8/12, wrong uppercase `B` 2/12, unresolved 2/12; phase state agrees with the independent scoring query 18/24. `FOCUS_KEYMAP`: exact `b` 12/12, phase agreement 24/24, no wrong or unresolved cases. Raw-only audit: 2,713 checks, errors `[]`; 12 evidence mutations reject after intact copies pass; 17 unit methods pass. Recorded exits and postformal process/cleanup evidence are retained.
- **C:** one private Xvfb/Tk/Shift fixture with explicit application focus establishment and a continuous observer connection. X-server logical key state is not physical HID telemetry. `KeymapNotify` is a state sample tied to this event stream, not timeless action authority or proof of task completion.
- **U:** arbitrary apps/toolkits, grabs, stream loss/reconnect, multiple modifiers, real hardware, model usefulness, latency/token benefit and production integration remain untested. The broad #2107 acceptance criteria are not closed by this result.

## Publication package

`EVIDENCE_ARCHIVE.json` binds the exact current-allocation archive and binary parts. It contains 699 files: all frozen source/build/environment inputs, the complete 24-case formal raw evidence, audit, corruption controls, unit tests, process/cleanup evidence and summaries. The predecessor experiment's nested ZIP is intentionally not pooled into this package; its exact SHA-256 remains recorded in provenance.

Run only:

```sh
python -B verify_publication.py
```

This restores to a fresh temporary directory and runs read-only audits/tests. Do **not** rerun the consumed formal X11 allocation.

## Integration meaning

The scoped constraint is to keep event-stream coverage explicit. A complete reducer over events it never received is not a complete account of global key state. When focus changes the observation boundary, either re-establish a current state basis with provenance and apply subsequent events, or remain UNKNOWN. This is research evidence, not a production runtime change, and component PASS is not integrated/product PASS.
