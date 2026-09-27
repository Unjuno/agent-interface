FROM python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends xvfb xauth libx11-6 && rm -rf /var/lib/apt/lists/* && mkdir -p /opt/python-artifacts && python -m pip download --no-deps --dest /opt/python-artifacts python3-xlib==0.15 six==1.17.0 && python -m pip install --no-deps /opt/python-artifacts/* && python -m pip check && sha256sum /opt/python-artifacts/* > /opt/python-artifact-sha256.txt && python -c "import Xlib; import importlib.metadata as m; assert m.version('python3-xlib') == '0.15'; print(Xlib.__file__)"

COPY SCHEDULE.json /opt/study/SCHEDULE.json
COPY study/ /opt/study/study/
WORKDIR /opt/study/study

RUN python -B -m unittest discover -s /opt/study/study -v

CMD ["python", "-B", "runner.py", "--formal", "--out", "/results/formal"]
