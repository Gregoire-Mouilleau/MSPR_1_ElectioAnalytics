"""
Module de connexion à la base de données
Gère les connexions PostgreSQL et SQLite
"""

from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from loguru import logger

from src.config import settings

# Base pour les modèles SQLAlchemy
Base = declarative_base()


class DatabaseManager:
    """Gestionnaire de connexion à la base de données"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialise le moteur de base de données"""
        try:
            self.engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=settings.debug
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            logger.info(f"Connexion à la base de données établie: {settings.db_type}")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du moteur de base de données: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test la connexion à la base de données
        
        Returns:
            True si la connexion est réussie, False sinon
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Test de connexion à la base de données réussi")
            return True
        except Exception as e:
            logger.error(f"Test de connexion échoué: {e}")
            return False
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager pour obtenir une session de base de données
        
        Yields:
            Session SQLAlchemy
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur lors de la transaction: {e}")
            raise
        finally:
            session.close()
    
    def create_all_tables(self):
        """Crée toutes les tables définies dans les modèles"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tables de base de données créées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création des tables: {e}")
            raise
    
    def drop_all_tables(self):
        """Supprime toutes les tables (ATTENTION: À utiliser avec précaution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Toutes les tables ont été supprimées")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des tables: {e}")
            raise


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()


def get_db() -> Session:
    """
    Dépendance FastAPI pour obtenir une session de base de données
    
    Yields:
        Session de base de données
    """
    with db_manager.get_session() as session:
        yield session
