FROM python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016
LABEL org.unjuno.study="ISSUE59-FOCUS-REPEAT-OWNER-T0-20261002-01"
ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends xvfb x11-utils x11-xserver-utils && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir --no-compile python-xlib==0.33
RUN python --version && python -c "import importlib.metadata; print('python-xlib', importlib.metadata.version('python-xlib'))" && command -v Xvfb && command -v xset && dpkg-query -W -f='${Package}=${Version}\n' xvfb x11-utils x11-xserver-utils