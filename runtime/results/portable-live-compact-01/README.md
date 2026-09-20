# Primary use of the current portable CLI

One owned WSL/Xvfb allocation exercised the zipapp built from committed main
7d12e7afc1b1db163b74a54a821658c8c867e5c7. The primary agent viewed the initial
400x180 PNG, selected the visible entry at (50,55), and submitted one explicit
focus/click/text/save/capture/release program using `dispatch --review --compact`.
The task was to enter and save `portable-3514` in the existing Tk integration fixture.

The CLI returned exit 0, all ten operations completed and input release verified.
The independent fixture file contains `{"saved":true,"text":"portable-3514"}`.
The action's PNG nevertheless still showed an empty entry and `unsaved`. The
primary agent did not replay input. One explicit read-only observation returned
the visible text and `saved:portable-3514`. This run confirms the combined result
route works, while retaining the counterexample that action completion plus a
captured image does not prove the image reflects the saved effect.

The compact option retained receipt-view-v1 because reference bookkeeping did
not produce a smaller receipt. There is no compression benefit in this sample.
The local subprocess interval for dispatch was 486.054988 ms, including Python
startup and CLI work. It excludes primary reasoning, tool transport/rendering,
and the later observation; it is not time to first useful feedback, semantic
completion, or a human-tempo comparison. No model tokens or costs were measured.

## Reproduction boundary and retained evidence

The archive SHA256 is 236b146fea68f54f213d522f159b264b37b48c1fec9f3e9fb10319b43c0d6206.
The retained zipapp BUILD.json/manifest pins every included source blob. The
zipapp ran with its working directory outside the repository package root.
The fixture and owner used the checked-out source; this is a synthetic fixture,
not Calc or a general desktop success claim. No secondary model or new sensor
implementation was used. Docker Desktop was not restarted.

The public contract's source sequence 1 and binding revision 0 were explicit
caller labels for this owned fixture; they are not a server-issued native MCP
source reference. The wrapper assigned a ten-second lease immediately before
the single dispatch. No automatic lease retry or source renewal occurred.

Xvfb :248 was checked for existing filesystem/abstract listeners and a lock
before launch, and connected geometry was checked as 640x360. On explicit stop,
the owner reaped the fixture (SIGTERM, -15) and Xvfb (0), then itself exited 0.
Only these tracked processes were checked; full descendant verification remains
false. Nonfatal xkbcomp warnings are retained.

RESULT.json inventories all 27 files in evidence.tar.gz by size and SHA256. The
archive was read back and every item compared. It includes commands, complete
CLI responses, PNGs, input events, fixture effect, decisions, build manifest,
zipapp, local call clocks and cleanup. The final observation used a direct shell
command and has no separate call-clock record. The primary agent's image views
are in the conversation; this bundle is not a complete host conversation trace.

This is draft integration evidence pending independent review. It supports no
formal adoption, latency improvement, compression ratio, or production claim.
