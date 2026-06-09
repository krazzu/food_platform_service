FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# Pre-download fastembed model at build time (ONNX, no torch/CUDA needed)
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Install playwright browsers
RUN playwright install chromium --with-deps

COPY . .

RUN mkdir -p /app/data && chmod +x /app/start.sh

CMD ["/app/start.sh"]
