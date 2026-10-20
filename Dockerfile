FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/appuser \
    PATH="/home/appuser/.local/bin:$PATH" \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true

# Install curl for container HEALTHCHECK and emoji font support
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Run as dedicated non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Cache dependency layer
COPY --chown=appuser:appuser requirements.txt .
USER appuser
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application assets, source, data tables, and configs
COPY --chown=appuser:appuser .streamlit/ .streamlit/
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser data/processed/ data/processed/
COPY --chown=appuser:appuser data/ai/ data/ai/
COPY --chown=appuser:appuser app.py streamlit_app.py pyproject.toml README.md LICENSE ./

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/healthz || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
