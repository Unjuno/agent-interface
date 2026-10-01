# Pre-run stop record

Allocation: `competence-location-map-3446-20261001-01`  
Recorded retrospectively with the formal result; this is not a candidate failure.

Before the formal candidate was started, the local C: volume reported 0 bytes
free. Docker Desktop remained available (Engine 29.8.0, context
`desktop-linux`); `docker ps` showed no running containers. The container image
and preregistered source were already present, but writing the required raw
result and audit artifacts could not be guaranteed. Candidate execution was
therefore held at the pre-run gate. No image, cache, container, branch, or user
data was removed to create space.

Later, a read-only capacity check showed 284.2 MiB free. The frozen image and
source hashes were rechecked, construction tests passed, and this allocation
was resumed once. The formal candidate and independent audit both exited 0;
their evidence is recorded in `results/3446-competence-location-map-20261001-01/`.

