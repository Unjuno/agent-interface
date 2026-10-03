# Compiled callback payload custody: ordinary integration repair

The existing compiled graph exposed two private mutable objects to callbacks.
A journal sink could format or retain an event dictionary that was also used as
returned critical evidence. An observation adapter could consume its requested
predicate list and thereby change the private validated interface declaration.
This repair gives journal callbacks a separate deep event copy and each
observation request its own list. It preserves the planner-authored graph and
recorded completed prefix while those callbacks process their own payloads.

Refs #57. Author is existing worker/session
`01a0ff35-2ef3-7911-9911-f31862ad642f`, FINAL-v5. This is a concrete correctness
and evidence-custody blocker in the chosen compiled path, not a new feature
family or a live/token comparison. The source owner claims for #6900's
successful effect-reference gate and #6908's capture-order gate remain separate.
No change to their source, frozen evidence, allocation or committee was made.

## Contract, reproduction and smallest repair

`emit()` already made a deep event copy, but then supplied that same copy to
`journal()` and retained it in `critical_events`. An ordinary callback that
cleared its event after formatting caused `KeyError` immediately after an inert
action. Editing action/status/release or nested matched conditions changed the
returned evidence. A sink retaining event objects could clear all eight returned
critical events even after `run()` finished. Those edits did not independently
change the real graph actions; they contradicted its own returned evidence.

The observation request separately passed `interface["predicates"]` directly.
Clearing this callback-local list made a valid phase predicate undeclared;
changing a retained earlier request interrupted a later observation after one
action. This defeated the private interface copy that `validate()` had made.

The production repair changes only two behavior lines in
`runtime/core_v1/compiled_gui.py`: supply `copy.deepcopy(row)` to the journal,
and `interface["predicates"].copy()` to observe. A shallow event dictionary copy
would leave nested matched-condition aliases, so the event copy is deep. The
validated predicate list contains only bounded immutable strings, so a list
copy is sufficient. No new dependency, broker, retry, scheduler or authority is
introduced. Exceptions still propagate; journal time remains included in the
existing deadline checks. Documentation adds that ownership boundary.

