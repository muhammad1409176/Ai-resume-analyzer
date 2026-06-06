FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set Memory Optimization Environment Variables
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV PYTORCH_CPU_ALLOC_CONF=expandable_segments:True

COPY requirements.txt .

# 1. Install torch CPU-only first (saves ~1.5GB of image size and avoids GPU runtime bloat)
# 2. Install other requirements
# 3. Pre-download models to avoid startup RAM spikes
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm \
    && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

EXPOSE 8000

# Use a single worker and no-reload to keep memory footprint minimal
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
