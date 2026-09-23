FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglu1-mesa libsdl2-2.0-0 libopenal1 xvfb ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir vizdoom==1.2.3
COPY runner.py audit.py /fixture/
WORKDIR /fixture
CMD ["sh","-lc","python runner.py /out/raw.jsonl && python audit.py /out/raw.jsonl"]