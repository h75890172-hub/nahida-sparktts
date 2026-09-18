ARG PYTORCH_IMAGE=pytorch/pytorch:2.7.1-cuda11.8-cudnn9-runtime
FROM ${PYTORCH_IMAGE}

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HUB_DISABLE_XET=1

ARG PIP_INDEX_URL=https://pypi.org/simple

WORKDIR /app

COPY requirements.txt requirements-docker.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install --index-url "${PIP_INDEX_URL}" \
        -r requirements.txt -r requirements-docker.txt

COPY infer.py nahida_tts.py nahida_webui.py ./
COPY sparktts ./sparktts

RUN mkdir -p /app/outputs

ENV MODEL_PATH=/models
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7861
ENV GRADIO_INBROWSER=0

EXPOSE 7861

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7861', timeout=5)"

CMD ["python", "-u", "nahida_webui.py"]
