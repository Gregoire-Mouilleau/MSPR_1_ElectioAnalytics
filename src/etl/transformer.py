"""
Module de transformation des données
Applique les transformations métier spécifiques au projet
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Union
import logging

logger = logging.getLogger(__name__)

try:
    from src.config import yaml_config
except ImportError:
    yaml_config = {'geographic': {}}


class DataTransformer:
    """Classe responsable de la transformation des données"""
    
    def __init__(self):
        self.geographic_config = yaml_config.get('geographic', {})
        logger.info("DataTransformer initialisé")
    
    # ============================================================================
    # MÉTHODES SPÉCIFIQUES AUX DONNÉES ÉLECTORALES
    # ============================================================================
    
    def identify_election_type(self, df: pd.DataFrame) -> str:
        """
        Identifie automatiquement le type d'élection à partir des colonnes
        
        Args:
            df: DataFrame à analyser
            
        Returns:
            Type d'élection ('presidentielles', 'legislatives', 'europeennes', 'unknown')
        """
        columns_lower = [col.lower() for col in df.columns]
        
        if any('président' in col or 'presid' in col for col in columns_lower):
            logger.info("Type détecté: Présidentielles")
            return 'presidentielles'
        elif any('législ' in col or 'legisl' in col or 'député' in col or 'depute' in col for col in columns_lower):
            logger.info("Type détecté: Législatives")
            return 'legislatives'
        elif any('europ' in col or 'parlement' in col for col in columns_lower):
            logger.info("Type détecté: Européennes")
            return 'europeennes'
        else:
            logger.warning("Type d'élection non détecté")
            return 'unknown'
    
    def standardize_electoral_columns(
        self, 
        df: pd.DataFrame, 
        election_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Standardise les noms de colonnes selon le type d'élection
        
        Args:
            df: DataFrame à standardiser
            election_type: Type d'élection (auto-détecté si None)
            
        Returns:
            DataFrame avec colonnes standardisées
        """
        if election_type is None:
            election_type = self.identify_election_type(df)
        
        df = df.copy()
        
        common_mappings = {
            'code_departement': ['code_dept', 'code_dpt', 'dept', 'departement'],
            'code_commune': ['code_com', 'commune_code', 'insee'],
            'libelle_commune': ['commune', 'nom_commune', 'ville'],
            'code_circonscription': ['code_circ', 'circonscription'],
            
            'inscrits': ['nb_inscrits', 'electeurs_inscrits', 'inscrit'],
            'votants': ['nb_votants', 'votant'],
            'abstentions': ['nb_abstentions', 'abstention'],
            'blancs': ['nb_blancs', 'votes_blancs', 'blanc'],
            'nuls': ['nb_nuls', 'votes_nuls', 'nul'],
            'exprimes': ['nb_exprimes', 'suffrages_exprimes', 'exprime'],
            
            'nom_candidat': ['candidat', 'nom', 'nom_liste', 'liste'],
            'prenom_candidat': ['prenom'],
            'parti': ['parti_politique', 'nuance', 'etiquette'],
            'voix': ['nb_voix', 'suffrages', 'nombre_voix'],
            
            'date_election': ['date', 'date_scrutin'],
            'tour': ['numero_tour', 'num_tour'],
            'annee': ['année', 'year']
        }
        
        for standard_name, variants in common_mappings.items():
            for col in df.columns:
                col_lower = col.lower().strip()
                if col_lower in variants or col_lower == standard_name:
                    df.rename(columns={col: standard_name}, inplace=True)
                    logger.debug(f"Colonne renommée: {col} -> {standard_name}")
                    break
        
        logger.info(f"Colonnes standardisées pour {election_type}")
        return df
    
    def calculate_electoral_percentages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule les pourcentages de participation et de votes
        
        Args:
            df: DataFrame avec données électorales
            
        Returns:
            DataFrame avec colonnes de pourcentages ajoutées
        """
        df = df.copy()
        
        if 'inscrits' in df.columns and 'votants' in df.columns:
            df['votants'] = pd.to_numeric(df['votants'], errors='coerce')
            df['inscrits'] = pd.to_numeric(df['inscrits'], errors='coerce')
            df['taux_participation'] = (df['votants'] / df['inscrits'] * 100).round(2)
            logger.info("Taux de participation calculé")
        
        if 'inscrits' in df.columns and 'abstentions' in df.columns:
            df['abstentions'] = pd.to_numeric(df['abstentions'], errors='coerce')
            df['taux_abstention'] = (df['abstentions'] / df['inscrits'] * 100).round(2)
            logger.info("Taux d'abstention calculé")
        
        if 'votants' in df.columns:
            if 'blancs' in df.columns:
                df['blancs'] = pd.to_numeric(df['blancs'], errors='coerce')
                df['taux_blancs'] = (df['blancs'] / df['votants'] * 100).round(2)
            if 'nuls' in df.columns:
                df['nuls'] = pd.to_numeric(df['nuls'], errors='coerce')
                df['taux_nuls'] = (df['nuls'] / df['votants'] * 100).round(2)
        
        if 'voix' in df.columns and 'exprimes' in df.columns:
            df['voix'] = pd.to_numeric(df['voix'], errors='coerce')
            df['exprimes'] = pd.to_numeric(df['exprimes'], errors='coerce')
            df['pourcentage_voix'] = (df['voix'] / df['exprimes'] * 100).round(2)
            logger.info("Pourcentage des voix calculé")
        
        return df
    
    def aggregate_electoral_results(
        self,
        df: pd.DataFrame,
        level: str = 'commune',
        group_by_tour: bool = True
    ) -> pd.DataFrame:
        """
        Agrège les résultats électoraux par niveau géographique
        
        Args:
            df: DataFrame avec résultats détaillés
            level: Niveau d'agrégation ('commune', 'circonscription', 'departement')
            group_by_tour: Si True, agrège aussi par tour
            
        Returns:
            DataFrame agrégé
        """
        group_cols = []
        
        if level == 'commune' and 'code_commune' in df.columns:
            group_cols.append('code_commune')
            if 'libelle_commune' in df.columns:
                group_cols.append('libelle_commune')
        
        if level == 'circonscription' and 'code_circonscription' in df.columns:
            group_cols.append('code_circonscription')
        
        if level == 'departement' and 'code_departement' in df.columns:
            group_cols.append('code_departement')
        
        if 'nom_candidat' in df.columns:
            group_cols.append('nom_candidat')
        
        if 'parti' in df.columns:
            group_cols.append('parti')
        
        if group_by_tour and 'tour' in df.columns:
            group_cols.append('tour')
        
        if not group_cols:
            logger.warning("Aucune colonne de groupement trouvée")
            return df
        
        agg_dict = {}
        numeric_cols = ['inscrits', 'votants', 'abstentions', 'blancs', 'nuls', 'exprimes', 'voix']
        
        for col in numeric_cols:
            if col in df.columns:
                agg_dict[col] = 'sum'
        
        if not agg_dict:
            logger.warning("Aucune colonne numérique à agréger")
            return df
        
        logger.info(f"Agrégation par {level}, colonnes: {group_cols}")
        df_agg = df.groupby(group_cols, as_index=False).agg(agg_dict)
        
        df_agg = self.calculate_electoral_percentages(df_agg)
        
        logger.info(f"Agrégation terminée: {len(df_agg)} lignes")
        return df_agg
    
    def add_electoral_rankings(
        self,
        df: pd.DataFrame,
        group_by: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Ajoute le classement des candidats par nombre de voix
        
        Args:
            df: DataFrame avec résultats
            group_by: Colonnes de groupement (commune, tour, etc.)
            
        Returns:
            DataFrame avec colonne 'rang' ajoutée
        """
        if 'voix' not in df.columns:
            logger.warning("Colonne 'voix' introuvable, impossible de calculer les rangs")
            return df
        
        df = df.copy()
        
        if group_by is None:
            group_by = []
            if 'code_commune' in df.columns:
                group_by.append('code_commune')
            if 'tour' in df.columns:
                group_by.append('tour')
        
        if group_by:
            df['rang'] = df.groupby(group_by)['voix'].rank(method='dense', ascending=False).astype('Int64')
            logger.info(f"Rangs calculés par {group_by}")
        else:
            df['rang'] = df['voix'].rank(method='dense', ascending=False).astype('Int64')
            logger.info("Rangs calculés globalement")
        
        return df
    
    def filter_qualified_candidates(
        self,
        df: pd.DataFrame,
        tour: int = 1,
        top_n: int = 2
    ) -> pd.DataFrame:
        """
        Filtre les candidats qualifiés pour le tour suivant
        
        Args:
            df: DataFrame avec résultats du tour
            tour: Numéro du tour
            top_n: Nombre de candidats qualifiés (2 pour présidentielles)
            
        Returns:
            DataFrame avec candidats qualifiés
        """
        if 'tour' not in df.columns or 'rang' not in df.columns:
            logger.warning("Colonnes 'tour' et/ou 'rang' introuvables")
            return df
        
        df_qualified = df[(df['tour'] == tour) & (df['rang'] <= top_n)].copy()
        logger.info(f"Candidats qualifiés du tour {tour}: {len(df_qualified)} lignes")
        
        return df_qualified
    
    def add_election_metadata(
        self,
        df: pd.DataFrame,
        election_type: str,
        annee: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Ajoute les métadonnées sur l'élection
        
        Args:
            df: DataFrame à enrichir
            election_type: Type d'élection
            annee: Année de l'élection
            
        Returns:
            DataFrame enrichi
        """
        df = df.copy()
        df['type_election'] = election_type
        
        if annee:
            df['annee'] = annee
        
        logger.info(f"Métadonnées ajoutées: {election_type}")
        return df
    
    def calculate_electoral_swing(
        self,
        df_current: pd.DataFrame,
        df_previous: pd.DataFrame,
        join_on: List[str] = ['code_commune', 'nom_candidat']
    ) -> pd.DataFrame:
        """
        Calcule l'évolution (swing) entre deux élections
        
        Args:
            df_current: Résultats de l'élection actuelle
            df_previous: Résultats de l'élection précédente
            join_on: Colonnes de jointure
            
        Returns:
            DataFrame avec colonnes d'évolution
        """
        for col in join_on:
            if col not in df_current.columns or col not in df_previous.columns:
                logger.error(f"Colonne de jointure manquante: {col}")
                return df_current
        
        if 'pourcentage_voix' not in df_current.columns or 'pourcentage_voix' not in df_previous.columns:
            logger.warning("Colonne 'pourcentage_voix' manquante, calcul impossible")
            return df_current
        
        df_merged = df_current.merge(
            df_previous[join_on + ['pourcentage_voix']],
            on=join_on,
            how='left',
            suffixes=('', '_previous')
        )
        
        df_merged['evolution_pourcentage'] = (
            df_merged['pourcentage_voix'] - df_merged['pourcentage_voix_previous']
        ).round(2)
        
        logger.info("Évolution calculée entre les deux élections")
        return df_merged
    
    def filter_by_geographic_zone(
        self, 
        df: pd.DataFrame,
        zone_column: str = 'code_zone',
        zone_code: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Filtre les données par zone géographique
        
        Args:
            df: DataFrame à filtrer
            zone_column: Nom de la colonne contenant le code de zone
            zone_code: Code de la zone à filtrer (si None, utilise la config)
            
        Returns:
            DataFrame filtré
        """
        if zone_code is None:
            zone_code = self.geographic_config.get('zone_code', '75')
        
        logger.info(f"Filtrage par zone géographique: {zone_code}")
        
        if zone_column not in df.columns:
            logger.error(f"Colonne {zone_column} introuvable")
            return df
        
        initial_count = len(df)
        df_filtered = df[df[zone_column].astype(str) == str(zone_code)].copy()
        filtered_count = len(df_filtered)
        
        logger.info(
            f"Filtrage terminé: {filtered_count}/{initial_count} lignes "
            f"({(filtered_count/initial_count)*100:.1f}%)"
        )
        
        return df_filtered
    
    def aggregate_by_period(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        period: str = 'Y',  # 'Y'=année, 'M'=mois, 'Q'=trimestre
        agg_func: str = 'sum'
    ) -> pd.DataFrame:
        """
        Agrège les données par période temporelle
        
        Args:
            df: DataFrame à agréger
            date_column: Colonne contenant les dates
            value_column: Colonne contenant les valeurs à agréger
            period: Période d'agrégation ('Y', 'M', 'Q', 'D')
            agg_func: Fonction d'agrégation ('sum', 'mean', 'count', etc.)
            
        Returns:
            DataFrame agrégé
        """
        logger.info(f"Agrégation par période: {period}, fonction: {agg_func}")
        
        if date_column not in df.columns:
            logger.error(f"Colonne de date {date_column} introuvable")
            return df
        
        try:
            df[date_column] = pd.to_datetime(df[date_column])
            df_agg = df.groupby(pd.Grouper(key=date_column, freq=period)).agg({
                value_column: agg_func
            }).reset_index()
            
            logger.info(f"Agrégation réussie: {len(df_agg)} périodes")
            return df_agg
            
        except Exception as e:
            logger.error(f"Erreur lors de l'agrégation: {e}")
            return df
    
    def calculate_rates(
        self,
        df: pd.DataFrame,
        numerator_col: str,
        denominator_col: str,
        output_col: str,
        multiply_by: float = 100.0
    ) -> pd.DataFrame:
        """
        Calcule des taux (pourcentages, ratios)
        
        Args:
            df: DataFrame
            numerator_col: Colonne numérateur
            denominator_col: Colonne dénominateur
            output_col: Nom de la colonne de sortie
            multiply_by: Facteur de multiplication (100 pour pourcentage)
            
        Returns:
            DataFrame avec nouvelle colonne de taux
        """
        logger.info(f"Calcul du taux: {output_col}")
        
        try:
            df[output_col] = (
                df[numerator_col] / df[denominator_col] * multiply_by
            ).round(2)
            
            # Gestion des valeurs infinies et NaN
            df[output_col] = df[output_col].replace([np.inf, -np.inf], np.nan)
            
            logger.info(f"Taux calculé: {output_col}")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du taux: {e}")
            return df
    
    def create_year_column(
        self,
        df: pd.DataFrame,
        date_column: str,
        year_column: str = 'year'
    ) -> pd.DataFrame:
        """
        Extrait l'année d'une colonne de date
        
        Args:
            df: DataFrame
            date_column: Colonne contenant les dates
            year_column: Nom de la nouvelle colonne année
            
        Returns:
            DataFrame avec colonne année
        """
        logger.info(f"Création de la colonne année depuis {date_column}")
        
        try:
            df[date_column] = pd.to_datetime(df[date_column])
            df[year_column] = df[date_column].dt.year
            
            logger.info(f"Colonne {year_column} créée")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la colonne année: {e}")
            return df
    
    def create_features_for_ml(
        self,
        df: pd.DataFrame,
        date_column: str = 'date'
    ) -> pd.DataFrame:
        """
        Crée des features temporelles pour le machine learning
        
        Args:
            df: DataFrame
            date_column: Colonne contenant les dates
            
        Returns:
            DataFrame avec features supplémentaires
        """
        logger.info("Création de features pour ML")
        
        try:
            df[date_column] = pd.to_datetime(df[date_column])
            
            # Features temporelles
            df['year'] = df[date_column].dt.year
            df['month'] = df[date_column].dt.month
            df['quarter'] = df[date_column].dt.quarter
            df['day_of_week'] = df[date_column].dt.dayofweek
            df['day_of_year'] = df[date_column].dt.dayofyear
            df['week_of_year'] = df[date_column].dt.isocalendar().week
            
            # Features cycliques (pour capturer la saisonnalité)
            df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
            
            logger.info("Features ML créées avec succès")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des features: {e}")
            return df
    
    def normalize_values(
        self,
        df: pd.DataFrame,
        columns: List[str],
        method: str = 'minmax'  # 'minmax' ou 'zscore'
    ) -> pd.DataFrame:
        """
        Normalise les valeurs numériques
        
        Args:
            df: DataFrame
            columns: Liste des colonnes à normaliser
            method: Méthode de normalisation ('minmax' ou 'zscore')
            
        Returns:
            DataFrame avec valeurs normalisées
        """
        logger.info(f"Normalisation des colonnes: {columns}, méthode: {method}")
        
        for col in columns:
            if col not in df.columns:
                logger.warning(f"Colonne {col} introuvable, ignorée")
                continue
            
            try:
                if method == 'minmax':
                    # Normalisation Min-Max (0-1)
                    min_val = df[col].min()
                    max_val = df[col].max()
                    df[f'{col}_normalized'] = (df[col] - min_val) / (max_val - min_val)
                    
                elif method == 'zscore':
                    # Normalisation Z-score (standardisation)
                    mean_val = df[col].mean()
                    std_val = df[col].std()
                    df[f'{col}_normalized'] = (df[col] - mean_val) / std_val
                
                logger.info(f"Colonne {col} normalisée")
                
            except Exception as e:
                logger.error(f"Erreur lors de la normalisation de {col}: {e}")
        
        return df
    
    def merge_datasets(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        on: Union[str, List[str]],
        how: str = 'inner',
        suffixes: tuple = ('_left', '_right')
    ) -> pd.DataFrame:
        """
        Fusionne deux datasets
        
        Args:
            df1: Premier DataFrame
            df2: Second DataFrame
            on: Colonne(s) de jointure
            how: Type de jointure ('inner', 'left', 'right', 'outer')
            suffixes: Suffixes pour les colonnes en doublon
            
        Returns:
            DataFrame fusionné
        """
        logger.info(f"Fusion de datasets sur: {on}, type: {how}")
        
        try:
            df_merged = pd.merge(
                df1, df2,
                on=on,
                how=how,
                suffixes=suffixes
            )
            
            logger.info(
                f"Fusion réussie: {len(df1)} + {len(df2)} -> {len(df_merged)} lignes"
            )
            return df_merged
            
        except Exception as e:
            logger.error(f"Erreur lors de la fusion: {e}")
            raise
    
    def calculate_statistics(
        self,
        df: pd.DataFrame,
        columns: List[str],
        group_by: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calcule les statistiques descriptives (moyennes, totaux, etc.)
        
        Args:
            df: DataFrame
            columns: Colonnes pour lesquelles calculer les statistiques
            group_by: Colonnes de regroupement (optionnel)
            
        Returns:
            DataFrame avec statistiques
        """
        logger.info(f"Calcul des statistiques pour: {columns}")
        
        try:
            if group_by:
                stats = df.groupby(group_by)[columns].agg([
                    'count', 'sum', 'mean', 'median', 'std', 'min', 'max'
                ]).reset_index()
                logger.info(f"Statistiques calculées par groupes: {group_by}")
            else:
                stats = df[columns].agg([
                    'count', 'sum', 'mean', 'median', 'std', 'min', 'max'
                ]).T
                logger.info("Statistiques globales calculées")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}")
            return df
    
    def calculate_variation_rate(
        self,
        df: pd.DataFrame,
        value_column: str,
        group_column: Optional[str] = None,
        output_column: str = 'variation_rate'
    ) -> pd.DataFrame:
        """
        Calcule le taux de variation entre périodes
        
        Args:
            df: DataFrame (doit être trié par date)
            value_column: Colonne des valeurs
            group_column: Colonne de regroupement (optionnel)
            output_column: Nom de la colonne de sortie
            
        Returns:
            DataFrame avec taux de variation
        """
        logger.info(f"Calcul du taux de variation pour: {value_column}")
        
        try:
            if group_column:
                df[output_column] = df.groupby(group_column)[value_column].pct_change() * 100
            else:
                df[output_column] = df[value_column].pct_change() * 100
            
            df[output_column] = df[output_column].round(2)
            logger.info(f"Taux de variation calculé: {output_column}")
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la variation: {e}")
            return df
    
    def harmonize_column_names(
        self,
        df: pd.DataFrame,
        column_mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Harmonise les noms de colonnes entre différentes sources
        
        Args:
            df: DataFrame
            column_mapping: Dictionnaire {ancien_nom: nouveau_nom}
            
        Returns:
            DataFrame avec colonnes renommées
        """
        logger.info(f"Harmonisation de {len(column_mapping)} colonnes")
        
        # Renommer uniquement les colonnes qui existent
        existing_columns = {
            old: new for old, new in column_mapping.items() 
            if old in df.columns
        }
        
        if existing_columns:
            df = df.rename(columns=existing_columns)
            logger.info(f"Colonnes harmonisées: {list(existing_columns.values())}")
        else:
            logger.warning("Aucune colonne à harmoniser trouvée")
        
        return df
    
    def create_derived_variables(
        self,
        df: pd.DataFrame,
        derivations: Dict[str, callable]
    ) -> pd.DataFrame:
        """
        Crée des variables dérivées à partir de colonnes existantes
        
        Args:
            df: DataFrame
            derivations: Dictionnaire {nouvelle_colonne: fonction_de_calcul}
            
        Returns:
            DataFrame avec variables dérivées
            
        Example:
            derivations = {
                'abstention_rate': lambda df: 100 - df['participation_rate'],
                'valid_votes_ratio': lambda df: df['valid_votes'] / df['total_votes']
            }
        """
        logger.info(f"Création de {len(derivations)} variables dérivées")
        
        for var_name, func in derivations.items():
            try:
                df[var_name] = func(df)
                logger.info(f"Variable dérivée créée: {var_name}")
            except Exception as e:
                logger.error(f"Erreur lors de la création de {var_name}: {e}")
        
        return df
    
    def transform_pipeline(
        self,
        df: pd.DataFrame,
        config: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Pipeline complet de transformation
        
        Args:
            df: DataFrame à transformer
            config: Configuration de transformation avec les clés:
                   - geographic_filter: Dict avec zone_column et zone_code
                   - column_mapping: Dict de renommage de colonnes
                   - date_columns: List des colonnes de dates
                   - calculate_rates: List de dicts pour calculs de taux
                   - derived_variables: Dict de variables dérivées
                   - save_output: bool pour sauvegarder le résultat
                   
        Returns:
            DataFrame transformé
        """
        logger.info("=" * 50)
        logger.info("Démarrage du pipeline de transformation")
        logger.info("=" * 50)
        
        if config is None:
            config = {}
        
        initial_rows = len(df)
        logger.info(f"État initial: {initial_rows} lignes, {len(df.columns)} colonnes")

        if config.get('geographic_filter'):
            geo_config = config['geographic_filter']
            df = self.filter_by_geographic_zone(
                df,
                zone_column=geo_config.get('zone_column', 'code_zone'),
                zone_code=geo_config.get('zone_code')
            )
        
        if config.get('column_mapping'):
            df = self.harmonize_column_names(df, config['column_mapping'])
        
        if config.get('date_columns'):
            for date_col in config['date_columns']:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    logger.info(f"Date standardisée: {date_col}")
        
        # Étape 4: Calcul des taux
        if config.get('calculate_rates'):
            for rate_config in config['calculate_rates']:
                df = self.calculate_rates(
                    df,
                    numerator_col=rate_config['numerator'],
                    denominator_col=rate_config['denominator'],
                    output_col=rate_config['output'],
                    multiply_by=rate_config.get('multiply_by', 100.0)
                )
        
        if config.get('derived_variables'):
            df = self.create_derived_variables(df, config['derived_variables'])
        
        if config.get('calculate_statistics'):
            stats_config = config['calculate_statistics']
            stats = self.calculate_statistics(
                df,
                columns=stats_config.get('columns', []),
                group_by=stats_config.get('group_by')
            )
            logger.info(f"Statistiques:\n{stats}")
        
        if config.get('save_output'):
            output_path = config.get('output_path', '../data/processed/transformed_data.csv')
            df.to_csv(output_path, index=False)
            logger.info(f"Données transformées sauvegardées: {output_path}")
        
        # Rapport final
        final_rows = len(df)
        logger.info("=" * 50)
        logger.info(f"État final: {final_rows} lignes, {len(df.columns)} colonnes")
        logger.info(f"Lignes conservées: {(final_rows/initial_rows)*100:.1f}%")
        logger.info("Pipeline de transformation terminé avec succès")
        logger.info("=" * 50)
        
        return df


# Exemple d'utilisation
if __name__ == "__main__":
    transformer = DataTransformer()
    
    # Données de test
    test_data = {
        'Code Commune': ['69381', '69381', '69382', '69383'],
        'Date Election': ['2020-01-15', '2021-01-15', '2020-01-15', '2021-01-15'],
        'Nb Inscrits': [1000, 1050, 500, 520],
        'Nb Votants': [650, 700, 350, 380],
        'Votes Exprimés': [600, 680, 340, 370]
    }
    
    df_test = pd.DataFrame(test_data)
    
    print("=" * 60)
    print("AVANT TRANSFORMATION")
    print("=" * 60)
    print(df_test)
    
    # Configuration de transformation
    transform_config = {
        'geographic_filter': {
            'zone_column': 'Code Commune',
            'zone_code': '69381'
        },
        'column_mapping': {
            'Code Commune': 'code_commune',
            'Date Election': 'date_election',
            'Nb Inscrits': 'nb_inscrits',
            'Nb Votants': 'nb_votants',
            'Votes Exprimés': 'votes_exprimes'
        },
        'date_columns': ['date_election'],
        'calculate_rates': [
            {
                'numerator': 'nb_votants',
                'denominator': 'nb_inscrits',
                'output': 'taux_participation',
                'multiply_by': 100.0
            }
        ],
        'derived_variables': {
            'taux_abstention': lambda df: 100 - df['taux_participation'],
            'ratio_exprimes': lambda df: df['votes_exprimes'] / df['nb_votants'] * 100
        },
        'save_output': False
    }
    
    # Transformation
    df_transformed = transformer.transform_pipeline(df_test, config=transform_config)
    
    print("\n" + "=" * 60)
    print("APRÈS TRANSFORMATION")
    print("=" * 60)
    print(df_transformed)
