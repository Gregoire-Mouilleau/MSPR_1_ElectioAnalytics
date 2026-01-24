"""
Module de nettoyage et normalisation des données
Fonctions génériques de nettoyage applicables à tous les datasets
"""

import pandas as pd
import numpy as np
from typing import List, Union, Optional, Dict
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Classe responsable du nettoyage et de la normalisation des données"""
    
    def __init__(self):
        logger.info("DataCleaner initialisé")
    
    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalise les noms de colonnes (minuscules, underscores, sans accents)
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            DataFrame avec colonnes normalisées
        """
        logger.info("Normalisation des noms de colonnes")
        
        def normalize_name(name: str) -> str:
            # Convertir en minuscules
            name = str(name).lower()
            # Remplacer les espaces et caractères spéciaux par des underscores
            name = re.sub(r'[^\w\s-]', '', name)
            name = re.sub(r'[-\s]+', '_', name)
            # Supprimer les accents
            accents = {
                'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                'à': 'a', 'â': 'a', 'ä': 'a',
                'ù': 'u', 'û': 'u', 'ü': 'u',
                'ô': 'o', 'ö': 'o',
                'î': 'i', 'ï': 'i',
                'ç': 'c'
            }
            for accent, replace in accents.items():
                name = name.replace(accent, replace)
            return name
        
        df.columns = [normalize_name(col) for col in df.columns]
        logger.info(f"Colonnes normalisées: {list(df.columns)}")
        return df
    
    def normalize_dates(
        self, 
        df: pd.DataFrame, 
        date_columns: List[str],
        target_format: str = '%Y-%m-%d',
        errors: str = 'coerce'
    ) -> pd.DataFrame:
        """
        Normalise les colonnes de dates dans un format standard
        
        Args:
            df: DataFrame à nettoyer
            date_columns: Liste des colonnes contenant des dates
            target_format: Format de date cible
            errors: Comportement en cas d'erreur ('coerce', 'raise', 'ignore')
            
        Returns:
            DataFrame avec dates normalisées
        """
        logger.info(f"Normalisation des dates: {date_columns}")
        
        for col in date_columns:
            if col not in df.columns:
                logger.warning(f"Colonne {col} introuvable, ignorée")
                continue
            
            try:
                # Tentative de conversion automatique
                df[col] = pd.to_datetime(df[col], errors=errors)
                
                # Comptage des valeurs invalides
                invalid_count = df[col].isna().sum()
                if invalid_count > 0:
                    logger.warning(f"Colonne {col}: {invalid_count} dates invalides converties en NaT")
                
                logger.info(f"Colonne {col} normalisée en datetime")
                
            except Exception as e:
                logger.error(f"Erreur lors de la normalisation de {col}: {e}")
        
        return df
    
    def clean_text_columns(
        self, 
        df: pd.DataFrame, 
        text_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Nettoie les colonnes textuelles (trim, casse, caractères spéciaux)
        
        Args:
            df: DataFrame à nettoyer
            text_columns: Liste des colonnes textuelles (si None, détecte automatiquement)
            
        Returns:
            DataFrame avec textes nettoyés
        """
        if text_columns is None:
            text_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        logger.info(f"Nettoyage de {len(text_columns)} colonnes textuelles")
        
        for col in text_columns:
            if col not in df.columns:
                continue
            
            # Suppression des espaces superflus
            df[col] = df[col].astype(str).str.strip()
            
            # Remplacement des multiples espaces par un seul
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
            
            # Suppression des caractères de contrôle
            df[col] = df[col].str.replace(r'[\x00-\x1f\x7f-\x9f]', '', regex=True)
        
        logger.info(f"{len(text_columns)} colonnes nettoyées")
        return df
    
    def remove_empty_rows_and_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Supprime les lignes et colonnes entièrement vides
        
        Args:
            df: DataFrame à nettoyer
            
        Returns:
            DataFrame sans lignes ni colonnes vides
        """
        initial_rows = len(df)
        initial_cols = len(df.columns)
        
        df = df.dropna(axis=1, how='all')
        
        df = df.dropna(axis=0, how='all')
        
        rows_removed = initial_rows - len(df)
        cols_removed = initial_cols - len(df.columns)
        
        if rows_removed > 0 or cols_removed > 0:
            logger.info(f"Lignes vides supprimées: {rows_removed}, Colonnes vides supprimées: {cols_removed}")
        
        return df
    
    def handle_missing_values(
        self, 
        df: pd.DataFrame,
        strategy: Dict[str, Union[str, float, int]] = None,
        threshold: float = 0.5
    ) -> pd.DataFrame:
        """
        Gère les valeurs manquantes selon différentes stratégies
        
        Args:
            df: DataFrame à nettoyer
            strategy: Dictionnaire {colonne: stratégie} où stratégie peut être:
                     - 'drop': Supprime les lignes
                     - 'mean': Remplace par la moyenne
                     - 'median': Remplace par la médiane
                     - 'mode': Remplace par le mode
                     - valeur: Remplace par une valeur spécifique
            threshold: Seuil de suppression de colonnes (proportion de valeurs manquantes)
            
        Returns:
            DataFrame nettoyé
        """
        logger.info("Gestion des valeurs manquantes")
        
        # Rapport initial
        missing_before = df.isna().sum()
        missing_pct = (missing_before / len(df)) * 100
        
        logger.info(f"Valeurs manquantes par colonne:\n{missing_pct[missing_pct > 0]}")
        
        # Suppression des colonnes avec trop de valeurs manquantes
        cols_to_drop = missing_pct[missing_pct > (threshold * 100)].index.tolist()
        if cols_to_drop:
            logger.warning(f"Suppression de {len(cols_to_drop)} colonnes: {cols_to_drop}")
            df = df.drop(columns=cols_to_drop)
        
        # Application des stratégies spécifiques
        if strategy:
            for col, strat in strategy.items():
                if col not in df.columns:
                    continue
                
                if strat == 'drop':
                    df = df.dropna(subset=[col])
                elif strat == 'mean':
                    df[col].fillna(df[col].mean(), inplace=True)
                elif strat == 'median':
                    df[col].fillna(df[col].median(), inplace=True)
                elif strat == 'mode':
                    df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else None, inplace=True)
                else:
                    df[col].fillna(strat, inplace=True)
                
                logger.info(f"Stratégie '{strat}' appliquée à {col}")
        
        # Rapport final
        missing_after = df.isna().sum().sum()
        logger.info(f"Valeurs manquantes restantes: {missing_after}")
        
        return df
    
    def remove_duplicates(
        self, 
        df: pd.DataFrame,
        subset: Optional[List[str]] = None,
        keep: str = 'first'
    ) -> pd.DataFrame:
        """
        Supprime les doublons
        
        Args:
            df: DataFrame à nettoyer
            subset: Colonnes à considérer pour la détection de doublons
            keep: Quelle occurrence garder ('first', 'last', False pour tout supprimer)
            
        Returns:
            DataFrame sans doublons
        """
        initial_count = len(df)
        df = df.drop_duplicates(subset=subset, keep=keep)
        removed_count = initial_count - len(df)
        
        logger.info(f"Doublons supprimés: {removed_count} ({(removed_count/initial_count)*100:.2f}%)")
        return df
    
    def convert_numeric_strings(
        self, 
        df: pd.DataFrame,
        numeric_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Convertit les colonnes numériques stockées comme strings
        
        Args:
            df: DataFrame à nettoyer
            numeric_columns: Liste des colonnes à convertir
            
        Returns:
            DataFrame avec types numériques
        """
        if numeric_columns is None:
            # Détection automatique des colonnes potentiellement numériques
            numeric_columns = []
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].str.replace(r'[,\s]', '', regex=True).str.match(r'^-?\d+\.?\d*$').any():
                    numeric_columns.append(col)
        
        logger.info(f"Conversion en numérique: {numeric_columns}")
        
        for col in numeric_columns:
            if col not in df.columns:
                continue
            
            try:
                # Nettoyage des séparateurs de milliers et conversion
                df[col] = df[col].astype(str).str.replace(r'[,\s]', '', regex=True)
                df[col] = df[col].str.replace(',', '.', regex=False)  # Conversion décimales
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                logger.info(f"Colonne {col} convertie en numérique")
                
            except Exception as e:
                logger.error(f"Erreur lors de la conversion de {col}: {e}")
        
        return df
    
    def standardize_categories(
        self, 
        df: pd.DataFrame,
        category_mappings: Dict[str, Dict[str, str]]
    ) -> pd.DataFrame:
        """
        Standardise les valeurs catégorielles (uniformisation de la casse, synonymes)
        
        Args:
            df: DataFrame à nettoyer
            category_mappings: {colonne: {valeur_source: valeur_cible}}
            
        Returns:
            DataFrame avec catégories standardisées
        """
        logger.info(f"Standardisation de {len(category_mappings)} colonnes catégorielles")
        
        for col, mapping in category_mappings.items():
            if col not in df.columns:
                continue
            
            df[col] = df[col].replace(mapping)
            logger.info(f"Colonne {col} standardisée avec {len(mapping)} mappings")
        
        return df
    
    def get_data_quality_report(self, df: pd.DataFrame) -> Dict:
        """
        Génère un rapport de qualité des données
        
        Args:
            df: DataFrame à analyser
            
        Returns:
            Dictionnaire contenant les métriques de qualité
        """
        report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values': df.isna().sum().to_dict(),
            'missing_percentage': ((df.isna().sum() / len(df)) * 100).to_dict(),
            'duplicates': df.duplicated().sum(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / (1024**2), 2)
        }
        
        logger.info(f"Rapport de qualité généré pour {report['total_rows']} lignes")
        return report
    
    def validate_data_coherence(
        self,
        df: pd.DataFrame,
        validation_rules: Optional[Dict[str, callable]] = None
    ) -> pd.DataFrame:
        """
        Valide la cohérence des données selon des règles métier
        
        Args:
            df: DataFrame à valider
            validation_rules: Dictionnaire {nom_règle: fonction_validation}
                            La fonction doit retourner un masque boolean
            
        Returns:
            DataFrame avec seulement les lignes valides
            
        Example:
            rules = {
                'age_valide': lambda df: (df['age'] >= 18) & (df['age'] <= 120),
                'date_coherente': lambda df: df['date_debut'] <= df['date_fin']
            }
        """
        logger.info("Validation de la cohérence des données")
        
        if validation_rules is None:
            logger.warning("Aucune règle de validation fournie")
            return df
        
        initial_count = len(df)
        
        for rule_name, rule_func in validation_rules.items():
            try:
                mask = rule_func(df)
                invalid_count = (~mask).sum()
                
                if invalid_count > 0:
                    logger.warning(
                        f"Règle '{rule_name}': {invalid_count} lignes invalides détectées"
                    )
                    # Marquer les lignes invalides
                    df.loc[~mask, f'_invalid_{rule_name}'] = True
                else:
                    logger.info(f"Règle '{rule_name}': Toutes les lignes valides")
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'application de la règle '{rule_name}': {e}")
        
        # Optionnel : supprimer les lignes avec au moins une règle invalide
        invalid_cols = [col for col in df.columns if col.startswith('_invalid_')]
        if invalid_cols:
            invalid_rows = df[invalid_cols].any(axis=1)
            removed_count = invalid_rows.sum()
            df = df[~invalid_rows]
            df = df.drop(columns=invalid_cols)
            logger.info(
                f"{removed_count} lignes incohérentes supprimées "
                f"({(removed_count/initial_count)*100:.2f}%)"
            )
        
        return df
    
    def clean_pipeline(
        self,
        df: pd.DataFrame,
        config: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Pipeline complet de nettoyage avec configuration
        
        Args:
            df: DataFrame à nettoyer
            config: Configuration du nettoyage avec les clés:
                   - normalize_columns: bool
                   - date_columns: List[str]
                   - numeric_columns: List[str]
                   - remove_duplicates: bool
                   - duplicate_subset: List[str]
                   - missing_strategy: Dict
                   - validation_rules: Dict
                   
        Returns:
            DataFrame nettoyé
        """
        logger.info("=" * 50)
        logger.info("Démarrage du pipeline de nettoyage")
        logger.info("=" * 50)
        
        if config is None:
            config = {}
        
        # Rapport initial
        initial_report = self.get_data_quality_report(df)
        logger.info(f"État initial: {initial_report['total_rows']} lignes, "
                   f"{initial_report['total_columns']} colonnes")
        
        # Étape 1: Normalisation des noms de colonnes
        if config.get('normalize_columns', True):
            df = self.normalize_column_names(df)
        
        # Étape 2: Suppression des doublons
        if config.get('remove_duplicates', True):
            df = self.remove_duplicates(
                df,
                subset=config.get('duplicate_subset')
            )
        
        # Étape 3: Nettoyage des colonnes textuelles
        df = self.clean_text_columns(df)
        
        # Étape 4: Conversion des colonnes numériques
        if config.get('numeric_columns'):
            df = self.convert_numeric_strings(
                df,
                numeric_columns=config.get('numeric_columns')
            )
        
        # Étape 5: Normalisation des dates
        if config.get('date_columns'):
            df = self.normalize_dates(
                df,
                date_columns=config.get('date_columns')
            )
        
        # Étape 6: Gestion des valeurs manquantes
        df = self.handle_missing_values(
            df,
            strategy=config.get('missing_strategy'),
            threshold=config.get('missing_threshold', 0.5)
        )
        
        # Étape 7: Standardisation des catégories
        if config.get('category_mappings'):
            df = self.standardize_categories(
                df,
                category_mappings=config.get('category_mappings')
            )
        
        # Étape 8: Validation de cohérence
        if config.get('validation_rules'):
            df = self.validate_data_coherence(
                df,
                validation_rules=config.get('validation_rules')
            )
        
        # Rapport final
        final_report = self.get_data_quality_report(df)
        logger.info("=" * 50)
        logger.info(f"État final: {final_report['total_rows']} lignes, "
                   f"{final_report['total_columns']} colonnes")
        logger.info(f"Données supprimées: "
                   f"{initial_report['total_rows'] - final_report['total_rows']} lignes "
                   f"({((initial_report['total_rows'] - final_report['total_rows']) / initial_report['total_rows'])*100:.2f}%)")
        logger.info("Pipeline de nettoyage terminé avec succès")
        logger.info("=" * 50)
        
        return df


# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration de test
    cleaner = DataCleaner()
    
    # Exemple de DataFrame de test
    test_data = {
        'Nom Prénom': ['  Jean Dupont  ', 'Marie Martin', 'Jean Dupont', 'Pierre Durand  '],
        'Age': ['25', '30,5', 'abc', '45'],
        'Date Naissance': ['1999-01-15', '15/03/1994', 'invalide', '1979-12-01'],
        'Ville': ['Paris', 'lyon', 'PARIS', 'Marseille'],
        'Revenu': ['25 000', '30000', None, '45,000']
    }
    
    df_test = pd.DataFrame(test_data)
    
    print("=" * 60)
    print("AVANT NETTOYAGE")
    print("=" * 60)
    print(df_test)
    print(f"\nTypes: {df_test.dtypes.to_dict()}")
    
    # Configuration du nettoyage
    clean_config = {
        'normalize_columns': True,
        'remove_duplicates': True,
        'date_columns': ['date_naissance'],
        'numeric_columns': ['age', 'revenu'],
        'missing_strategy': {'revenu': 'mean'},
        'category_mappings': {
            'ville': {'lyon': 'Lyon', 'PARIS': 'Paris'}
        },
        'validation_rules': {
            'age_valide': lambda df: (df['age'] >= 18) & (df['age'] <= 120)
        }
    }
    
    # Nettoyage
    df_clean = cleaner.clean_pipeline(df_test, config=clean_config)
    
    print("\n" + "=" * 60)
    print("APRÈS NETTOYAGE")
    print("=" * 60)
    print(df_clean)
    print(f"\nTypes: {df_clean.dtypes.to_dict()}")
