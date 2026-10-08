# Inkscape numeric-position primary use

A fresh primary-model session (seed 991360) set a rectangle's X coordinate to 80 using the visible Selector toolbar. The post-control saved-SVG oracle found exactly one red rectangle at X80/Y50, width40/height30. Selection, units, full-field selection, changed geometry and saved status were visually reviewed before the evaluator opened the SVG.

Six public persistent-X11 MCP calls: observe, select object, select X value, replace with 80 and Enter, save, close. Four input programs, five full image presentations, zero image references, no extra observations or input replay. The updated host showed explicit MCP isError=false on all six responses. Inputs were released; relay exit0; fixture cleanup codes0/1/-15 are retained.

This demonstrates a usable exact-position route when the application exposes a suitable numeric field. It does not establish a universal substitute for dragging, automatic target discovery or a pixel/document conversion. The preceding drag trial scored only rightward movement; this trial scored X80, so they are not matched arms and their call counts/times cannot support a causal comparison.

Host send-to-reply intervals sum to2426.8795ms; first send to final reply spans57702.8171ms. These include host/orchestration boundaries and are not isolated model wait, first useful feedback or exact semantic-completion measurements. Human-tempo and token/cost gains remain unmeasured.

The server used the explicitly selected retained portable archive SHA256 857d8841e4dbeceb8c7ae62a7d58e6ec117feea5285681c67a328e5da4030664 (build source39e7d6d3997fbfa2ebac85261a012c214a7de989), with the current host presentation code. This was not a new runtime build. Exact implementation metadata and host sources are retained.

Run `python3 -O runtime/results/inkscape-numeric-primary-01/verify.py`. It checks archived evidence, actual request sequence, reviews/images, input release, saved geometry and host timeline identities. No new GUI session is started.
