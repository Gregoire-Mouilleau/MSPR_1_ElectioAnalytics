"""
Script ETL complet pour les données électorales de Lyon 7ème
Regroupe extraction, filtrage et traitement des européennes, législatives et présidentielles
"""

import pandas as pd
from pathlib import Path
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# EXTRACTION EUROPÉENNES - DÉPARTEMENT 69 (RHÔNE)
# ============================================================================

def extract_europeennes():
    """Extrait les européennes pour le département 69 (Rhône)"""
    
    raw_dir = Path("data/raw/europeennes")
    output_dir = Path("data/filtered/lyon_7e/europeennes")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("\n" + "="*60)
    logger.info("EXTRACTION EUROPÉENNES - DÉPARTEMENT 69 (RHÔNE)")
    logger.info("="*60)
    
    excel_files = list(raw_dir.glob("*.xls")) + list(raw_dir.glob("*.xlsx"))
    
    if not excel_files:
        logger.warning(f"Aucun fichier trouvé dans {raw_dir}")
        return 0
    
    success_count = 0
    logger.info(f"Fichiers trouvés: {len(excel_files)}")
    
    for excel_file in excel_files:
        logger.info(f"\n  Traitement: {excel_file.name}")
        
        try:
            df = pd.read_excel(excel_file, engine='xlrd' if excel_file.suffix == '.xls' else 'openpyxl')
            
            code_dept_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if 'code' in col_lower and ('département' in col_lower or 'departement' in col_lower):
                    code_dept_col = col
                    break
            
            if code_dept_col is None:
                code_dept_col = df.columns[0]
            
            df_filtered = df[df[code_dept_col].astype(str).str.strip() == '69'].copy()
            
            logger.info(f"    Lignes département 69: {len(df_filtered)}")
            
            if len(df_filtered) > 0:
                output_file = output_dir / f"{excel_file.stem}_lyon.csv"
                df_filtered.to_csv(output_file, sep=';', index=False, encoding='utf-8', na_rep='NA')
                logger.info(f"    ✓ Sauvegardé: {output_file.name}")
                success_count += 1
                
        except Exception as e:
            logger.error(f"    ✗ Erreur: {e}")
    
    logger.info(f"\n  Résumé: {success_count}/{len(excel_files)} fichiers traités")
    return success_count


# ============================================================================
# EXTRACTION LÉGISLATIVES - LYON 7ÈME (CIRCONSCRIPTIONS 1 ET 3)
# ============================================================================

