# Interrupted 250 ms navigation trial

This allocation tested the same seed (991337) and exact portable runtime as
`guarded-navigation-batch-primary-01`, changing only the final navigation wait
from 100 to 250 ms. The port, process lifetime, model context and host scheduling
were different; this was not a randomized or matched latency comparison.

The preserved host has 12 requests and 12 replies. Primary review receipts
confirmed SAVED pages for tasks 1 and 2, each after an additional observation.
Navigation 6 and 11 returned images recorded as destination-unconfirmed;
observation 7 confirmed task 2. Call 12 has presentation callbacks but no primary
review receipt. Do not manufacture a review or independent success from it.

A user-authorized WSL-wide restart subsequently terminated this environment.
Post-restart inspection found no fixture/relay/Xvfb process and transport exit
code 1. The raw evidence does not establish the exact moment or cause of that
transport exit. No finish, independent evaluation, submission-history copy,
cleanup report, explicit interface close or post-close read was retained.
This is an interrupted allocation, not a six-task pass or an intrinsic failure
of the 250 ms setting. The host timeline correctly remains partial.

No runtime default changes follow from this record. Increasing a fixed wait did
not guarantee destination-ready images in the observed prefix. It also cannot
explain the delays after Save, whose 100 ms wait was unchanged. Root cause,
matched efficiency, useful-feedback latency, semantic completion latency, actual
model tokens/cost and human tempo remain unmeasured.

raw.tar.gz preserves all 184 files found in the original allocation plus its
predeclared plan, fixture and exact runtime artifact. Original files were not
modified. manifest.json binds every archive member. host-timing.json is a
post-restart read-only reconstruction, not a fabricated terminal event.
Run `python3 -O runtime/results/guarded-navigation-delay250-interrupted-01/verify.py`
from the repository root. A PASS verifies preservation and the partial report;
it does not mean the GUI task passed. Any continuation requires a fresh allocation.
