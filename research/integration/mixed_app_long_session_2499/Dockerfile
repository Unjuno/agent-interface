FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends python3 xvfb xdotool x11-utils inkscape libreoffice chromium ca-certificates && rm -rf /var/lib/apt/lists/*
COPY research/integration/mixed_app_long_session_2499/formal_session.py /opt/agent-interface/formal_session.py
ENTRYPOINT ["python3", "/opt/agent-interface/formal_session.py"]