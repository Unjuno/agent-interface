# Formal invocation repair

Formal result `writer-uno-x11-binding-v1-20260916-01` is consumed and must never be rerun. Its one-shot matrix wrapper completed nine of ten planned fresh sessions, then the outer execution envelope reached its 180-second limit before the tenth session. No aggregate was created. The nine completed receipts remain evidence but do not constitute the planned 5+5 formal result.

Successor result ID: `writer-uno-x11-binding-v1-20260916-02`.

The scientific design and all eight execution/source blobs from source freeze `6288256399c5e40ae8c0777002d9b541b0d7dc38` are unchanged. The only repair is invocation checkpointing: execute the same fixed schedule as ten separate `experiment.py` invocations, each in a fresh private Xvfb/Openbox/LibreOffice Writer session, and aggregate only after all ten receipts exist. Fixed order remains `positional-0, activated-0, ..., positional-4, activated-4`. No `-01` session is reused or pooled.

PASS remains: all five positional arms reproduce wrong-target effect; all five activated arms produce exact `A=bookkeeperoffice`, `B=sidecar`; all ten end with empty physical input. A changed positional ordering is retained rather than rescued. No model/provider/network calls.