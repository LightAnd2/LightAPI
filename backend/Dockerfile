# LightAI backend — FastAPI + APScheduler + PyTorch LSTM
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install CPU-only PyTorch first (far smaller than the default CUDA build),
# then the remaining dependencies (torch is already satisfied).
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# Persist the SQLite DB and trained model weights outside the image layer.
# Mount a volume at /data and set DATABASE_URL=sqlite:////data/lightai.db.
VOLUME ["/data"]

EXPOSE 8000

# Honour $PORT if the host injects one (Fly/Render/Cloud Run), else default 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