def extract_legislatives():
    """Extrait les législatives pour Lyon 7ème (circonscriptions 1 et 3)"""
    
    raw_dir = Path("data/raw/legislatives")
    output_dir = Path("data/filtered/lyon_7e/legislatives")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("\n" + "="*60)
    logger.info("EXTRACTION LÉGISLATIVES - LYON 7ÈME (CIRC. 1 & 3)")
    logger.info("="*60)
    
    txt_files = list(raw_dir.glob("*.txt"))
    excel_files = list(raw_dir.glob("*.xls")) + list(raw_dir.glob("*.xlsx"))
    all_files = txt_files + excel_files
    
    if not all_files:
        logger.warning(f"Aucun fichier trouvé dans {raw_dir}")
        return 0
    
    success_count = 0
    logger.info(f"Fichiers trouvés: {len(all_files)}")
    
    for file_path in all_files:
        logger.info(f"\n  Traitement: {file_path.name}")
        
        try:
            if file_path.suffix == '.txt':
                with open(file_path, 'r', encoding='ISO-8859-1') as f:
                    header = f.readline().strip()
                    lines_lyon7 = []
                    
                    for line in f:
                        if line.startswith('69;'):
                            parts = line.split(';')
                            if len(parts) > 5:
                                code_circ = parts[2].strip() if len(parts) > 2 else ''
                                code_commune = parts[4].strip() if len(parts) > 4 else ''
                                libelle_commune = parts[5].strip() if len(parts) > 5 else ''
                                
                                if code_commune == '123' and code_circ in ['01', '03'] and 'Lyon' in libelle_commune:
                                    lines_lyon7.append(line.strip())
                
                logger.info(f"    Lignes Lyon 7ème: {len(lines_lyon7)}")
                
                if len(lines_lyon7) > 0:
                    output_file = output_dir / f"{file_path.stem}_lyon7eme.csv"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(header + '\n')
                        f.write('\n'.join(lines_lyon7))
                    logger.info(f"    ✓ Sauvegardé: {output_file.name}")
                    success_count += 1
            
            else:
                df = pd.read_excel(file_path, engine='xlrd' if file_path.suffix == '.xls' else 'openpyxl')
                
                if '2024' in file_path.name:
                    code_region_col = df.columns[0]
                    df_filtered = df[df[code_region_col].astype(str).str.strip() == '84'].copy()
                    
                    logger.info(f"    Lignes région Auvergne-Rhône-Alpes (contient Lyon): {len(df_filtered)}")
                    
                    if len(df_filtered) > 0:
                        output_file = output_dir / f"{file_path.stem}_regional.csv"
                        df_filtered.to_csv(output_file, sep=';', index=False, encoding='utf-8', na_rep='NA')
                        logger.info(f"    ✓ Sauvegardé: {output_file.name} (données régionales)")
                        success_count += 1
                    continue
                
                code_dept_col = None
                code_circ_col = None
                code_commune_col = None
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'code' in col_lower and 'département' in col_lower:
                        code_dept_col = col
                    elif 'code' in col_lower and 'circonscription' in col_lower:
                        code_circ_col = col
                    elif 'code' in col_lower and 'commune' in col_lower:
                        code_commune_col = col
                
                if code_dept_col is None or code_circ_col is None or code_commune_col is None:
                    code_dept_col = df.columns[0]
                    code_circ_col = df.columns[2]
                    code_commune_col = df.columns[4]
                
                if all([code_dept_col, code_circ_col, code_commune_col]):
                    df_filtered = df[
                        (df[code_dept_col].astype(str).str.strip() == '69') &
                        (df[code_commune_col].astype(str).str.strip() == '123') &
                        (df[code_circ_col].astype(str).str.strip().isin(['1', '01', '3', '03']))
                    ].copy()
                    
                    logger.info(f"    Lignes Lyon 7ème: {len(df_filtered)}")
                    
                    if len(df_filtered) > 0:
                        output_file = output_dir / f"{file_path.stem}_lyon7eme.csv"
                        df_filtered.to_csv(output_file, sep=';', index=False, encoding='utf-8', na_rep='NA')
                        logger.info(f"    ✓ Sauvegardé: {output_file.name}")
                        success_count += 1
                
        except Exception as e:
            logger.error(f"    ✗ Erreur: {e}")
    
    logger.info(f"\n  Résumé: {success_count}/{len(all_files)} fichiers traités")
    return success_count


# ============================================================================
# EXTRACTION PRÉSIDENTIELLES - LYON 7ÈME (BUREAUX 07XX)
# ============================================================================

def extract_presidentielles():
    """Extrait les présidentielles pour Lyon 7ème (bureaux de vote 07xx)"""
    
    raw_dir = Path("data/raw/présidentielles")
    output_dir = Path("data/filtered/lyon_7e/presidentielles")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("\n" + "="*60)
    logger.info("EXTRACTION PRÉSIDENTIELLES - LYON 7ÈME (BUREAUX 07XX)")
    logger.info("="*60)
    
    txt_files = list(raw_dir.glob("*.txt"))
    
    if not txt_files:
        logger.warning(f"Aucun fichier trouvé dans {raw_dir}")
        return 0
    
    success_count = 0
    total_lines = 0
    logger.info(f"Fichiers trouvés: {len(txt_files)}")
    
    for txt_file in txt_files:
        logger.info(f"\n  Traitement: {txt_file.name}")
        
        try:
            with open(txt_file, 'r', encoding='ISO-8859-1') as f:
                header = f.readline().strip()
                lines_lyon7 = []
                
                if '2022' in txt_file.name and '2eme' in txt_file.name.lower():
                    for line in f:
                        if line.startswith('69;') and ';123;Lyon;' in line:
                            lines_lyon7.append(line.strip())
                    
                    logger.info(f"    Lignes Lyon complet (toute la ville): {len(lines_lyon7)}")
                    
                    if len(lines_lyon7) > 0:
                        output_file = output_dir / f"{txt_file.stem}_lyon_complet.csv"
                        with open(output_file, 'w', encoding='utf-8') as out_f:
                            out_f.write(header + '\n')
                            out_f.write('\n'.join(lines_lyon7))
                        logger.info(f"    ✓ Sauvegardé: {output_file.name} (données ville complète)")
                        total_lines += len(lines_lyon7)
                        success_count += 1
                    continue
                
                for line in f:
                    if (line.startswith('69;') or line.startswith('1;69;') or line.startswith('2;69;')) and ';123;Lyon;07' in line:
                        lines_lyon7.append(line.strip())
            
            logger.info(f"    Lignes Lyon 7ème: {len(lines_lyon7)}")
            
            if len(lines_lyon7) > 0:
                output_file = output_dir / f"{txt_file.stem}_lyon7eme.csv"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(header + '\n')
                    f.write('\n'.join(lines_lyon7))
                logger.info(f"    ✓ Sauvegardé: {output_file.name}")
                total_lines += len(lines_lyon7)
                success_count += 1
                
        except Exception as e:
            logger.error(f"    ✗ Erreur: {e}")
    
    logger.info(f"\n  Résumé: {success_count}/{len(txt_files)} fichiers traités")
    logger.info(f"  Total: {total_lines} lignes extraites")
    return success_count


