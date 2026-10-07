FROM python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
WORKDIR /opt/agent-interface-wslc-build-smoke
COPY payload.txt /opt/agent-interface-wslc-build-smoke/payload.txt
COPY probe.py /opt/agent-interface-wslc-build-smoke/probe.py
ENTRYPOINT ["python", "-B", "/opt/agent-interface-wslc-build-smoke/probe.py"]
