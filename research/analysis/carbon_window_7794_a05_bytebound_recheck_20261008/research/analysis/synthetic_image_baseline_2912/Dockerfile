FROM python:3.11-slim
RUN pip install --no-cache-dir pillow==10.4.0
WORKDIR /exp
COPY synth_eval.py /exp/synth_eval.py
ENTRYPOINT ["python", "/exp/synth_eval.py"]
