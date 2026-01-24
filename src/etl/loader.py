"""
Module de chargement des données
Gère l'insertion des données dans PostgreSQL et la sauvegarde en fichiers
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import text
    from src.config import settings
    from src.database import db_manager
except ImportError:
    logger.warning("SQLAlchemy non disponible, les fonctions de base de données seront désactivées")
    class Settings:
        data_processed_path = Path('data/processed')
    settings = Settings()
    db_manager = None


class DataLoader:
    """Classe responsable du chargement des données vers les destinations"""
    
    def __init__(self, output_path: Optional[Path] = None):
        """
        Initialise le loader de données
        
        Args:
            output_path: Chemin vers le répertoire de sortie
        """
        self.output_path = output_path or settings.data_processed_path
        logger.info(f"DataLoader initialisé avec sortie: {self.output_path}")
    
    def load_to_database(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: str = 'electio_analytics',
        if_exists: str = 'append',
        batch_size: int = 1000
    ) -> int:
        """
        Charge un DataFrame dans PostgreSQL
        
        Args:
            df: DataFrame à charger
            table_name: Nom de la table de destination
            schema: Schéma de la base de données
            if_exists: Comportement si la table existe ('fail', 'replace', 'append')
            batch_size: Taille des batches pour l'insertion
            
        Returns:
            Nombre de lignes insérées
        """
        logger.info(f"Chargement vers la table {schema}.{table_name}")
        
        try:
            # Vérifier la connexion
            if not db_manager.test_connection():
                raise ConnectionError("Impossible de se connecter à la base de données")
            
            # Charger les données
            rows_inserted = df.to_sql(
                name=table_name,
                con=db_manager.engine,
                schema=schema,
                if_exists=if_exists,
                index=False,
                chunksize=batch_size,
                method='multi'
            )
            
            logger.info(
                f"{len(df)} lignes insérées dans {schema}.{table_name}"
            )
            
            # Log dans la table etl_logs
            self._log_etl_execution(
                pipeline_name=f"load_{table_name}",
                status='success',
                records_processed=len(df),
                records_success=len(df),
                records_failed=0
            )
            
            return len(df)
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement dans la base: {e}")
            
            # Log de l'erreur
            self._log_etl_execution(
                pipeline_name=f"load_{table_name}",
                status='failed',
                records_processed=len(df),
                records_success=0,
                records_failed=len(df),
                error_message=str(e)
            )
            
            raise
    
    def load_to_csv(
        self,
        df: pd.DataFrame,
        filename: str,
        subfolder: Optional[str] = None,
        **kwargs
    ) -> Path:
        """
        Sauvegarde un DataFrame en CSV
        
        Args:
            df: DataFrame à sauvegarder
            filename: Nom du fichier de sortie
            subfolder: Sous-dossier optionnel (ex: 'legislatives', 'presidentielles')
            **kwargs: Paramètres supplémentaires pour to_csv
            
        Returns:
            Chemin du fichier créé
        """
        if subfolder:
            output_dir = self.output_path / subfolder
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / filename
        else:
            output_file = self.output_path / filename
        
        logger.info(f"Sauvegarde CSV: {output_file}")
        
        try:
            df.to_csv(
                output_file,
                index=False,
                encoding='utf-8',
                sep=';',
                na_rep='NA',
                **kwargs
            )
            
            logger.info(f"CSV sauvegardé: {len(df)} lignes, {output_file.stat().st_size / 1024:.2f} KB")
            return output_file
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde CSV: {e}")
            raise
    
    def load_to_excel(
        self,
        df: pd.DataFrame,
        filename: str,
        sheet_name: str = 'Data',
        **kwargs
    ) -> Path:
        """
        Sauvegarde un DataFrame en Excel
        
        Args:
            df: DataFrame à sauvegarder
            filename: Nom du fichier de sortie
            sheet_name: Nom de la feuille Excel
            **kwargs: Paramètres supplémentaires pour to_excel
            
        Returns:
            Chemin du fichier créé
        """
        output_file = self.output_path / filename
        
        logger.info(f"Sauvegarde Excel: {output_file}")
        
        try:
            df.to_excel(
                output_file,
                sheet_name=sheet_name,
                index=False,
                **kwargs
            )
            
            logger.info(f"Excel sauvegardé: {len(df)} lignes, {output_file.stat().st_size / 1024:.2f} KB")
            return output_file
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde Excel: {e}")
            raise
    
    def load_to_json(
        self,
        df: pd.DataFrame,
        filename: str,
        orient: str = 'records',
        **kwargs
    ) -> Path:
        """
        Sauvegarde un DataFrame en JSON
        
        Args:
            df: DataFrame à sauvegarder
            filename: Nom du fichier de sortie
            orient: Format d'orientation du JSON
            **kwargs: Paramètres supplémentaires pour to_json
            
        Returns:
            Chemin du fichier créé
        """
        output_file = self.output_path / filename
        
        logger.info(f"Sauvegarde JSON: {output_file}")
        
        try:
            df.to_json(
                output_file,
                orient=orient,
                force_ascii=False,
                indent=2,
                **kwargs
            )
            
            logger.info(f"JSON sauvegardé: {len(df)} lignes, {output_file.stat().st_size / 1024:.2f} KB")
            return output_file
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde JSON: {e}")
            raise
    
    def _log_etl_execution(
        self,
        pipeline_name: str,
        status: str,
        records_processed: int,
        records_success: int,
        records_failed: int,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Enregistre l'exécution ETL dans la table de logs
        
        Args:
            pipeline_name: Nom du pipeline
            status: Statut de l'exécution
            records_processed: Nombre de lignes traitées
            records_success: Nombre de lignes réussies
            records_failed: Nombre de lignes échouées
            error_message: Message d'erreur éventuel
            metadata: Métadonnées supplémentaires
        """
        try:
            with db_manager.get_session() as session:
                query = text("""
                    INSERT INTO electio_analytics.etl_logs (
                        pipeline_name, status, records_processed,
                        records_success, records_failed, error_message, metadata
                    ) VALUES (
                        :pipeline_name, :status, :records_processed,
                        :records_success, :records_failed, :error_message, :metadata::jsonb
                    )
                """)
                
                session.execute(query, {
                    'pipeline_name': pipeline_name,
                    'status': status,
                    'records_processed': records_processed,
                    'records_success': records_success,
                    'records_failed': records_failed,
                    'error_message': error_message,
                    'metadata': str(metadata) if metadata else None
                })
                
                logger.debug(f"Log ETL enregistré: {pipeline_name} - {status}")
                
        except Exception as e:
            logger.warning(f"Impossible d'enregistrer le log ETL: {e}")
    
    def execute_sql_file(self, sql_file: Union[str, Path]):
        """
        Exécute un fichier SQL
        
        Args:
            sql_file: Chemin vers le fichier SQL
        """
        sql_file = Path(sql_file)
        
        if not sql_file.exists():
            raise FileNotFoundError(f"Fichier SQL introuvable: {sql_file}")
        
        logger.info(f"Exécution du fichier SQL: {sql_file}")
        
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            with db_manager.get_session() as session:
                session.execute(text(sql_content))
            
            logger.info(f"Fichier SQL exécuté avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du fichier SQL: {e}")
            raise
