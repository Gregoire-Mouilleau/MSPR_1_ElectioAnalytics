"""
Pipeline ETL principal
Orchestre l'ensemble du processus Extract, Transform, Load
"""

import pandas as pd
from typing import Optional, Dict, List
from pathlib import Path
from loguru import logger

from src.config import settings, yaml_config
from src.etl.extractor import DataExtractor
from src.etl.cleaner import DataCleaner
from src.etl.transformer import DataTransformer
from src.etl.loader import DataLoader


class ETLPipeline:
    """Pipeline ETL complet pour ElectioAnalytics"""
    
    def __init__(self):
        """Initialise le pipeline ETL"""
        self.extractor = DataExtractor()
        self.cleaner = DataCleaner()
        self.transformer = DataTransformer()
        self.loader = DataLoader()
        
        logger.info("Pipeline ETL initialisé")
    
    def run_elections_pipeline(
        self,
        file_path: str,
        zone_code: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Pipeline spécifique pour les données électorales
        
        Args:
            file_path: Chemin vers le fichier de données électorales
            zone_code: Code de la zone géographique à filtrer
            
        Returns:
            DataFrame traité
        """
        logger.info("=== Début du pipeline Élections ===")
        
        try:
            # EXTRACT
            df = self.extractor.extract_csv(file_path, encoding='utf-8', separator=';')
            logger.info(f"Extraction: {len(df)} lignes")
            
            # CLEAN
            df = self.cleaner.normalize_column_names(df)
            df = self.cleaner.clean_text_columns(df)
            df = self.cleaner.remove_duplicates(df)
            
            # Normalisation des dates
            date_columns = [col for col in df.columns if 'date' in col.lower()]
            if date_columns:
                df = self.cleaner.normalize_dates(df, date_columns)
            
            # TRANSFORM
            if zone_code:
                df = self.transformer.filter_by_geographic_zone(df, zone_code=zone_code)
            
            # Créer colonne année si date disponible
            if 'election_date' in df.columns or 'date' in df.columns:
                date_col = 'election_date' if 'election_date' in df.columns else 'date'
                df = self.transformer.create_year_column(df, date_col)
            
            # LOAD
            self.loader.load_to_database(df, 'elections_results')
            self.loader.load_to_csv(df, 'elections_cleaned.csv')
            
            logger.info("=== Pipeline Élections terminé ===")
            return df
            
        except Exception as e:
            logger.error(f"Erreur dans le pipeline Élections: {e}")
            raise
    
    def run_security_pipeline(
        self,
        file_path: str,
        zone_code: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Pipeline spécifique pour les données de sécurité
        
        Args:
            file_path: Chemin vers le fichier de données de sécurité
            zone_code: Code de la zone géographique à filtrer
            
        Returns:
            DataFrame traité
        """
        logger.info("=== Début du pipeline Sécurité ===")
        
        try:
            # EXTRACT
            df = self.extractor.extract_csv(file_path, encoding='utf-8', separator=';')
            logger.info(f"Extraction: {len(df)} lignes")
            
            # CLEAN
            df = self.cleaner.normalize_column_names(df)
            df = self.cleaner.clean_text_columns(df)
            df = self.cleaner.remove_duplicates(df)
            df = self.cleaner.convert_numeric_strings(df)
            
            # TRANSFORM
            if zone_code:
                df = self.transformer.filter_by_geographic_zone(df, zone_code=zone_code)
            
            # LOAD
            self.loader.load_to_database(df, 'security_indicators')
            self.loader.load_to_csv(df, 'security_cleaned.csv')
            
            logger.info("=== Pipeline Sécurité terminé ===")
            return df
            
        except Exception as e:
            logger.error(f"Erreur dans le pipeline Sécurité: {e}")
            raise
    
    def run_employment_pipeline(
        self,
        file_path: str,
        zone_code: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Pipeline spécifique pour les données d'emploi
        
        Args:
            file_path: Chemin vers le fichier de données d'emploi
            zone_code: Code de la zone géographique à filtrer
            
        Returns:
            DataFrame traité
        """
        logger.info("=== Début du pipeline Emploi ===")
        
        try:
            # EXTRACT
            df = self.extractor.extract_csv(file_path, encoding='utf-8', separator=';')
            logger.info(f"Extraction: {len(df)} lignes")
            
            # CLEAN
            df = self.cleaner.normalize_column_names(df)
            df = self.cleaner.clean_text_columns(df)
            df = self.cleaner.remove_duplicates(df)
            df = self.cleaner.convert_numeric_strings(df)
            
            # TRANSFORM
            if zone_code:
                df = self.transformer.filter_by_geographic_zone(df, zone_code=zone_code)
            
            # LOAD
            self.loader.load_to_database(df, 'employment_data')
            self.loader.load_to_csv(df, 'employment_cleaned.csv')
            
            logger.info("=== Pipeline Emploi terminé ===")
            return df
            
        except Exception as e:
            logger.error(f"Erreur dans le pipeline Emploi: {e}")
            raise
    
    def run_full_pipeline(
        self,
        elections_file: str,
        security_file: str,
        employment_file: str,
        zone_code: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Exécute le pipeline complet pour toutes les sources de données
        
        Args:
            elections_file: Fichier de données électorales
            security_file: Fichier de données de sécurité
            employment_file: Fichier de données d'emploi
            zone_code: Code de la zone géographique
            
        Returns:
            Dictionnaire contenant tous les DataFrames traités
        """
        logger.info("=== DÉBUT DU PIPELINE COMPLET ===")
        
        results = {}
        
        try:
            # Pipeline Élections
            results['elections'] = self.run_elections_pipeline(elections_file, zone_code)
            
            # Pipeline Sécurité
            results['security'] = self.run_security_pipeline(security_file, zone_code)
            
            # Pipeline Emploi
            results['employment'] = self.run_employment_pipeline(employment_file, zone_code)
            
            logger.info("=== PIPELINE COMPLET TERMINÉ ===")
            return results
            
        except Exception as e:
            logger.error(f"Erreur dans le pipeline complet: {e}")
            raise
    
    def process_socioeconomic_files(
        self,
        source_dir: Path,
        output_dir: Path
    ) -> Dict[str, int]:
        """
        Traite tous les fichiers socio-économiques (CSV et Parquet)
        
        Args:
            source_dir: Répertoire contenant les fichiers bruts
            output_dir: Répertoire de sortie pour les fichiers nettoyés
            
        Returns:
            Dictionnaire avec statistiques (success_count, total_rows)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files = list(source_dir.glob("*.csv")) + list(source_dir.glob("*.parquet"))
        
        if not files:
            logger.warning(f"Aucun fichier trouvé dans {source_dir}")
            return {'success_count': 0, 'total_rows': 0}
        
        success_count = 0
        total_rows = 0
        logger.info(f"Fichiers trouvés: {len(files)}")
        
        for file_path in sorted(files):
            logger.info(f"\n  Traitement: {file_path.name}")
            
            try:
                if file_path.suffix == '.parquet':
                    try:
                        df = self.extractor.extract_parquet(file_path)
                    except Exception as e:
                        logger.warning(f"    ⚠ Fichier Parquet ignoré (bibliothèque non disponible)")
                        continue
                else:
                    df = self.extractor.extract_csv(file_path)
                
                initial_rows = len(df)
                logger.info(f"    Lignes: {initial_rows:,} | Colonnes: {len(df.columns)}")
                
                df = self.cleaner.remove_empty_rows_and_columns(df)
                df = self.cleaner.remove_duplicates(df)
                
                cleaned_rows = len(df)
                
                output_filename = f"{file_path.stem}_cleaned.csv"
                output_path = output_dir / output_filename
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(output_path, index=False, encoding='utf-8', sep=';', na_rep='NA')
                
                logger.info(f"    ✓ Sauvegardé: {output_filename} ({cleaned_rows:,} lignes)")
                
                success_count += 1
                total_rows += cleaned_rows
                
            except Exception as e:
                logger.error(f"    ✗ Erreur: {e}")
        
        return {'success_count': success_count, 'total_rows': total_rows, 'total_files': len(files)}
    
    def get_pipeline_status(self) -> Dict:
        """
        Récupère le statut et les statistiques du pipeline
        
        Returns:
            Dictionnaire contenant les métriques du pipeline
        """
        return {
            'extractor': 'ready',
            'cleaner': 'ready',
            'transformer': 'ready',
            'loader': 'ready',
            'database_connection': 'connected' if self.loader._test_db_connection() else 'disconnected'
        }


# Point d'entrée si exécution directe
if __name__ == "__main__":
    logger.info("Exécution du pipeline ETL...")
    
    # Exemple d'utilisation
    pipeline = ETLPipeline()
    
    # Exemple avec fichiers fictifs
    # results = pipeline.run_full_pipeline(
    #     elections_file="elections_data.csv",
    #     security_file="security_data.csv",
    #     employment_file="employment_data.csv",
    #     zone_code="75"
    # )
    
    logger.info("Pipeline prêt à l'emploi!")
