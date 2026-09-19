FROM python:3.11-slim
RUN pip install --no-cache-dir pillow==10.4.0
WORKDIR /exp
COPY image_eval.py /exp/image_eval.py
ENTRYPOINT ["python", "/exp/image_eval.py"]
