FROM python:3.12-slim-bookworm
RUN python -m pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
WORKDIR /work
ENTRYPOINT ["python"]
