# Configured child target ancestry

The primary trial in `../post-dispatch-inspection-01` found that a Tk child ID accepted input but failed focused-family inspection. This change resolves the configured child to its first managed ancestor, retains both IDs and the ancestry path in review evidence, and preserves explicit target selection. Original managed-client configurations keep their evidence shape. The original failed allocation is unchanged.

The traversal is bounded to 64 IDs and refuses cycles, missing/destroyed windows, reaching the root without a managed client, or excessive ancestry. A focused unrelated application still refuses. The existing one-use review compares the complete evidence again; a changed configured path invalidates it. This is X11 metadata, not authenticated application identity or input authority.

## Actual primary use and recovery

A fresh two-editor allocation on portable build `67b764aee6249eb1a3d10e065c9702773c37aa4d` configured the original Tk child IDs. The primary entered `http://m_n` into Left and received a summary containing the child-to-managed ancestry without any implicit rebind. It explicitly reviewed the managed Left candidate, changing binding revision 1 to 2; the returned capture matched the reviewed image bytes. All later inspections retained the original configured family root and ancestry.

The first image showed `ttp://m_n`: initial h was missing despite the 50ms click delay and 20ms character gaps. The primary noticed this from the image. A repair request using uppercase `HOME` was refused before program execution with zero program emissions; inspection was skipped. The corrected `Home` chord followed by one h repaired only the missing prefix. A separate save then visibly showed `saved:http://m_n`. Independent post-close scoring confirmed that exact saved value. Right remained blank and has no audited events or saved effect.

Seven calls: observe, input/inspect, explicit target review, refused repair, corrected repair/inspect, save/inspect, close. Three input programs completed; one was refused. Five images were explicitly reviewed (four image presentations and one exact reviewed-image reference). One partial-input repair and one caller key-name correction are part of the result; this was not an error-free typing trial. Passive audit preserves the initial nine printable characters, Home, h and Ctrl-S. No entire text replay or helper model was used.

The native suite was running concurrently for part of the trial. This was functional self-use, not a latency comparison; do not assign a cause to the missing character or infer that a fixed delay is reliable. Read-only diagnosis independently shows both child and managed configurations resolving to the same actual managed window.

## Verification

`python3 -O runtime/results/managed-target-ancestry-01/verify.py` checks all archived hashes, call order, successful summary contexts against stored reports, no implicit rebind, explicit review selection, preserved child ancestry, zero-emission repair refusal, saved value, passive event sequence, untouched Right, image-review bindings, terminal children and native log hashes. It does not interpret image pixels or establish speed/model cost.

The archive includes the fixture, allocation, all raw requests/replies and images, reviews, passive events, saved effect, cleanup, host timing, diagnosis, portable build and local native checks (294 protocol and 132 harness tests). Earlier failures stay in the previous evidence bundle.
