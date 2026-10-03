# Native clipboard availability and delayed-effect boundary — #36 / #57

Worker01a0ff51; namespace only. Base316ac44b24d4ac29c1942d2fee51f1c0599855b1.
No production implementation or new scientific Issue. Previous #6886/#6916
format allocations and #3981 mutation allocation remain consumed and unchanged.

## H

A positive, unchanged X11 selection-owner ID is insufficient to establish
clipboard availability. A normal Qt native paste can outlive a finite caller
reply deadline when its owner is deliberately stopped, then affect the document
after that owner resumes. A finite subprocess read before native input can refuse
that specific unavailable state with no paste key, while accepting a healthy
control. A reply timeout after input is UNKNOWN_PENDING_EFFECT, never no-effect.

## T

Six fixed cells in cases.json, one each: healthy/absent/SIGSTOPed owner crossed
with ordinary native Ctrl+V and read-before-input. Fresh separate Qt owner,
QPlainTextEdit consumer and Xvfb100..105 per cell; synthetic Cedar only.
No retry/replacement/tuning. Candidate once; separate raw-only auditor once.
Construction P01 uses Spruce/direct/stopped, P02 Willow/preflight/stopped and is
excluded. Original successful native construction and failed binary-tar collector
are retained; recovery was read-only, not a candidate replay.

Pin all source/input/protocol/launcher hashes, source commit and image ID in a
public FREEZE before invocation. Reuse the exact cached native image from #6916,
sha256:18835dcb3335d1cc5367c78bf0c76a8174c522aebe0fd76ba743f509dcd4f309;
fresh inspect records actual identity. Python3.12.3/Qt5.15.13/PyQt5.15.10,
Linux arm64, dedicated private Engine, no host clipboard or shared native lane.
Network none, read-only source/root, .5CPU/512MiB/128pids, tmpfs64MiB.
Actual cgroup values are evidence of configuration, not enforcement validation.

Every cell starts empty, records native focus/owner/32-byte keymap, then either
closes the owner or SIGSTOPs only its exact child PID and observes /proc state T.
Read-before-input uses xclip text/plain with .5s communicate deadline; kills and
waits its own read process on timeout. Admit only exact bytes, successful read and
positive owner. Ctrl+V uses XTEST/xdotool; no consumer insertion API. After input,
request saved state with .5s finite byte-framed reply wait, retain the application
journal prefix at that deadline and independently query the still-responsive
X server. Resume the stopped owner only after this record. No blind replay.
Then reconcile late/current saved text, Qt HTML, screenshot, app native key and
effect journal, owner journal and actual exits. IPC permits observation/close,
not post-ready text setting. Prior app.py is reused with two disclosed journal
additions: current text on textChanged and IPC command receipt.

Native commands/replies/child cleanup have3s waits; stop-state query1s.
Container outer coreutils timeout is60s plus3s kill-after, host attach75s then
owned docker kill/inspect with15s command waits. Auditor30s plus3s kill-after,
host45s. On first cell infrastructure uncertainty STOP, preserve partials and
cleanup. Output cap2MiB checked without truncating evidence; exceeding is STOP.
These are finite configured watchdogs, not hard real-time or daemon-stall proof.

## D

PASS_CLIPBOARD_AVAILABILITY_BOUNDARY_SCOPED only if all six raw cells, source/
artifact identity, focus/key neutrality and actual graceful child exits reconcile;
healthy controls both save Cedar; absent direct saves empty and read policy sends
no paste; stopped direct reaches UNKNOWN_PENDING_EFFECT with no textChanged in
its recorded deadline prefix, owner ID unchanged and neutral physical keys, then
one Cedar effect after SIGCONT; stopped read times out/kills only xclip, refuses
before input and still saves empty after owner restoration. All paste-admitted
cells have exactly one Ctrl/V press and release pair, refusal cells zero. Raw-only
auditor rejects ten specifically named, rejoined/rehash corruption controls.
Complete gate miss is FAIL; missing/incoherent evidence STOP/HOLD; no rerun.

## C

This is cooperative Qt behavior and deliberate process suspension, not natural
failure prevalence, a toolkit vulnerability, clipboard exclusivity, continuous
owner/focus proof or prevention of changes after preflight. Standard bounded
subprocess reading suffices for the constructed fault: no novel mechanism is
required. Native input release can precede application effect; it cannot cancel
already queued consumption. The guard may falsely hold a slow healthy owner.

## U / decision

Same-container monotonic order is exact evidence; elapsed .5s is a selected caller
budget, not a measured human tempo or optimal timeout. Host contention remains
uncontrolled. No timing calibration, tail bound, population rate, privacy/security,
native macOS, arbitrary application, model, token, rollback or runtime integration
claim. Qt6 documentation describes the X11 event-loop dependency but does not
certify this Qt5 run: https://doc.qt.io/QT-6/qclipboard.html .
Integration decision: carry UNKNOWN_PENDING_EFFECT after a post-input deadline;
an observed neutral keymap and stable owner are insufficient no-effect evidence.
Availability checks are separately bounded and fail closed before input when
their evidence is missing. Overall #36/#57 and roadmap remain open.
