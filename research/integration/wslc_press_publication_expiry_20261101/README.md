# WSLc Xvfb press after custody publication

Fresh el01 ran the merged guarded backend at main 565ed10161fb4b95c2a4df5c40570223cda26135 on private Xvfb via WSLc, 1 CPU, 1 GiB, network none, image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25. The tested bridge/backend blobs matched main (ff6dc4fa086ba22054eee890816fbf0b7cbc32ba and 2302da74fbabea976f00a294a17a39c7517eaf65). The test supplies an injected blocking publisher and simulated owner/custody callback; it uses real XTEST and an independently connected event window.

A valid-lease positive control delivered down and up events for left button and key a. For each expired condition, the callback returned only after the deadline; the backend refused the press, emitted zero press requests, retained the respective prearmed obligation, and release_all verified neutral. The independent event window observed no late press; pointer button readback and final cleanup were neutral. One trial, both cases passed, exit 0.

This does not test a real application effect, production publisher transport, an actual hung server, cancellation races, a reliability rate, or a hard guarantee after native request submission. Raw runner, predeclared conditions and result are in raw.zip; its isolated container is retained locally. The memory limit did not include swap according to the WSLc warning.
