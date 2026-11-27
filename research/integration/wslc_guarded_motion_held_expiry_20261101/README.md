# WSLc held button during guarded motion expiry

Fresh ek01 used WSLc with private Xvfb, image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25, 1 CPU, 1 GiB, no network, and the execution backend from main 4c24da67ab933bb9c0d08cf2f536a2250cd5e2e4. Admission, focus, target observation and the test-local custody callback were simulated. The actual X11 execution loop, guarded motion fence, cleanup and session wrapper ran against the private X server.

An independent X connection observed left down before expiry. After the simulated observation crossed the deadline, the execution returned failure at motion, with the later right-button operation unexecuted. Its one program emission was the cleanup left-button release. The cleanup receipt verified neutral, and independent X readback found both buttons up and the pointer still at (10,10); readback was 11.563 ms after expiry. Final cleanup also verified neutral. Container exit was 0.

This one controlled attempt joins a held input, expiry and release. It does not establish arbitrary real application effects, a hard transport deadline, production visual admission, cancellation races or reliability. Conditions, runner and raw result are retained in raw.zip; the stopped isolated container remains local. This is distinct from ej01/ej02 in the preceding experiment.
