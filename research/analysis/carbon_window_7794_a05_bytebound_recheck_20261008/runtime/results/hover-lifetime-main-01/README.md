# Explicit hover motion and reference deadlines on main

Hover can change a button's pixels before a click. The existing exact-pixel
guard correctly refuses a reference grounded before that change, but main did
not expose a pointer-only guarded operation to inspect the hover first. Main
also omitted a reference's finite expiry from public mint replies, making an
expired alias harder to anticipate after a long pause.

This integrates the tested candidate implementations onto source
`659177b7fab93fe00248516beabaa53c2836d8f2`, based on main
`4a0d0da26d6983c3addd5c369f3d97ad63a2870b`. `interaction="move"`
dispatches motion without a press, permitting only waits and observations in
its tail. The caller inspects fresh hover pixels and explicitly grounds a new
alias. Existing guards, admission, lease and recovery behavior remain in force.
Mint replies expose the existing deadline without extending or renewing it;
legacy Python `mint` keeps its offset-only contract.

Candidate pointer-move and lifetime archives are retained unchanged inside the
raw bundle and independently rechecked normally and with `-O`. Their limited
outcomes remain limited: two candidate Save tasks and a lifetime metadata study
do not close the full six-task, matched-efficiency or cross-domain gates. Whole
candidate PR #5639 remains HOLD. No primary-caller trial policy is adopted here.

## New main-specific personal trial

The pre-run source/build/fixture/driver hashes and H/T/D/C/U are frozen in
`PLAN.json`. The primary used the committed portable production MCP host on a
private WSL Xvfb/Openbox/Tk scene. It inspected the grey SAVE button, grounded
its text, moved without pressing, and inspected the blue SAVE (hover) screen.
The predeclared old-alias click control returned `region_pixels_missing` at
before-admission with no execution and `input_dispatched=false`. The primary
then inspected that image, minted a new hover reference, clicked, and read
SAVED 1. Only after public/transport close was the independent journal read.

The original application journal records exactly one Save, after motion had
completed. Two dispatch programs exist: one focus/motion/wait/release program
and one click program with a single press. Input releases and public close are
verified neutral. Transport exit is 0; owned child exits are `[0,0,-15]`.
There were 7 public calls and 4 original images. The refusal image appeared
black inline, so one predeclared same-byte PNG preview was used; its hash and
actual review are retained. No new observation or input retry replaced it.

Host send-to-reply for motion was 251.17 ms, including an explicit 100 ms fixed
delay. The complete first-send-to-last-reply span was 73,198.73 ms: requests
outstanding 1,722.89 ms, presentation callbacks 6.41 ms, other host intervals
71,469.44 ms. The latter include orchestration, logs and caller gaps, not isolated
model thinking/waiting. No comparison establishes speedup, first useful feedback,
semantic latency, human tempo, provider tokens or cost.

## Validation and retained evidence

The new tests failed before the port and passed afterward (33 selected tests).
The shared runner passed 337 protocol and 156 harness tests. Legacy invalid
tail/capacity checks now use public click/keyboard methods rather than the
changed private helper signature; no-guard/no-dispatch assertions are retained.

`raw.tar.gz` contains 167 files: frozen main trial, original host/runtime images
and replies, application journal/cleanup, exact source, complete RED/green/native
logs, and the two unchanged candidate evidence bundles with recheck outputs.
`raw-manifest.json` lists member bytes/hashes; `result.json` binds archive and
auditor. The raw-only verifier recomputes frozen-source identity, program shapes,
neutral release, unchanged PNG bytes, review binding, actual stored expiry, and
independent Save count. A duplicated Save event is rejected normally and with
`-O`. Verification requires no live desktop or input:

```sh
python runtime/results/hover-lifetime-main-01/verify.py
python -O runtime/results/hover-lifetime-main-01/verify.py
```

After the audit/archive had been generated, packaging initially tried to read a
previous verifier from a path omitted by the sparse checkout and stopped with
FileNotFoundError. The repair reads that committed file through `git show` and
creates this report's verifier. Both modes then pass. This packaging failure
does not restart or change the frozen live trial; it is retained separately in
`packaging-stop.json`.
