FROM python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
COPY requirements.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir --no-deps --require-hashes -r /tmp/requirements.lock \
    && python -c 'import numpy; assert numpy.__version__ == "1.26.4"'
ENV OPENBLAS_NUM_THREADS=1
