FROM python:3.14-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends tk xvfb x11-xkb-utils \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir python-xlib==0.33
WORKDIR /work
CMD ["python", "-B", "research/x11_midprogram_keymap_5236_formal05_save_diagnostic_20261001/diagnose.py"]
