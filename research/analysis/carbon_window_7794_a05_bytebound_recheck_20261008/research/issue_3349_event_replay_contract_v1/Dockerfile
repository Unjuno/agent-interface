FROM python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /study
COPY candidate.py cases.json audit.py /study/
RUN python -c "import hashlib,pathlib; p=pathlib.Path('/study/candidate.py'); assert hashlib.sha256(p.read_bytes()).hexdigest() == '4e700b05c60626e73070eb6f5883d9341c8b1374996d45f08e5766fc6cb0f463'"
ENTRYPOINT ["python", "/study/audit.py"]

