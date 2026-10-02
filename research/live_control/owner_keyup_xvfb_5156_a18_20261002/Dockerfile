FROM python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
LABEL org.unjuno.study="MAP01-OWNER-KEYUP-BRACKET-5156-WSLC-20261002-18"
ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends xvfb x11-utils && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir --no-compile python-xlib==0.33
RUN python -V && python -c "import importlib.metadata; print('python-xlib', importlib.metadata.version('python-xlib'))" && command -v Xvfb && dpkg-query -W -f='${Package}=${Version}\n' xvfb x11-utils xserver-common
