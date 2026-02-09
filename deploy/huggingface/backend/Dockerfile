# =============================================================================
# BACKEND — Hugging Face Spaces Dockerfile
# =============================================================================
# Runs the FastAPI backend in standalone mode (in-memory state, no Dapr).
# HF Spaces expects port 7860 by default.
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install standalone requirements (no Dapr SDK needed)
COPY deploy/huggingface/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy backend source code
COPY services/backend/src ./src
COPY services/backend/src/standalone.py ./src/standalone.py

# Enable standalone mode (in-memory state, no Dapr)
ENV STANDALONE_MODE=true
ENV PORT=7860

EXPOSE 7860

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "7860"]
