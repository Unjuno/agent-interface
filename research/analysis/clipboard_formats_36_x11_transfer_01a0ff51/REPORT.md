# Native multi-format transfer: scoped result for #36

Status: **PASS_X11_MIME_TRANSFER_METHOD_SCOPED** for the four predeclared cells,
the observed cleanup conditions, and all14 named corruption checks.
Separate owner/consumer processes transferred both representations through a
private native X11 clipboard; actual Ctrl+V produced the predeclared effects.
The ordinary rich/plain widget distinction explains this result. No new
clipboard authority mechanism is needed for these four cells.

| Cell | Widget | text/plain | text/html text/style | Saved text/style | Summary eligible | Both-format eligible | Intended Robin task correct |
|---|---|---|---|---|---|---|---|
| N01 | rich QTextEdit | Robin | Robin bold | Robin bold | yes | yes | yes |
| N02 | plain QPlainTextEdit | Robin | Robin bold | Robin plain | yes | yes | yes |
| N03 | rich QTextEdit | Robin | Quinn bold | Quinn bold | yes | no | no |
| N04 | plain QPlainTextEdit | Quinn | Robin bold | Quinn plain | no | no | no |

The summary diagnostic admits N03 despite the wrong saved text. Comparing
both supplied formats rejects both authored conflicts. Checking the exact
saved text and uniform boldness also detects both wrong task effects and
accepts both controls. These three facts are diagnostics of the same four
deliberately executed pastes; they are not three implemented controllers.
Post-effect checking does not prevent or undo either deliberately wrong paste.

## Prospective identity and first outcomes

- Study: `CLIPBOARD-36-X11-MULTIFORMAT-TRANSFER-20261003-01`.
- Source commit: `21be64324057d8186fe321923fba6181e6b9cb55`.
- Source base: `332da58a9b6b825c384a142dfb59d7ed2b8b774e`.
- Freeze commit: `f607f191738241cadffb1be48aacee9016977273`.
- Freeze bytes SHA256: `8fb7da8a4f424bdf511e990c88ab84cbca4962aa293f54af70d30a6d582233fb`.
- Fixed image: `sha256:18835dcb3335d1cc5367c78bf0c76a8174c522aebe0fd76ba743f509dcd4f309`.
- Freeze written at `2026-10-03T03:26:58.910314+00:00`, pushed and read back
  byte-for-byte at that commit before candidate invocation.
- Candidate receipt: `2026-10-03T03:27:51.552174+00:00` through
  `2026-10-03T03:27:53.529800+00:00`; client/container exits0, retained
  `du -sb` output50806B within the prospective1048576B cap.
- Candidate and separate auditor: one invocation each, retries0; both
  receipts say `EXIT_ZERO_SOURCE_EQUAL`. Nine pinned source/input/protocol/
  launcher files match before and after each invocation. The auditor reads
  candidate evidence through a read-only mount and imports no Qt/app/runner.
- Original raw SHA256:
  `db548d21cd580032f4a187af825617256b42739c812e9d246f2cbd334f19116f`.

The timestamps are driver/Engine diagnostics, not comparable operation
latency or a speed benchmark. Candidate/auditor receipts preserve actual
create/start/inspect/hash argv, stdout, stderr, UTC times and state.

## Method and observed cleanup

Each cell used a fresh private Xvfb display, an owner process with stable
`text/plain` and `text/html`, and one standard consumer widget. Payloads
never changed during a cell. `xclip` preserved both exact native byte strings.
`xdotool windowfocus --sync` and XTEST `ctrl+v` targeted the consumer; the
consumer never called an insertion API. Saved text, Qt HTML and a window PNG
are retained. Owner MIME-request and consumer key/text-change journals are
separate. The raw-only stdlib auditor parses the saved HTML to reconstruct
text and uniform boldness rather than trusting the recorded dump.

Native xcb, stable owner/focus during paste, release of Control and V,
neutral32-byte keymaps before/after/final, final clipboard owner0, and all
three owned process exits0 were observed in every cell. Reused native XIDs
are scoped to each fresh display; they are not cross-server object identities.
The joined per-cell manifest covers all11 non-row artifacts. Separate row
records and the top-level raw are also retained. Screenshots visually agree
with the saved documents but are not the independent formal effect oracle.

The14 frozen raw corruptions rejected for their individual required reasons:
omission, duplication, offscreen platform, boolean PID, float owner, false
exit alias, focus change, held keymap, boolean command exit, relabeled paste,
missing key release, changed transport hash, changed saved-HTML hash and
relabeled dump. Each modified row also fails its row-record agreement where
applicable; that generic failure alone did not count for a named check.
This tests those14 corruptions, not general tamper-proofness or all malformed
JSON/HTML. The four regression tests use unchanged construction02 bytes.

Source getter logging supports the expected rich/plain transfer preference.
It does not prove exclusive consumed-MIME semantics. The audit explicitly
records `exclusive_consumed_format_proven: false`.

## Environment, construction and preservation

Own dedicated OrbStack guest/private Docker Engine on macOS; Linux aarch64,
Python3.12.3, kernel `7.0.5-orbstack-00330-ge3df4e19b0a0-dirty`. The fixed
image derives from the earlier Qt5/PyQt5 image; the tested toolkit is Qt5,
not the Qt6 documentation linked for the X11 system analogy.
Network none, read-only root/source, own output, private tmpfs64MiB.
Observed cgroup settings are CPU50000/100000microseconds (ratio0.5),
memory536870912B, pids128. These are recorded settings, not an adversarial
resource-enforcement or host-pressure experiment. Other host workloads are
uncontrolled. No host X socket, clipboard, model, GPU or shared GUI lease
was used. Xvfb's retained xkbcomp warnings concern unrelated keysyms; actual
paste commands, required key releases and saved effects reconciled.

Construction01 stopped before `run.py`: inherited Python entrypoint plus an
explicit Python command attempted `/src/python3`, exit2. Original stderr,
Dockerfile and later state inspection remain. Imagev2 explicitly clears
entrypoint/CMD; Docker inspection omits those keys when cleared.
Construction02's first Setup rich paste, its source snapshot and bytes remain
unchanged. Construction03 verifies the later joined artifact/display/cgroup
recorder on Setup. Neither construction run contributes to the four formal
counts. Test-first four failures and the later four passing regression tests
are retained. The public red log replaces only the private source prefix with
`<SOURCE_ROOT>`; the original log remains in the private task evidence.
Build logs contain no private source prefix and are preserved without that
redaction, including original carriage-return terminal output. An initial
staged whitespace check reports only those two raw build logs; the check
on all other changed paths passes. No raw bytes were normalized for it. No original candidate or formal audit was overwritten.

## Decision boundary and remaining work

Adopt the narrower lesson: selection of a representation and the correct
saved task effect must be checked for the target widget. Existing MIME
inspection and exact saved-state checking suffice for these authored cells.
The merged offscreen result now has native Linux cross-process transfer
evidence, without natural races or serialized-writer policy.

All cases were development-known, synthetic ASCII, two Qt widget classes,
one image and four authored stable payloads. This does not establish native
macOS clipboard behavior, arbitrary applications, natural races, model task
utility, performance, privacy/security/runtime safety, or completion of
#36, #2774 or #57. #3981's consumed27-case admission/mutation allocation and
incomplete prior evidence remain unchanged and were not rerun. Integration
requires fresh nonauthor content agreement and current-main/tree confirmation;
the scientific PASS is independent of the PR/merge state.
