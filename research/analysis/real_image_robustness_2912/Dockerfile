FROM python:3.11-slim
RUN pip install --no-cache-dir pillow==10.4.0
WORKDIR /exp
COPY robust_eval.py /exp/robust_eval.py
ENTRYPOINT ["python", "/exp/robust_eval.py"]
