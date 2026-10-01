ARG BASE_IMAGE=mixed-app-2499-xauth:v4
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements-live.txt /tmp/requirements-live.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages -r /tmp/requirements-live.txt \
    && python3 -c "import PIL, Xlib, openpyxl, numpy; print('live-reader dependencies ready')" \
    && rm -f /tmp/requirements-live.txt

WORKDIR /repo
