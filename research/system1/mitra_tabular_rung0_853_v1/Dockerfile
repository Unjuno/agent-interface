FROM python:3.12-slim-bookworm
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    CUDA_VISIBLE_DEVICES="" \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1
COPY requirements.txt /src/requirements.txt
RUN python -m pip install --no-cache-dir --index-url https://pypi.org/simple --extra-index-url https://download.pytorch.org/whl/cpu -r /src/requirements.txt \
    && python -m pip check \
    && python -m pip freeze > /opt/requirements.freeze
WORKDIR /src
ENTRYPOINT ["python", "runner.py"]
