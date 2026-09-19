FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends chromium xvfb python3 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY . /fixture/
WORKDIR /fixture
CMD ["sh","-lc","mkdir -p /out && python3 formal_runner.py && python3 audit.py /out/raw.jsonl"]
# rerun formal after audit correction
