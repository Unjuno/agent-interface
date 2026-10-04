# Run record

- Exact repository base: `ea5c5cba0bf18b4a78208d0b87e2ee7c48e22310`.
- Candidate: `python3 -B candidate.py` (one invocation only; see `RESULT.json`).
- Candidate: `python3 -B candidate.py` exited 0 and retained `HOLD_ENERGY_SENSOR_UNAVAILABLE` (one sensor probe).
- Auditor v1 and v2 each stopped before writing an audit because raw man-page overstrikes/line wraps were not normalized; both failures are recorded in `AUDIT_ATTEMPT_V1.json` and `AUDIT_ATTEMPT_V2.json`.
- Independent auditor v3: `python3 -B audit_v3.py` exited 0 and confirmed the eligibility HOLD. No candidate or sensor probe was repeated.
- Sensor command attempted without privilege: `/usr/bin/powermetrics -s cpu_power -i 1000 -n 2`.
- No `sudo`, install, GUI, app, model, route, or container invocation. This is a host-only sensor eligibility check; a container would not expose the host measurement surface being qualified.
- No T1 route pilot or energy estimate was performed.
