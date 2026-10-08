FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-tk xvfb xauth \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /arena
COPY engine.py arena.py test_engine.py gui_smoke.py /arena/
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["xvfb-run", "-a", "python3", "arena.py", "--suite", "full", "--clock", "realtime", "--report", "/tmp/arena-v1-report.json"]
