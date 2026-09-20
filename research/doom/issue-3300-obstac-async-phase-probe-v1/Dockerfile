FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglu1-mesa libsdl2-2.0-0 libopenal1 ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir vizdoom==1.2.3
WORKDIR /fixture
COPY research/doom/session_map01_v13.py research/doom/map01_scorer_stdio_adapter_v1.py research/doom/main_thread_scorer_polling_v1.py research/doom/independent_progress_clock_v2.py research/doom/doom_retained_input_backend_v3.py /fixture/
COPY research/doom/issue-3300-obstac-async-phase-probe-v1/runner.py research/doom/issue-3300-obstac-async-phase-probe-v1/audit.py /fixture/
CMD ["sh", "-lc", "python runner.py /out/raw.jsonl && python audit.py /out/raw.jsonl"]