The source follows ordinary Python object-copy semantics, as documented in
the [Python 3.11 copy reference](https://docs.python.org/3.11/library/copy.html).
No external algorithm implementation was copied; the existing stdlib call is
used. This page is PSF-licensed documentation. Selected interpreter/copy file
pins are recorded without claiming all-system provenance.

## Test-first evidence and actual validation

The first five journal regressions ran against exact current working source:
four failed for the alias defects, while the exception-propagation control
passed. After the event-copy change, five passed. Two subsequent observation
request regressions failed against the journal-only source before the list-copy
change. Every first stdout/stderr, argv/cwd/UTC/exit receipt and the original
before/journal-only sources remain. The seven final tests use the actual
compiled graph and the existing inert Driver fixture with literal branch,
prefix, pending-effect and evidence expectations.

| Check | Executed environment | Actual result |
|---|---|---|
| First journal regressions | native Windows CPython 3.11.9 | 5 methods: 4 FAIL, 1 PASS |
| Journal repair | same | 5 PASS |
| First observation-request regressions | same | 2 FAIL |
| Complete affected core discovery | same, normal and `-O` | 83 PASS in each |
| Complete affected core discovery | native Windows CPython 3.12.14 | 83 PASS |
| Initial guarded adapter composition | 3.11.9; no installed Xlib | 29 methods: 27 PASS, 2 import ERROR |
| Guarded adapter after private dependency setup | 3.12.14, python-xlib 0.33/six 1.17.0 | 29 PASS |
| Existing isolated working-source archive check | 3.12.14 | 1 PASS |
| Core doctor | 3.12.14 | exit 0, native backend not loaded/no authority |
| Normal committed-source archive build | 3.12.14 | exit 0, source commit pinned |
| Seven regressions from that actual zipapp | isolated 3.12.14 `-I` | 7 PASS; no research imports |

The guarded tests execute the real shared adapter with inert captures/input and
PIL images. Their successful imports are not native X11 control. The dependency
installation went into an owned private target directory, never a shared
runtime. Its first two import errors remain visible by test name. No original
formal producer or previously consumed experiment was executed. No hosted CI
outcome is claimed. Existing core discovery selects the new test module; no
workflow is changed.

Example local verification, from a checkout of the proposed source:

```text
python -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v
python -O -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v
python -m unittest runtime.guarded_x11_v1.test_compiled -v
python -m unittest runtime.distribution_v2.test_compiled_archive -v
python -m runtime.core_v1.doctor
```

Guarded tests require the repository's optional Pillow/python-xlib imports;
they open no display. Actual commands and interpreter paths are in retained
receipts, with declared personal path projections.

## Committed identity, conversion and first metadata error

Content base is `316ac44b24d4ac29c1942d2fee51f1c0599855b1`. Source commit
`49817d17884afe467faf26f405682d42971a98c4` has that sole parent and exactly three
changed paths: implementation, contract document and seven-method test module.
The full parent tree is otherwise preserved. The evidence delivery adds only
this inert package; its final head/proposal are recorded outside that head.

The first staged-byte verifier assumed raw working bytes equalled Git's clean
bytes, failed on CRLF normalization, and the next dependent local commit
nevertheless ran. That sequencing error is disclosed; nothing had been pushed,
voted or applied. The original tool traces remain private; no independently
captured native streams that did not exist are fabricated. Readback then proved
the exact three-path/full-parent scope and per-file conversion; see
`source-commit-readback.json`. The first sparse checkout command also emitted
inherited pattern warnings and ended nonzero on an absent optional ci.yml read
after its Git steps succeeded. A later read-only archive metadata checker used
the wrong `sources` key, exited 1 before its Git/ZIP source loop, and was corrected
after inspecting the actual `source_files` schema. Its first tool trace is also
retained; no previously uncaptured streams are reconstructed. These operational
errors did not become passes.

Tested working implementation SHA256
`5b813fcf7d2e88f2625e67baafdd8474aee949dd5858e85eb3365fd55bea90b8`
becomes committed SHA256
`3f9d03a89c647a4221a556496a27e91f656a1cf3ae14e1ebdea072d3bdd96a81`
solely by CRLF-to-LF conversion. Their Python ASTs are identical. The regression
module is byte-identical at SHA256
`c8df4300fdf121dc5ac450e665b37a2498956df5337fbd7e10ad49b6ff8cc40b`.
Receipts preserve the actual executed working-source hash; they are not
relabeled as byte-identical Git runs. The normal builder then read the actual
committed source, and the isolated seven-regression probe verified its module
came from that zipapp with exact committed bytes.

`PUBLICATION.json` maps every copied original/public file's length and hash.
Personal absolute home prefixes alone are projected from textual derivatives;
private original bytes remain. The first binary archive is unchanged. Package
attributes preserve all public archival bytes without newline conversion.
`SOURCE.json` pins the selected base dependency/configuration blobs;
`ENVIRONMENT.json` records selected interpreter/copy and private library files.
Those do not authenticate clocks or cover every binary/OS/transitive dependency.
`MANIFEST.json` lists every package file except itself; final Git blobs are
separately verified after staging. Source snapshots and helpers are inert `.txt`
files, and normal runtime packaging imports no research evidence.

## Decision and transfer limits

RETAIN the narrow runtime repair as a proposal supported by the observed
test-first failures and affected integration checks. Main adoption requires a
prospective fixed committee of three actual existing nonauthors/two explicit
content approvals, then an exact-current combined tree, nonauthor applicability
checks, actual repository/platform conditions and one conditional forward
application. The author issues no content vote or main request here.

At the checked newer main `816724f93a7239b3ad9b5ebb2e5f79b8a103b2db`, intervening
changes are archival and the selected runtime/core/guarded/CLI/distribution/
backend/configuration footprint is unchanged. That is author-only context,
not a nonauthor current-tree certificate or approval of arbitrary later main.

Scope is trusted sequential callbacks, controlled built-in JSON payloads and
inert effect/release adapters. Hostile callbacks can still raise, block, change
external state or manufacture observations; no sandbox or authentication is
provided. Arbitrary custom objects and concurrent mutation are untested. The
repair does not prove physical release, independent application effects, live
adaptation, token/resource savings, latency or overall computer control. Extra
copying cost is unmeasured. The broad #57/#59 acceptance gates remain open.
