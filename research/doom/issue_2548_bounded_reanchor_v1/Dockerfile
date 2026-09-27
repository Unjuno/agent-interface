FROM python:3.13.5-slim-bookworm@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_INDEX=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libasound2 libgl1 libglu1-mesa libopenal1 libsdl2-2.0-0 \
        libxtst6 openbox wmctrl x11-utils xauth xdotool xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY wheels/ /opt/wheels/
RUN python -m pip install --no-index --no-deps /opt/wheels/*.whl \
    && python -c "import openpyxl, numpy, PIL, Xlib, vizdoom; assert vizdoom.__version__ == '1.3.0'; print('offline imports OK', vizdoom.__version__)" \
    && rm -rf /opt/wheels

WORKDIR /work
