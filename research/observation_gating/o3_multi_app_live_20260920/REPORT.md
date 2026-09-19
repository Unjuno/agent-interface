# O3 multi-application live transport

- Governing issue: #2811; successor/source-binding follow-up: #3131
- Image: `agent-interface-2994:20260920`
- Digest: `sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c`
- Fresh execution: Docker `--network none`, Xvfb `:147`, two real GTK fixtures
- Input: Python Xlib/XTEST Ctrl-S targeted to each observed X11 window
- Result: `PASS_O3_MULTI_APP_TRANSPORT_SCOPED`
- app_a XID `2097155`: useful save receipt
- app_b XID `4194307`: partial save receipt with collateral label
- Both had independent capture/arrival timestamps and admitted live gates
- Model calls: 0; network calls: 0

This is a scoped transport/effect-binding result. It does not claim broad GUI success, model-level task success, or arbitrary-window authenticity; #3131 remains the source-window binding follow-up.
