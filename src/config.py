"""
Configuration centralisée de l'application
Charge les variables d'environnement et le fichier config.yaml
"""

import os
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from loguru import logger

# Charger les variables d'environnement
load_dotenv()

# Chemins de base
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"


class Settings(BaseSettings):
    """Configuration de l'application via variables d'environnement"""
    
    # Application
    app_name: str = os.getenv("APP_NAME", "ElectioAnalytics-ETL")
    env: str = os.getenv("ENV", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", 8000))
    
    # Database
    db_type: str = os.getenv("DB_TYPE", "postgresql")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_name: str = os.getenv("DB_NAME", "electio_analytics")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres123")
    
    # Paths
    data_raw_path: Path = Path(os.getenv("DATA_RAW_PATH", str(DATA_DIR / "raw")))
    data_processed_path: Path = Path(os.getenv("DATA_PROCESSED_PATH", str(DATA_DIR / "processed")))
    data_temp_path: Path = Path(os.getenv("DATA_TEMP_PATH", str(DATA_DIR / "temp")))
    logs_path: Path = Path(os.getenv("LOGS_PATH", str(LOGS_DIR)))
    
    # ETL
    batch_size: int = int(os.getenv("BATCH_SIZE", 1000))
    max_workers: int = int(os.getenv("MAX_WORKERS", 4))
    
    # Geographic Zone
    target_geographic_zone: str = os.getenv("TARGET_GEOGRAPHIC_ZONE", "departement_75")
    
    @property
    def database_url(self) -> str:
        """Génère l'URL de connexion à la base de données"""
        if self.db_type == "postgresql":
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif self.db_type == "sqlite":
            return f"sqlite:///{self.data_raw_path / 'electio.db'}"
        else:
            raise ValueError(f"Type de base de données non supporté: {self.db_type}")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_yaml_config(config_file: str = "config.yaml") -> Dict[str, Any]:
    """
    Charge la configuration depuis le fichier YAML
    
    Args:
        config_file: Nom du fichier de configuration
        
    Returns:
        Dict contenant la configuration
    """
    config_path = CONFIG_DIR / config_file
    
    if not config_path.exists():
        logger.warning(f"Fichier de configuration {config_path} introuvable. Utilisation des valeurs par défaut.")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            logger.info(f"Configuration chargée depuis {config_path}")
            return config
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        return {}


# Instance globale des settings
settings = Settings()

# Chargement de la configuration YAML
yaml_config = load_yaml_config()

# Configuration du logger
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logger.add(
    settings.logs_path / "electio_{time:YYYY-MM-DD}.log",
    rotation="100 MB",
    retention="30 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)

# Création des répertoires nécessaires
for path in [settings.data_raw_path, settings.data_processed_path, settings.data_temp_path]:
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Répertoire créé/vérifié: {path}")

logger.info(f"Configuration chargée - Environnement: {settings.env}")
