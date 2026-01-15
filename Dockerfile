# ============================================
# Stage de base avec Python et dépendances communes
# ============================================
FROM python:3.11-slim as base
LABEL maintainer="ElectioAnalytics Team"
LABEL description="ETL Pipeline et API pour l'analyse prédictive électorale"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# ============================================
# Stage API (FastAPI)
# ============================================
FROM base as api
COPY src/ /app/src/
COPY config/ /app/config/S
COPY .env.example /app/.env
RUN mkdir -p /app/data/raw /app/data/processed /app/data/temp /app/logs
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ============================================
# Jupyter Lab
# ============================================
FROM base as jupyter

RUN pip install jupyter jupyterlab ipywidgets matplotlib seaborn plotly
COPY src/ /app/src/
COPY config/ /app/config/
RUN mkdir -p /app/notebooks /app/data /app/logs
EXPOSE 8888

RUN jupyter lab --generate-config && \
    echo "c.ServerApp.ip = '0.0.0.0'" >> ~/.jupyter/jupyter_lab_config.py && \
    echo "c.ServerApp.allow_root = True" >> ~/.jupyter/jupyter_lab_config.py && \
    echo "c.ServerApp.open_browser = False" >> ~/.jupyter/jupyter_lab_config.py

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]


# ============================================
# Stage Streamlit Dashboard
# ============================================
FROM base as streamlit
RUN pip install streamlit plotly altair
COPY src/ /app/src/
COPY config/ /app/config/
COPY streamlit_app/ /app/streamlit_app/
RUN mkdir -p /app/data /app/logs
EXPOSE 8501

RUN mkdir -p ~/.streamlit && \
    echo "[server]" > ~/.streamlit/config.toml && \
    echo "headless = true" >> ~/.streamlit/config.toml && \
    echo "port = 8501" >> ~/.streamlit/config.toml && \
    echo "enableCORS = false" >> ~/.streamlit/config.toml

CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
