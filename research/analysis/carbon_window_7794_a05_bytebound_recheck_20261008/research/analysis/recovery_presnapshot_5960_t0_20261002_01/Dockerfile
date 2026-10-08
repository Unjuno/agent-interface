FROM python:3.12-slim
WORKDIR /study
COPY . .
RUN python -m unittest -v test_t0.py
CMD ["sh", "-c", "python run_candidate.py && python independent_audit.py"]
