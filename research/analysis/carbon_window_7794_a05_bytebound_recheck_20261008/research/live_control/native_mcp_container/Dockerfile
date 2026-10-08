# Private X11 research runtime used by the native MCP adapter.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pil python3-numpy python3-openpyxl python3-xlib python3-tk \
    xvfb openbox x11-utils xauth wmctrl libreoffice-calc inkscape fonts-liberation ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY research/live_control/requirements-native-mcp.txt /tmp/requirements-native-mcp.txt
RUN python3 -m venv --system-site-packages /opt/mcp \
    && /opt/mcp/bin/pip install --no-cache-dir -r /tmp/requirements-native-mcp.txt
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace:/workspace/research/live_control
WORKDIR /workspace
ENTRYPOINT ["/opt/mcp/bin/python", "research/live_control/native_mcp_v1.py"]
