# Plan — native X11 tight-loop text pacing v1

The first lowering adapter was rejected before freeze because per-character repeated `Execute` calls created ~19 ms natural spacing, making 0/1 ms indistinguishable. This candidate instead forks the exact frozen native-X11 source (`ca141254...`; backend blob `ed8186...`) into this new namespace and injects strict lowercase ASCII directly inside one native `Execute` loop.

Development calibration established that the discriminator works: 0 ms produced 0/16 exact Calc strings with ~58.8 us median within-text start interval, while 1 ms produced 16/16 exact with ~1.214 ms interval. These are development findings only and are not formal evidence.

Formal after source freeze uses fixed order `0,12,1 ms`; one fresh private Xvfb/Openbox/LibreOffice Calc/XLSX per arm; same 16-string repeated-character corpus; separate post-execution openpyxl scorer; stale text must be rejected with zero injected events; terminal release required; no formal arm reruns. The matrix continues after a semantically failing arm so the 0 ms negative cannot block positive controls.

Per-character native call duration and within-text start interval are retained. PASS transfer requires 1 ms and 12 ms exact durable semantics plus all control gates. 0 ms is retained whatever its outcome. If 1 ms fails, downgrade the prior candidate without rescue. If 0 ms passes, retain it as implementation-specific counterevidence rather than asserting pacing is universally unnecessary.
