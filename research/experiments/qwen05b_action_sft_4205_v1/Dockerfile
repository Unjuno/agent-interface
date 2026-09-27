FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
WORKDIR /study
COPY requirements.lock /study/requirements.lock
RUN python -m pip install --no-cache-dir -r /study/requirements.lock
COPY generate.py train.py audit.py test_protocol.py preflight.py /study/
ENTRYPOINT ["python"]
