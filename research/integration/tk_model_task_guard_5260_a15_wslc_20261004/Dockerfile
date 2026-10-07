# Local construction base: inspect the tag before each build and require image
# sha256:217851fe68e7340cd6301e6d1a1bd79d2c7b6cb4d13eb444a06fabaf0fde3417.
# The formal experiment must invoke the resulting immutable image ID, not tag.
FROM ai-x20-tk-5260:20261003-a02
USER 0:0
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN /usr/local/bin/python -m pip install --no-cache-dir \
    mcp==1.30.0 pydantic==2.13.5 Pillow==12.3.0 \
    jsonschema==4.26.0 python-xlib==0.33 \
    && /usr/local/bin/python -m pip freeze --all > /opt/a15-dependency-lock.txt \
    && /usr/local/bin/python -c "import tkinter, Xlib, PIL, mcp, pydantic, jsonschema"
USER 65534:65534
WORKDIR /src
ENTRYPOINT ["/usr/local/bin/python", "-B"]
