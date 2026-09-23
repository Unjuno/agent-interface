FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends     chromium inkscape libreoffice-calc xvfb xdotool x11-utils python3 ca-certificates     && rm -rf /var/lib/apt/lists/*
WORKDIR /repo
COPY research/integration/mixed_app_identity_2666_live_v3/identity_preflight.py /repo/identity_preflight.py
ENTRYPOINT ["python3","/repo/identity_preflight.py"]
