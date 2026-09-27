# Host-side fixture GET component probe

## H / T / D / C / U

- **H** — The exact historical `gui_suite.fixture_server` GET handler returns
  the ready form without creating/modifying the submitted-output path; output
  mutation is reserved for POST.
- **T** — One host-side component-only allocation,
  `issue2922-fixture-get-host-component-20260927-r1`. Parse historical
  `research/observation_gating/gui_suite.py`, AST-extract only the original
  `fixture_server` function, execute it with its standard-library dependencies,
  then issue one `urllib.request.urlopen` GET to its loopback endpoint. A fresh
  temporary `submitted.txt` path was checked immediately before and after.
  Runtime was macOS host Python 3.14.5. The module was not imported because
  unrelated GUI dependencies (Pillow) are unavailable on the host. Exact
  source SHA-256: `953a078a06d55b9278bd7b31e176404912340a4f13407e1db343b7776645e97f`.
- **D** — HTTP 200, `text/html; charset=utf-8`, 187 response bytes, body
  contained `AI FORM READY`; output path absent before and after; no POST sent.
  Result: `PASS_GET_HANDLER_NO_OUTPUT_MUTATION`.
- **C** — This is a host-only standard-library component check. It does not run
  in a container or through `session_v4`, does not test the session-owned
  endpoint, and does not establish an application/task effect.
- **U** — Whether the integrated historical runtime's private endpoint is
  reachable from its route/session and whether Chromium can request the fixture
  while preserving the no-task boundary remain untested. The pending Docker
  audit request was stopped as `STOP_INFRA_NO_RESPONSE`; no claim is made that
  this host check substitutes for it.

The only request was GET. A POST is deliberately excluded because the
historical handler writes the submitted output file on POST and no task action
was authorized by this preflight.
