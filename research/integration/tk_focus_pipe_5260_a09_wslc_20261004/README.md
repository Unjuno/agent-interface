# #5260 A09 — finite private-pipe focus admission

First allocation: target ACK4/4 saved hxy with empty decoy; wrong-target2/2
refused with zero input; NOW4/4 saved xy with decoy h. Original outcome and
warnings: RUN.md and evidence/. This is a private instrumented Tk fixture, not
a public focus guarantee or performance/memory benefit. Prior results unchanged.

Data-only verification (no app/container/input replay):

```powershell
python -B research/integration/tk_focus_pipe_5260_a09_wslc_20261004/verify_packet.py
python -B -m unittest discover -s research/integration/tk_focus_pipe_5260_a09_wslc_20261004 -p 'test_*.py' -q
```

Never invoke host_capture.py --frozen candidate/auditor again. Both commands
were consumed; a new allocation requires separately fixed sources/conditions.
Source freeze44135c00; actual pre-input conditions commita5c51f35. Prospective
conditions were published/read back before input after comment API HTTP403.
SHA256SUMS covers every package file except itself. Verification reconstructs
the first audit and checks saved command/stream/source bindings and corruptions.
Broader roadmap remains open; this does not prove physical input release,
general live feedback/recovery or human tempo. PR/main integration is pending.
