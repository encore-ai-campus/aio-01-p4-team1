FROM python:3.12-slim@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30
WORKDIR /opt/oke-rag
RUN pip install --no-cache-dir "psycopg[binary]==3.3.7"
COPY . .
ENV PYTHONDONTWRITEBYTECODE=1 SEARCH_MODE=live
EXPOSE 8765
CMD ["python", "tools/search_http.py", "--host", "0.0.0.0", "--port", "8765"]
