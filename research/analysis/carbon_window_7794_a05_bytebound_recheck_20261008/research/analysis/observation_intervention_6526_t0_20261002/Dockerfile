FROM python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libtk8.6 \
        tk8.6 \
        x11-apps \
        xauth \
        x11-utils \
        xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /study
ENTRYPOINT ["python", "-B", "/src/preflight_smoke.py"]
