# GPU pilot-03 STOP after call 1

The first fresh-seed call completed: `qwen2.5:3b / metadata_only`, producing 16 case rows. Its full request/response and exact JSONL source lines were recovered from the runner's final STOP payload and retained in `call-01.json`, `calls.json`, and `raw.jsonl`. The row file SHA-256 was independently computed from those exact retained lines (recorded in this commit).

The event had been redirected into the runner's internal stdout capture instead of the live controller stream. The process then saw closed stdin rather than the controller's GitHub ACK and stopped before call 2. The remaining five calls were not issued. Ollama's call-adjacent `ollama ps` evidence reported `100% GPU` on the RTX 3080 for this model; the later `nvidia-smi` sample was 0% after inference, so it is not treated as peak-utilization evidence.

This allocation is partial and unaudited. No pilot-level behavior conclusion is claimed. Do not retry or fill the remaining calls under this freeze; any complete replication needs a new issue, fresh seeds, and a tested streaming/ack controller before inference.
