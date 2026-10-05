FROM sha256:f649ccab8aec3b94e451c6b0037e60fca72d7d7559381f8cd4aa98530b786c55
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3-uno && rm -rf /var/lib/apt/lists/*
USER 65534:65534
