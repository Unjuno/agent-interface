# Attempt 01 STOP — GPU inference passed, output contract failed

The frozen call ran once and completed on RTX 3080. Model and input were on `cuda:0`; CUDA allocation rose from 996,323,840 bytes before generation to 1,004,846,592 after, with a 1,016,208,896-byte peak. The adjacent `nvidia-smi` sample identified the RTX 3080 and showed 37% utilization after the call. Generation took 5,241.953 ms and returned 157 tokens.

The overall attempt is **STOP_GATE_FAILED**, not PASS: the response was wrapped in a Markdown JSON fence, so the raw response is not JSON. After removing the fence, the content parses but `confidence` and `unknown_probability` are strings rather than bounded numbers. The model also did not identify a concrete evidence source. Independent audit: `ATTEMPT01_AUDIT.json`; complete measurements and generated text: `ATTEMPT01_RAW.json`.

This is one local runtime readiness call with synthetic input only. It does not validate report quality or strategic-reporting behavior. No retry was made.
