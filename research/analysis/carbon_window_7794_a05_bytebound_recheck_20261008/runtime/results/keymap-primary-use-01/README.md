# Primary use after X11 keymap integration

The primary model used the portable public MCP runtime through one persistent
X11 session, with no helper model or sensor. After observing the empty Tk field,
it entered and saved http://a_b under JP, reviewed the returned image, requested
the private fixture's US remap, then selected/replaced the text and saved
http://c_d. It reviewed the final field and saved label before closing. The
independent saved-file oracle ran only after control ended and matched http://c_d.

Four MCP calls: observe, dispatch, dispatch, close. Two input programs, three
full images, three explicit caller review receipts, no input retries or extra
observations. Explicit 20-ms inter-character gaps and 100-ms post-save waits were
caller choices, not measured optimal defaults. This is a tiny construction task,
not general desktop reliability, live game performance or human-tempo proof.

Archive build source: 1b23026ab598fe9410da08df4094726c596d77f2.
Allocation source: bd6606980d669d94abb7e32bfeac432c10a54e5c.
The tested archive backend matched main after integration. The raw archive
includes the build, manifest, host source, requests/replies, images, reviews,
application event log, final saved file, setup scripts and cleanup.

The first allocation failed before app launch due to duplicate env arguments in
the fixture launcher; its failure and cleanup are retained. The corrected
allocation used a new directory after the first process had exited.

Host timing: first send through last reply 69.096 s; summed request-outstanding
intervals 2.496 s; presentation callbacks within that span 0.010 s; other host
intervals 66.590 s. Those other intervals include orchestration and caller gaps
and are not measured model reasoning. First useful feedback, semantic completion,
provider token usage and cost remain unavailable. No matched speedup is claimed.

Also retained is the preceding private-Xvfb preflight microbenchmark: 20 warmups,
200 measured iterations per arm, alternating order. Baseline median 0.0097735 ms,
candidate median 0.0876565 ms. This measures a single preflight and its added
barrier, not full dispatch or task latency. Raw samples/provenance are included.

Run python3 runtime/results/keymap-primary-use-01/verify.py to verify retained
bytes, the call sequence, final saved effect and completed cleanup without
extracting the archive or issuing input. Review receipts are caller declarations,
not an automated semantic oracle.
