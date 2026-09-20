FROM agent-interface-map01-clock-review-fixed:20260920
RUN apt-get update \
    && apt-get install -y --no-install-recommends strace=6.1-0.1 \
    && strace --version \
    && rm -rf /var/lib/apt/lists/*
