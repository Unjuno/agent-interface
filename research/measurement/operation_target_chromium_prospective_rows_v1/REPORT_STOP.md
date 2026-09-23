# #1582 preformal Chromium construction stop

Decision: **PREFORMAL_CONSTRUCTION_STOP_CHROMIUM_URL_POLICY**. Scientific disposition: **NONE**.

The planned prospective real-Chromium row collection stopped before source freeze and before any formal row. The local HTTP fixture itself returned HTTP 200, but Chromium rendered `chrome-error://chromewebdata/` with an organization-blocked message. Adding `--no-proxy-server` did not change the result. A separate `file://` control was also blocked.

The container's managed Chromium policy at `/etc/chromium/policies/managed/000_policy_merge.json` has SHA-256 `3b740260e337305aaef268e6c63af8fa2796057ce46f43df5ae5a3949e085e86` and contains `URLBlocklist: ["*"]`. No attempt was made to modify, bypass or disable the managed policy.

Accounting: formal0, reruns0, model/provider calls0, task-input actions0. No scientific source was frozen and no Chromium row is counted toward #1015.

A legitimate successor must use a real application that is permitted in the execution environment (for example private XTerm or LibreOffice) while preserving the #1132 row contract and #1566 missing-class objective. Do not silently replace the blocked Chromium allocation under the same task ID.
