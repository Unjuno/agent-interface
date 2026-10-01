# Portable runtime image review: actual WSL run

Built from committed source 23aae0c8728a053fe22d6c3e0221153ce02c909c on Windows.
Artifact: 118813 bytes, SHA256 8865230dfb25aca0d853a5f8cf6058000a1c6bc3115adc73076bbb37e4b24a06.
The deterministic build manifest retains exact source hashes; the generated
zipapp is reproducible and not checked into this evidence directory.

The same zipapp ran both observe and review in WSL against one owned Xvfb :147.
Both CLI processes and the fixture exited 0; server/client cleanup completed.
Primary assistant viewed the returned PNG and confirmed white text and green
rectangle. Direct pre/post raw pixels and public capture hash are identical
(comparison.json). input_dispatched=false. The image PNG hash also matches the
previous source-module run, though this is not a matched latency experiment.

Windows local distribution/review tests: 6 passed. Remote latest Native MCP
runs were queued when inspected; no remote pass is claimed for this source.
No task-success, speed, token, sensor or formal research-adoption claim.
Original runtime paths remain historical references; no fresh authority.
