"""
Module d'extraction de données depuis diverses sources
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union
import chardet
import logging

logger = logging.getLogger(__name__)

try:
    from src.config import settings
except ImportError:
    from pathlib import Path
    class Settings:
        data_raw_path = Path('data/raw')
    settings = Settings()


class DataExtractor:
    """Classe responsable de l'extraction des données brutes"""
    
    def __init__(self, source_path: Optional[Path] = None):
        """
        Initialise l'extracteur de données
        
        Args:
            source_path: Chemin vers le répertoire contenant les données brutes
        """
        self.source_path = source_path or settings.data_raw_path
        logger.info(f"DataExtractor initialisé avec source: {self.source_path}")
    
    def detect_encoding(self, file_path: Path) -> str:
        """
        Détecte automatiquement l'encodage d'un fichier
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Encodage détecté
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(100000)
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
                logger.info(f"Encodage détecté: {encoding} (confiance: {confidence:.2%})")
                return encoding if encoding else 'utf-8'
        except Exception as e:
            logger.warning(f"Impossible de détecter l'encodage: {e}, utilisation de utf-8")
            return 'utf-8'
    
    def detect_separator(self, file_path: Path, encoding: str = 'utf-8') -> str:
        """
        Détecte automatiquement le séparateur d'un fichier CSV/TXT
        
        Args:
            file_path: Chemin vers le fichier
            encoding: Encodage du fichier
            
        Returns:
            Séparateur détecté
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                first_line = f.readline()
                separators = [';', '\t', ',', '|']
                counts = {sep: first_line.count(sep) for sep in separators}
                separator = max(counts, key=counts.get)
                if counts[separator] > 0:
                    logger.info(f"Séparateur détecté: '{separator}'")
                    return separator
                return ','
        except Exception as e:
            logger.warning(f"Impossible de détecter le séparateur: {e}, utilisation de ','")
            return ','
    
    def extract_csv(
        self, 
        file_path: Union[str, Path], 
        encoding: Optional[str] = None,
        separator: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrait les données d'un fichier CSV/TXT avec détection automatique
        
        Args:
            file_path: Chemin vers le fichier CSV
            encoding: Encodage du fichier (détecté automatiquement si None)
            separator: Séparateur de colonnes (détecté automatiquement si None)
            **kwargs: Paramètres supplémentaires pour pd.read_csv
            
        Returns:
            DataFrame pandas contenant les données
        """
        try:
            file_path = Path(file_path)
            
            logger.info(f"Extraction CSV/TXT depuis: {file_path}")
            
            if encoding is None:
                encoding = self.detect_encoding(file_path)
            if separator is None:
                separator = self.detect_separator(file_path, encoding)
            
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=separator,
                    on_bad_lines='skip',
                    engine='python',  
                    quoting=3, 
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"Échec avec engine='python', tentative avec 'c': {e}")
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    sep=separator,
                    low_memory=False,
                    on_bad_lines='skip',
                    **kwargs
                )
            
            logger.info(f"Fichier extrait avec succès: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
            
        except FileNotFoundError:
            logger.error(f"Fichier introuvable: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction CSV: {e}")
            raise
    
    def extract_excel(
        self,
        file_path: Union[str, Path],
        sheet_name: Union[str, int] = 0,
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrait les données d'un fichier Excel (.xlsx, .xls)
        
        Args:
            file_path: Chemin vers le fichier Excel
            sheet_name: Nom ou index de la feuille à extraire
            **kwargs: Paramètres supplémentaires pour pd.read_excel
            
        Returns:
            DataFrame pandas contenant les données
        """
        try:
            file_path = Path(file_path)
            
            logger.info(f"Extraction Excel depuis: {file_path}, feuille: {sheet_name}")
            
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                **kwargs
            )
            
            logger.info(f"Excel extrait avec succès: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
            
        except FileNotFoundError:
            logger.error(f"Fichier introuvable: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction Excel: {e}")
            raise
    
    def extract_json(
        self,
        file_path: Union[str, Path],
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrait les données d'un fichier JSON
        
        Args:
            file_path: Chemin vers le fichier JSON
            **kwargs: Paramètres supplémentaires pour pd.read_json
            
        Returns:
            DataFrame pandas contenant les données
        """
        try:
            file_path = Path(file_path)
            
            logger.info(f"Extraction JSON depuis: {file_path}")
            
            df = pd.read_json(
                file_path,
                **kwargs
            )
            
            logger.info(f"JSON extrait avec succès: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
            
        except FileNotFoundError:
            logger.error(f"Fichier introuvable: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction JSON: {e}")
            raise
    
    def extract_parquet(
        self,
        file_path: Union[str, Path],
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrait les données d'un fichier Parquet
        
        Args:
            file_path: Chemin vers le fichier Parquet
            **kwargs: Paramètres supplémentaires pour pd.read_parquet
            
        Returns:
            DataFrame pandas contenant les données
        """
        try:
            file_path = Path(file_path)
            
            logger.info(f"Extraction Parquet depuis: {file_path}")
            
            df = pd.read_parquet(
                file_path,
                **kwargs
            )
            
            logger.info(f"Parquet extrait avec succès: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
            
        except FileNotFoundError:
            logger.error(f"Fichier introuvable: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction Parquet: {e}")
            raise
    
    def extract_auto(
        self,
        file_path: Union[str, Path],
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrait automatiquement les données selon l'extension du fichier
        Supporte: .csv, .txt, .xlsx, .xls, .json, .parquet
        
        Args:
            file_path: Chemin vers le fichier
            **kwargs: Paramètres supplémentaires pour l'extraction
            
        Returns:
            DataFrame pandas contenant les données
        """
        file_path = Path(file_path)
        
        if not file_path.is_absolute():
            if file_path.exists():
                pass  
            elif (self.source_path / file_path).exists():
                file_path = self.source_path / file_path
            elif len(file_path.parts) >= 2 and file_path.parts[0] == 'data' and file_path.parts[1] == 'raw':
                file_path = Path.cwd() / file_path
            else:
                file_path = self.source_path / file_path
        
        extension = file_path.suffix.lower()
        
        logger.info(f"Détection automatique du format: {extension}")
        
        if extension in ['.csv', '.txt']:
            return self.extract_csv(file_path, **kwargs)
        elif extension in ['.xlsx', '.xls']:
            return self.extract_excel(file_path, **kwargs)
        elif extension == '.json':
            return self.extract_json(file_path, **kwargs)
        elif extension == '.parquet':
            return self.extract_parquet(file_path, **kwargs)
        else:
            raise ValueError(f"Format de fichier non supporté: {extension}")
    
    def extract_from_database(
        self,
        query: str,
        connection_string: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrait les données depuis une base de données SQL
        
        Args:
            query: Requête SQL
            connection_string: Chaîne de connexion (utilise settings par défaut)
            **kwargs: Paramètres supplémentaires pour pd.read_sql
            
        Returns:
            DataFrame pandas contenant les données
        """
        try:
            from src.database import get_engine
            
            engine = get_engine()
            if engine is None:
                raise RuntimeError("Moteur de base de données non disponible")
            
            logger.info(f"Extraction depuis base de données: {query[:100]}...")
            
            df = pd.read_sql(
                query,
                engine,
                **kwargs
            )
            
            logger.info(f"Données extraites: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction depuis la base de données: {e}")
            raise