# ============================================================================
# TRAITEMENT ETL DES FICHIERS FILTRÉS
# ============================================================================

def process_filtered_files():
    """Traite tous les fichiers filtrés avec le pipeline ETL"""
    
    logger.info("\n" + "="*60)
    logger.info("TRAITEMENT ETL DES FICHIERS FILTRÉS")
    logger.info("="*60)
    
    pipeline = ElectoralPipeline()
    filtered_base = Path("data/filtered/lyon_7e")
    
    processed_count = 0
    
    for election_type in ['europeennes', 'legislatives', 'presidentielles']:
        election_dir = filtered_base / election_type
        
        if not election_dir.exists():
            continue
        
        csv_files = list(election_dir.glob("*.csv"))
        
        if not csv_files:
            continue
        
        logger.info(f"\n{election_type.upper()}: {len(csv_files)} fichiers")
        
        for csv_file in csv_files:
            try:
                filename = csv_file.stem
                annee = None
                for year in range(2000, 2030):
                    if str(year) in filename:
                        annee = year
                        break
                
                df = pipeline.process_single_file(
                    file_path=csv_file,
                    election_type=election_type,
                    annee=annee,
                    save_to_db=True,
                    save_to_csv=True
                )
                
                if df is not None and len(df) > 0:
                    processed_count += 1
                    
            except Exception as e:
                logger.error(f"  ✗ Erreur {csv_file.name}: {e}")
    
    logger.info(f"\n  Total: {processed_count} fichiers traités avec succès")
    return processed_count


# ============================================================================
# EXTRACTION DONNÉES SOCIO-ÉCONOMIQUES - DOSSIER AUTRES
# ============================================================================

def extract_autres():
    """Extrait et nettoie les données socio-économiques (chômage, revenus, délinquance, etc.)"""
    
    from src.etl.pipeline import ETLPipeline
    
    raw_dir = Path("data/raw/autres")
    output_dir = Path("data/filtered/autres")
    
    logger.info("\n" + "="*60)
    logger.info("EXTRACTION DONNÉES SOCIO-ÉCONOMIQUES - AUTRES")
    logger.info("="*60)
    
    pipeline = ETLPipeline()
    results = pipeline.process_socioeconomic_files(raw_dir, output_dir)
    
    success_count = results['success_count']
    total_rows = results['total_rows']
    total_files = results['total_files']
    
    logger.info(f"\n  Résumé: {success_count}/{total_files} fichiers traités, {total_rows:,} lignes totales")
    return success_count


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """Exécute l'extraction et le filtrage des données électorales (raw → filtered)"""
    
    print("\n" + "#"*60)
    print("EXTRACTION & FILTRAGE - DONNÉES ÉLECTORALES LYON 7ÈME")
    print("#"*60)
    
    try:
        results = {}
        
        results['europeennes'] = extract_europeennes()
        
        results['legislatives'] = extract_legislatives()
        
        results['presidentielles'] = extract_presidentielles()
        
        results['autres'] = extract_autres()
        
        logger.info("\n" + "#"*60)
        logger.info("RÉSUMÉ FINAL")
        logger.info("#"*60)
        
        logger.info("\nExtraction (raw → filtered):")
        for election_type in ['europeennes', 'legislatives', 'presidentielles']:
            count = results.get(election_type, 0)
            status = "✓" if count > 0 else "✗"
            logger.info(f"  {status} {election_type.capitalize()}: {count} fichiers extraits")
        
        autres_count = results.get('autres', 0)
        if autres_count > 0:
            logger.info(f"  ✓ Données socio-économiques: {autres_count} fichiers extraits")
        
        logger.info("\n" + "#"*60)
        logger.info("✅ EXTRACTION TERMINÉE AVEC SUCCÈS")
        logger.info("#"*60 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
