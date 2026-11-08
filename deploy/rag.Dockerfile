FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/rag
COPY requirements-runtime.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && groupadd --gid 10002 rag && useradd --uid 10002 --gid 10002 --no-create-home rag
COPY --chown=10002:10002 *.py /app/rag/
COPY --chown=10002:10002 config /app/rag/config
COPY --chown=10002:10002 rag-permissions.json /app/rag/rag-permissions.json
USER 10002:10002
EXPOSE 8765 8766
