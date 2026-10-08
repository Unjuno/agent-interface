# A05 manifest reconciliation

This note records a verification limitation for the original `SHA256SUMS` manifest. It does not alter the frozen candidate outputs, the original manifest, or the posthoc audit.

At commit `ed02dcac9cdb0c1214129508700c512f466819b8`, a fresh `shasum -a 256 -c SHA256SUMS` check from the A05 directory verified 21 listed files and could not read one listed file: `logs/A05-setup.log`. The manifest records its expected SHA-256 as `9f4127943c57a1be363129c9f277e8bcab5ca509c8450430aef2fed874c43606`. The file is absent from the checkout, so that digest remains unverified.

The retained transfer bundle and checkout were searched for a recoverable copy; none was found. No replacement, reconstruction, or empty-file substitution was made. Therefore the original manifest is incomplete as a verification result (21/22 files verified), and the setup-log provenance remains unresolved. The expected digest above is transcribed from the frozen manifest only; it is not evidence that the absent file had that content.
