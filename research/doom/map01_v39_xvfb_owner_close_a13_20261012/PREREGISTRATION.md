# A13 preregistration - exact-main owner close over private loopback

H: Exact current-main V4->V3->V12 admits `a` to one focused isolated Xvfb client, then closes with matching KeyRelease, observer key-up, verified terminal owner release and stopped thread.

T: Xvfb `:136`, TCP only inside a private network namespace; client uses `127.0.0.1:136`. One key admission, then wrapper close and raw-only audit.

D: PASS_METHOD_SCOPED requires frozen main sources and every independent audit check. Incomplete/setup trace STOP; complete mismatch FAIL. Candidate once and auditor once.

C/U: Synthetic server only; no physical key, app consumption, task feedback, threat response, recovery or task completion.

Base main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
