# Playwright/Chromium container construction smoke

- Runtime: OrbStack Docker Engine 29.4.0, linux/arm64.
- Image: `mcr.microsoft.com/playwright@sha256:941cc91e5022880ac1d14ae90b476b624deb6399dbbc28d612d5d5bd7928fcbd`; image ID is the same digest.
- Browser package: local Playwright JavaScript 1.62.1 tree hash `8ff3153fb520f5978e324f08ebc7801d3380c1548033ac8072c9cbf0c2bf7089`.
- Container: `blackwell-6678-a02-browser-smoke-20261003`, ID `65e84e3c4423964c1185365e25e08791609e0a602dfe9a3d361eb02c2c433cac`.
- Command: `docker --context orbstack run --name blackwell-6678-a02-browser-smoke-20261003 --network none --read-only --tmpfs /tmp:rw,nosuid,size=256m --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 1024m --pids-limit 128 -e HOME=/tmp -e NODE_PATH=/opt/pw -e PLAYWRIGHT_MODULE_PATH=/opt/pw/playwright -e PLAYWRIGHT_BROWSERS_PATH=/ms-playwright --mount type=bind,src=/Users/taka/node_modules,dst=/opt/pw,readonly mcr.microsoft.com/playwright@sha256:941cc91e5022880ac1d14ae90b476b624deb6399dbbc28d612d5d5bd7928fcbd node -e '<one-page about:blank smoke>'`
- Exit: 0. Stdout: `{"version":"151.0.7922.34","title":"smoke","browser":"ok"}`.
- Purpose/boundary: verifies that the pinned Linux/arm64 image can load the matching host-installed Playwright package and start Chromium under the declared isolation. It did not render the research fixture, create formal observations, invoke the candidate/auditor, or count toward formal allocation stages. No retry.

The exact post-run Docker inspect object is retained alongside this file. This container was left exited and untouched after evidence capture.
