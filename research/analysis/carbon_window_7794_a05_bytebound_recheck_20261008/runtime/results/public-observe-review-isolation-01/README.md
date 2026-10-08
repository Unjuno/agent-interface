# Public observation visual verification after display isolation

Source: 84e581ec8. WSL Ubuntu; primary assistant, no helper model or sensor.
Previous evidence remains in public-observe-review-01 unchanged.

Attempt 4 added a direct pre/post X11 GetImage comparison to the earlier
fixture. It failed before public observation with Xlib BadMatch (GetImage,
major opcode 73); finally closed the client and owned Xvfb, exit 1.

Attempt 5 selected display :147 after checking filesystem socket, lock and
abstract socket absence, used the existing WSL -nolisten unix setting,
checked server process readiness and asserted a 640x480 screen before creating
the fixture. Public observe and review both returned successfully; the fixture
and Xvfb were closed, exit 0. input_dispatched=false.

The primary assistant inspected the reviewed PNG and saw the white text
"Public CLI observation -> review" and green rectangle. The fixture's direct
raw pixels before and after public observe and the public captured raw pixels
have identical SHA-256 (comparison.json); both direct images contain 3 colors.
The review image also matches its recorded PNG artifact hash.

This demonstrates visible content through the public observe/review route.
It is not application task completion, a latency comparison, sensor evaluation,
or evidence of token savings. The earlier uniform-background result was not
reproduced under explicit display isolation. Automatic display allocation plus
WSLg filesystem/abstract socket coexistence is a candidate explanation, not a
proven root cause: prior connection identity was not recorded. No runtime
capture fix was needed to obtain this successful result.

Original runtime paths are retained in JSON; archived captures grant no live
authority. Manifest hashes all files except itself.
