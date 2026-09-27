FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-tk xvfb xauth \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /bench
COPY benchmark.py /bench/benchmark.py
COPY test_benchmark.py /bench/test_benchmark.py

ENV PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["python3", "/bench/benchmark.py"]
