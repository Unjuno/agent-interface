# #1445 T1 authority-ordering successor A8

Fresh successor to #1441 `STOP_T1_A7_AUTHORITY_ORDERING`; #1441 is not rerun.

Science is inherited unchanged. A8 changes one factor only: close local authority at the 40 ms handback independently of controller completion and gate XTEST admission on the actual send-begin clock. Active transition delivery excludes nominal 40 ms; retained <=40 ms boundary evidence is flushed only after stop + controller join.

Pre-live order: pure/static interleaving discriminator -> synthetic formal audit -> GitHub source readback/freeze -> finite #60 lease -> exactly one excluded TRANSIENT_28 pair -> mandatory reread -> at most one six-pair formal invocation. No retry.
