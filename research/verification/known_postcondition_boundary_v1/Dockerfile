FROM python:3.12-slim
WORKDIR /work
COPY research/verification/known_postcondition_boundary_v1 /work
CMD ["sh", "-lc", "python experiment.py /out/result && python audit.py /out/result"]
