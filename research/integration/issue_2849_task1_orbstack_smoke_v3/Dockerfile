FROM issue-2849-task1-runtime:20260921@sha256:dff1c7b56201b4c299883655d98aee3b3f8d7c0c6dd1e4ad6320b942fb5d17fb

COPY python-requirements.lock /tmp/python-requirements.lock
RUN python3 -m pip install --break-system-packages --no-cache-dir --no-deps \
    -r /tmp/python-requirements.lock && rm /tmp/python-requirements.lock
