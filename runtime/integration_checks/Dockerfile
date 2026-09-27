# Same Python/dependency inputs as .github/workflows/native-mcp-v1.yml.
# Source and writable results are supplied at run time, not baked into the image.
FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY research/live_control/requirements-native-mcp.txt /tmp/requirements-native-mcp.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements-native-mcp.txt Pillow==10.2.0 numpy==1.26.4 python-xlib==0.33
WORKDIR /src
ENTRYPOINT ["python", "runtime/integration_checks/native.py"]
