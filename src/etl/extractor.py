"""
Module d'extraction des données
Gère le chargement des fichiers CSV, Excel, JSON depuis différentes sources
"""

import pandas as pd
from pathlib import Path
from typing import Union, List, Optional
from loguru import logger

from src.config import settings


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
    
    def extract_csv(
        self, 
        file_path: Union[str, Path], 
        encoding: str = 'utf-8',
        separator: str = ',',
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrait les données d'un fichier CSV
        
        Args:
            file_path: Chemin vers le fichier CSV
            encoding: Encodage du fichier (utf-8, latin1, etc.)
            separator: Séparateur de colonnes (,, ;, etc.)
            **kwargs: Paramètres supplémentaires pour pd.read_csv
            
        Returns:
            DataFrame pandas contenant les données
        """
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.source_path / file_path
            
            logger.info(f"Extraction CSV depuis: {file_path}")
            
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=separator,
                low_memory=False,
                **kwargs
            )
            
            logger.success(f"CSV extrait avec succès: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
            
        except FileNotFoundError:
            logger.error(f"Fichier introuvable: {file_path}")
            raise
        except pd.errors.EmptyDataError:
            logger.warning(f"Fichier vide: {file_path}")
            return pd.DataFrame()
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
        Extrait les données d'un fichier Excel
        
        Args:
            file_path: Chemin vers le fichier Excel
            sheet_name: Nom ou index de la feuille à lire
            **kwargs: Paramètres supplémentaires pour pd.read_excel
            
        Returns:
            DataFrame pandas contenant les données
        """
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.source_path / file_path
            
            logger.info(f"Extraction Excel depuis: {file_path}, feuille: {sheet_name}")
            
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                **kwargs
            )
            
            logger.success(f"Excel extrait avec succès: {len(df)} lignes, {len(df.columns)} colonnes")
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
            if not file_path.is_absolute():
                file_path = self.source_path / file_path
            
            logger.info(f"Extraction JSON depuis: {file_path}")
            
            df = pd.read_json(file_path, **kwargs)
            
            logger.success(f"JSON extrait avec succès: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
            
        except FileNotFoundError:
            logger.error(f"Fichier introuvable: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction JSON: {e}")
            raise
    
    def extract_multiple(
        self,
        file_patterns: List[str],
        file_type: str = 'csv',
        **kwargs
    ) -> pd.DataFrame:
        """
        Extrait et concatène plusieurs fichiers du même type
        
        Args:
            file_patterns: Liste de patterns de fichiers (glob)
            file_type: Type de fichier ('csv', 'excel', 'json')
            **kwargs: Paramètres supplémentaires pour l'extraction
            
        Returns:
            DataFrame pandas concaténant tous les fichiers
        """
        dataframes = []
        
        for pattern in file_patterns:
            files = list(self.source_path.glob(pattern))
            logger.info(f"Trouvé {len(files)} fichiers correspondant à '{pattern}'")
            
            for file_path in files:
                try:
                    if file_type == 'csv':
                        df = self.extract_csv(file_path, **kwargs)
                    elif file_type == 'excel':
                        df = self.extract_excel(file_path, **kwargs)
                    elif file_type == 'json':
                        df = self.extract_json(file_path, **kwargs)
                    else:
                        raise ValueError(f"Type de fichier non supporté: {file_type}")
                    
                    dataframes.append(df)
                except Exception as e:
                    logger.error(f"Erreur lors de l'extraction de {file_path}: {e}")
                    continue
        
        if not dataframes:
            logger.warning("Aucune donnée extraite")
            return pd.DataFrame()
        
        result = pd.concat(dataframes, ignore_index=True)
        logger.success(f"Total extrait: {len(result)} lignes depuis {len(dataframes)} fichiers")
        return result
    
    def get_file_info(self, file_path: Union[str, Path]) -> dict:
        """
        Récupère les informations sur un fichier
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Dictionnaire contenant les métadonnées du fichier
        """
        file_path = Path(file_path)
        if not file_path.is_absolute():
            file_path = self.source_path / file_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {file_path}")
        
        stat = file_path.stat()
        return {
            'name': file_path.name,
            'path': str(file_path),
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'extension': file_path.suffix,
            'modified_time': stat.st_mtime
        }
