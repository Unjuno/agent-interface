# Excluded construction and setup log

Issue #4638. No formal Xvfb allocation has started as of this log entry.

## Source provenance

The initial runner, fixture, native libX11 oracle, schedule, and raw-only audit were copied from main's merged #4455 evidence path, research/integration/x11_string8_capture_v1/, at merge commit 142af396a7efec9fa13134d28531fc996174e620. This allocation changes only the pinned Docker environment, version-specific audit decision identifiers, and this preregistration. It does not change shared runtime code or predecessor evidence.

## Local source-test setup

The first excluded unittest invocation used the cached codex-x11-preflight:local image (Python 3.11.16 / Python-Xlib 0.33), a read-only root, and no writable temporary filesystem. Four tests passed; test_auditor_accepts_synthetic_integrity_fixture_and_rejects_corruptions errored because Python could not find a writable /tmp. This is a setup error, not a String8 observation.

The same five source tests then ran in the same image with a private 64 MiB /tmp tmpfs, network disabled, and the source mount read-only: 5/5 passed. This is only a source/harness test; it is not construction on Python-Xlib 0.15 or a formal row.

## Next excluded construction

Build the pinned Python 3.11 Docker image from Dockerfile, acquire and hash the exact Python-Xlib 0.15 distribution inside the image, verify Xvfb/xauth/libX11, run only the two already-declared construction cases, then publish the immutable freeze before any formal session. Preserve any failure verbatim; do not pool construction rows.

## Docker image build attempt 1

The first build pinned the intended Python 3.11-slim base and successfully installed the Debian Xvfb/xauth/libX11 packages. It then stopped with pip error Invalid requirement: plus because the generated Dockerfile contained literal plus signs at the beginning of chained RUN fragments. Exit code 1; no image tag was produced, Python-Xlib 0.15 was not installed, and no Xvfb construction/formal case ran. This is a setup failure, not a scientific result. The Dockerfile chain is corrected and the next attempt is still image construction only.

## Docker image build attempt 2

The corrected build installed Xvfb, xauth, and libX11, then pip reported that python-xlib==0.15 does not exist on the current index (available releases began at 0.16). Exit code 1; no image tag was produced, no library 0.15 package was installed, and no Xvfb construction/formal case ran. This exposed a distribution-name issue, not a scientific outcome. The official PyPI project python3-xlib provides the historical 0.15 distribution; Issue #4638 was corrected before source freeze to pin that exact distribution. See https://pypi.org/project/python3-xlib/.

## Docker image build attempt 3 and selected image

The corrected distribution resolved as python3-xlib 0.15. The selected image is agent-interface-string8-4638:candidate-v1, local image/manifest digest sha256:1c334ebd65f4b1bfe81cc84c90780ea01e6f70c0f7b18cd89c09e03406460238 (linux/amd64). Build completed; the exact five inherited source tests passed 5/5 inside the image. Python is 3.11.16, python3-xlib is 0.15, six is 1.17.0, xvfb is 2:21.1.16-1.3+deb13u4, xauth is 1:1.1.2-1.1, and libx11-6 is 2:1.8.12-1. The downloaded python3-xlib 0.15 sdist SHA256 is dc4245f3ae4aa5949c1d112ee4723901ade37a96721ba9645f2bfa56e5b383f8; six wheel SHA256 is 4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274. The locally built python3_xlib-0.15 wheel SHA256 from the successful build log is 17293e5b6dad0303b1feb6888cecb871e345db412e2ab55f8d58fa8c56301cc8.

A diagnostic inventory command incorrectly used Xvfb -version (unsupported by this X server) and allowed PowerShell to expand a dpkg-query format string. No experiment ran. The corrected package inventory succeeded using dpkg-query -W; package versions are recorded above.

## Excluded Xvfb construction

An initial runner launch failed before creating output because the mounted output root already existed and the runner correctly requires a new leaf directory. No Xvfb/fixture started. The corrected run used a fresh child output path and completed the two prespecified construction cases in this local Docker image with --network none, read-only root, bounded tmpfs, CPU=4 and memory=4 GiB.

Construction outcome: 2/2 complete; one str payload and one bytes payload; one legacy bytes(str) TypeError; candidate/native byte mismatches=0; pixel-oracle mismatches=0; both fixture and Xvfb exits=0; cleanup=2/2; TCP listening=false; Xauthority mode 0600. Construction raw.jsonl SHA256 fd19a0102c7d0381bc98dadac909164ebbe505413e79cc7e45a41a003183bfc5; summary.json SHA256 7c0d1f6d1a9b7a9f1fff654eccda30cfc99d52b4dd138d6abeabe109124902f4. These two rows are excluded and will not be pooled into the 30-case formal matrix.

The hypothesis discriminator and native oracle were exercised successfully at construction only. Formal remains unstarted; source/environment/gate freeze must be published and read back before formal case 0.
