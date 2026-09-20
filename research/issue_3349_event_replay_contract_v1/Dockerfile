FROM python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /study
COPY candidate.py cases.json audit.py /study/
RUN python -c "import hashlib,pathlib; p=pathlib.Path('/study/candidate.py'); assert hashlib.sha256(p.read_bytes()).hexdigest() == '4432a6188b5318dc552f050a26ff9e2a5d32bbf9'"
ENTRYPOINT ["python", "/study/audit.py"]

