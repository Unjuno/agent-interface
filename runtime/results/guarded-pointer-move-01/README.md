# Explicit guarded pointer motion: primary self-use

**PASS_SCOPED_GUARDED_POINTER_MOVE; full integration remains HOLD.** Source
`da150434f62b719ed29380172ede6e4a5e061628`, fresh seed `1001048`, WSL
3.0.1 / Ubuntu / private Xvfb `:153` / Chromium. The primary used the packaged
production guarded-X11 MCP relay and composed `sendPresented` host.

The [previous controlled probe](../pointer-hover-contract-01/README.md) identified
an actual button whose pixels change when the pointer moves over it. The new
`NativeHandleBridge.move` / `interface_guarded_input(interaction="move")` exposes
that motion without pressing. Its tail permits only waits and observations.
The caller reviews the returned screen and explicitly mints a new reference;
the original exact-pixel guard is never weakened or refreshed automatically.

The primary entered and visually checked two task tokens, moved onto Save,
reviewed the hover image, minted new Save aliases, clicked, and reviewed each
SAVED image. Independent scoring recorded task-1 and task-2 exactly once with
no unexpected submissions or duplicates. Tasks 3–6 were deliberately unattempted
under the frozen two-task plan; the full six-task oracle correctly returns false.
Task2's non-hover Save alias was minted after its field capture, because field
motion changes the pointer state. There is no automatic remint or replay policy.

Both move receipts retain valid admission/focus/move guards and one pointer
emission, with zero presses. Both later clicks retain valid before-press guards
on the new hover pixels. All nine delivered images were forwarded to and
reviewed by the primary. The move crop hash equals the earlier probe's hover
hash; pre-move guard patches equal its non-hover hash. All input releases and
the explicit session close were verified empty. Original fixture handle `9060`
and relay transport ended with code 0. Fixture child codes `[0,1,1]` are retained;
this is not a claim that every child exits cleanly.

There were 17 public calls and eight input calls. Host send-to-reply feedback
for the two moves was 246.635 / 236.699 ms, and for the final clicks 276.240 /
275.165 ms. Each included an explicit 100ms fixed delay. These are individual
tool feedback measurements, not task completion or primary perception times.
No matched baseline or actual token/cost comparison was run in this scope.
The new three-check move shape falls back to full presentation even when brief
is requested; no compression advantage is claimed.

Two unsuccessful predecessors are preserved: trial01 failed importing the
fixture-only openpyxl dependency in the MCP venv before allocation; trial02
stopped after the primary chose a flat blank-page navigation reference. Its mint
was refused before input, and the original fixture and relay ended with code 0.
The successful trial03 uses the dependency-checked standard Ubuntu Python for
the fixture, the dedicated venv for MCP, and a textured browser tab reference.
No consumed allocation was restarted. The earlier premature terminal snapshot
is preserved alongside v2 containing the actual transport close result.

Validation: guarded runtime 18 tests and package-qualified CLI 264 tests passed.
The first CLI discovery command lacked `-t .` and failed one relative import;
the corrected command passed. The six new tests first failed for the absent move
API/public schema, then passed with the implementation. These tests verify
transport/admission contracts; the actual primary trial supplies separate GUI
evidence. This remains a candidate, pending a fresh complete six-task matched
comparison, recovery and cross-domain coverage.

The first hosted native-MCP run on `fc0bec45b` failed because two legacy tests
called the private `_run_guarded(activate=...)` signature directly (12 subcase
errors). They now exercise public `click` and `keyboard`, preserving invalid
gap/capacity rejection and no-guard/no-dispatch assertions. The new move tests
are also registered in the shared CI harness. The corrected shared local runner
passed 336 protocol and 146 harness tests. `ci-fix.tar.gz` and its manifest retain
the original hosted failure log, complete corrected local logs and source pins.
This changes tests and suite registration only; the frozen live runtime remains
the source recorded above. Hosted success for the corrected head must be checked
separately and is not inferred from this local pass.

`raw.tar.gz` retains all three trials, packaged runtime and host, frozen plans,
requests/replies, full native artifacts, independent score and primary review
records. `manifest.json` hashes every member. The verifier recomputes request/
reply identities, presentation order, exact guards, pointer-only programs,
delivered/native image identity, hover crop, independent counts and termination:

```sh
python3 runtime/results/guarded-pointer-move-01/verify.py
python3 -O runtime/results/guarded-pointer-move-01/verify.py
```
