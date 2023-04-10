FROM python:3.8

WORKDIR /app
COPY requirements.txt /app

# Use the cache if requirements.txt hasn't changed
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

ENTRYPOINT ["python", "kubernetes_orchestrator.py"]
CMD []