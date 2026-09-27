# Actual public dispatch review selection

Source 103011803176fd1fc01010f13a6d81b3d16400bf. WSL Ubuntu, owned Xvfb :147,
primary assistant, one allocation. No sensor or helper model.

Public dispatch focused the explicit fixture, captured the complete 400x180
window, captured the 180x45 green rectangle at (20,75), then released input.
Dispatch returned completed. Public review returned execution_observation_index
1 and a PNG hash equal to the second retained capture. The primary assistant
viewed that image: a green 180x45 rectangle, not the earlier full window.
Program, dispatch JSON (historically named observation.json), review JSON and
both capture artifacts remain unchanged. The owned client/server closed and
the runner exited 0. review itself did not capture or dispatch additional input.

This proves the actual public dispatch-to-review route and final-capture
selection. It does not measure application task success, latency improvement,
model tokens or recovery reliability. The fixture drawing and capture regions
were scripted integration inputs, not model-grounded application actions.
Original file references are historical; manifest excludes itself only.
