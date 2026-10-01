FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglu1-mesa libsdl2-2.0-0 libopenal1 xvfb xauth openbox ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir vizdoom==1.3.0
WORKDIR /fixture
COPY research/doom/session_map01_v13.py research/doom/map01_scorer_stdio_adapter_v1.py research/doom/main_thread_scorer_polling_v1.py research/doom/independent_progress_clock_v2.py research/doom/doom_retained_input_backend_v3.py /fixture/
COPY research/doom/fixtures/map01-threat-contact-v2/fixture.json research/doom/fixtures/map01-threat-contact-v2/save.png /fixture/fixture/
COPY research/doom/issue-3300-phase-stratified-map01-v2/runner.py /fixture/runner.py
CMD ["sh", "-lc", "Xvfb :99 -screen 0 1280x1024x24 -ac >/tmp/xvfb.log 2>&1 & export DISPLAY=:99; sleep 1; openbox >/tmp/openbox.log 2>&1 & sleep 1; exec python -u runner.py /out/raw.jsonl"]
