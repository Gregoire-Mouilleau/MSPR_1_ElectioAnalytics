"""
API FastAPI pour ElectioAnalytics
Point d'entrée principal de l'API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Création de l'application FastAPI
app = FastAPI(
    title="ElectioAnalytics API",
    description="API pour l'analyse prédictive électorale - Lyon 7e arrondissement",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route de santé
@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "name": "ElectioAnalytics API",
        "version": "1.0.0",
        "status": "running",
        "description": "API pour l'analyse prédictive électorale",
        "zone": "Lyon 7e arrondissement, Rhône (69)",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "database": "/db/status"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ElectioAnalytics API",
        "database": "PostgreSQL",
        "environment": os.getenv("ENV", "development")
    }

@app.get("/db/status")
async def database_status():
    """Vérification de la connexion à la base de données"""
    try:
        # TODO: Vérifier la connexion réelle à PostgreSQL
        db_config = {
            "host": os.getenv("DB_HOST", "postgres"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "electio_analytics"),
            "user": os.getenv("DB_USER", "postgres"),
        }
        return {
            "status": "connected",
            "config": db_config,
            "message": "Configuration OK - Connexion à implémenter"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de connexion: {str(e)}")

@app.get("/api/info")
async def api_info():
    """Informations sur l'API"""
    return {
        "project": "ElectioAnalytics",
        "type": "ETL Pipeline & Predictive Analytics",
        "technologies": {
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "etl": "Python + Pandas",
            "ml": "Scikit-learn",
            "bi": "Metabase",
            "notebooks": "Jupyter Lab",
            "dashboard": "Streamlit"
        },
        "geographic_zone": {
            "type": "arrondissement",
            "code": "69007",
            "name": "Lyon 7e arrondissement",
            "department": "Rhône (69)"
        }
    }

# Point d'entrée pour le démarrage
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
