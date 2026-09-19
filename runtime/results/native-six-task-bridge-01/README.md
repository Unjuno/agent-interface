# Six-task primary-assistant use of the native handle bridge

2026-09-19, seed 991083. The existing six-task Chromium fixture was used with
`NativeHandleBridge` for field entry and Save. The primary assistant viewed the
cold and repair PNGs and supplied explicitly named source sequences and points.
No helper model ran. Frozen handle/fixture modules were reused without edits.

Run 2's independent oracle reports six exact submissions, one per task, with no
duplicates, missing tasks or unexpected submissions. Tasks 2/3 reused cold
handles. Task 4 rejected the old field before dispatch with **zero input**;
the assistant viewed source 27 and reminted handles for the changed layout.
Tasks 5/6 reused the repaired handles. Twelve native field/Save programs ended
with verified empty input; a thirteenth request was the retained refusal.
All owned processes have terminal return codes.

Public window titles supply READY/SAVED navigation readiness. Independent
submission-history scoring runs at the end. Task descriptions supply authorized
URLs/tokens, not target coordinates.

## Failure and text correction

Run 1 stopped on task 1: native text preflight accepted `-`, but literal X keysym
lookup failed after emitting a prefix. Partial-execution evidence preserved the
completed operations, uncertain text operation and verified release. No Save was
attempted; the independent oracle has zero submissions. The failure is retained.

The fix resolves the full supported payload before execution and text emission.
Period/minus use named X keysyms; underscore uses Shift+minus. This repairs the
advertised character set, without adding URL punctuation or claiming portable
Unicode/keymap behavior. Two unit tests cover mapping and no emitted prefix when
a late character is unmapped. Eight private-Xvfb tests passed, including exact
`a-._ A` output. The first test-suite failure is also retained: punctuation passed,
but Ctrl+A did not clear Tk's field before the next test. The test helper now
uses Home then Shift+End. Chromium's Ctrl+A field-entry path is unchanged.

## Scope and timing

URL navigation still uses the existing research `Driver`, with navigation time
and input counts retained. This is a **mixed navigation / native guarded-input
integration**, not a fully unified public API or closure of Issue #2337.

| Task | Field/Save local elapsed ms |
|---|---:|
| 1 | 731.306830 |
| 2 | 743.561639 |
| 3 | 774.380195 |
| 4, including refusal and assistant repair wait | 27637.785429 |
| 5 | 783.557621 |
| 6 | 768.802736 |

These intervals include local guard captures/result persistence, but exclude
navigation, initial cold grounding/minting and the following SAVED-title wait.
Task 4 includes the outer repair wait. No matched baseline, measured model
tokens/cost, human-tempo or generalized performance claim is made. Non-atomic
capture/input, semantic verification before Save, global source/binding revisions
and uncertain-delivery recovery remain open.

## Evidence and reproduction

`run-1` retains the native text failure. `run-2` retains the successful run, all
bridge observations/programs/results, explicit grounding, submission history and
cleanup. `text-test-1/2` retain failed/corrected automated suites. `final-source`
contains final sources, not the source version of run 1. The failed run used the
native backend at preceding main revision `bb5a48ae15052cea52c74bf75ce5966e09ded3d4`
before the text fix. `SHA256.json` hashes 192 files, excluding itself and this
README; 57 native PNG/source links across both runs were checked during retention.
Historical absolute image paths refer to results-local; copies keep their
basenames. `cold-source.json` and `repair-source.json` identify viewed sources.

With existing Linux/X11 suite dependencies and Chromium available:

```sh
XAUTHORITY= PYTHONPATH=.:research/live_control python3 -u \
  research/live_control/run_native_six_task_self_use_v1.py --out NEW_DIRECTORY
```

Override `--chromium` if needed. View each printed image, then supply the requested
JSON containing its source sequence, field point and submit point. The runner
waits at most five minutes for each grounding and invokes no helper model.
