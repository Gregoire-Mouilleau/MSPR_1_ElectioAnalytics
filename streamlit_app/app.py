"""
Application Streamlit pour ElectioAnalytics
Dashboard de visualisation des données électorales
"""

# Fichier de test pour Streamlit, pour prévisualiser le dashboard, 
# a refaire complètement une fois l'ETL

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(
    page_title="ElectioAnalytics - Dashboard",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal
st.title("🗳️ ElectioAnalytics - Dashboard")
st.markdown("### Analyse prédictive électorale - Lyon 7e arrondissement")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Zone géographique
    st.subheader("Zone géographique")
    zone = st.selectbox(
        "Sélectionner la zone",
        ["Lyon 7e arrondissement", "Rhône (69)", "Auvergne-Rhône-Alpes"]
    )
    
    # Période d'analyse
    st.subheader("Période d'analyse")
    date_debut = st.date_input("Date de début", datetime(2020, 1, 1))
    date_fin = st.date_input("Date de fin", datetime.now())
    
    # Filtres
    st.subheader("Filtres")
    show_predictions = st.checkbox("Afficher les prédictions", value=True)
    show_historical = st.checkbox("Afficher l'historique", value=True)
    
    st.markdown("---")
    st.markdown("**Version:** 1.0.0")
    st.markdown("**Dernière mise à jour:** {}".format(datetime.now().strftime("%d/%m/%Y")))

# Onglets principaux
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Vue d'ensemble", 
    "🗺️ Données géographiques",
    "📈 Analyses",
    "🤖 Prédictions ML"
])

with tab1:
    st.header("Vue d'ensemble des données")
    
    # Métriques clés (exemple avec données fictives)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total enregistrements",
            value="12,458",
            delta="↑ 234 cette semaine"
        )
    
    with col2:
        st.metric(
            label="🗳️ Taux de participation moyen",
            value="67.5%",
            delta="↑ 2.3%"
        )
    
    with col3:
        st.metric(
            label="📍 Bureaux de vote",
            value="24",
            delta="0"
        )
    
    with col4:
        st.metric(
            label="✅ Qualité des données",
            value="94.2%",
            delta="↑ 1.5%"
        )
    
    st.markdown("---")
    
    # Graphiques de démonstration
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Évolution de la participation")
        # Données fictives
        df_participation = pd.DataFrame({
            'Année': [2017, 2018, 2019, 2020, 2021, 2022, 2023],
            'Participation': [65.2, 66.1, 67.3, 64.8, 68.2, 69.1, 67.5]
        })
        fig = px.line(df_participation, x='Année', y='Participation', 
                     markers=True, title="Taux de participation (%)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏘️ Répartition par catégorie")
        # Données fictives
        df_categories = pd.DataFrame({
            'Catégorie': ['Zone A', 'Zone B', 'Zone C', 'Zone D'],
            'Valeur': [23, 45, 18, 14]
        })
        fig = px.pie(df_categories, values='Valeur', names='Catégorie',
                    title="Répartition des zones")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("🗺️ Données géographiques")
    st.info("📍 Zone sélectionnée : Lyon 7e arrondissement, Rhône (69)")
    
    st.markdown("""
    ### Caractéristiques de la zone
    - **Code postal**: 69007
    - **Population**: ~52,000 habitants
    - **Superficie**: 9.47 km²
    - **Bureaux de vote**: 24
    """)
    
    # Placeholder pour une carte
    st.subheader("Carte interactive")
    st.info("🗺️ La carte interactive sera disponible après l'intégration des données géographiques")

with tab3:
    st.header("📈 Analyses statistiques")
    
    # Analyse multi-critères
    st.subheader("Indicateurs multiples")
    
    # Sélection des indicateurs
    indicateurs = st.multiselect(
        "Sélectionner les indicateurs à analyser",
        ["Participation", "Sécurité", "Emploi", "Démographie", "Économie"],
        default=["Participation", "Emploi"]
    )
    
    if indicateurs:
        st.success(f"✅ {len(indicateurs)} indicateur(s) sélectionné(s)")
        
        # Graphique de démonstration
        df_indicateurs = pd.DataFrame({
            'Mois': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin'],
            'Participation': [65, 66, 67, 66, 68, 69],
            'Emploi': [92, 93, 93, 94, 95, 94]
        })
        
        fig = go.Figure()
        for ind in indicateurs:
            if ind in df_indicateurs.columns:
                fig.add_trace(go.Scatter(
                    x=df_indicateurs['Mois'],
                    y=df_indicateurs[ind],
                    mode='lines+markers',
                    name=ind
                ))
        
        fig.update_layout(title="Évolution des indicateurs", 
                         xaxis_title="Mois",
                         yaxis_title="Valeur")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Veuillez sélectionner au moins un indicateur")

with tab4:
    st.header("🤖 Prédictions Machine Learning")
    
    st.info("🔮 Module de prédictions basé sur Scikit-learn")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Configuration du modèle")
        
        model_type = st.selectbox(
            "Type de modèle",
            ["Random Forest", "Régression linéaire", "SVM", "Gradient Boosting"]
        )
        
        test_size = st.slider("Taille de l'ensemble de test (%)", 10, 40, 20)
        
        if st.button("🚀 Entraîner le modèle", type="primary"):
            with st.spinner("Entraînement en cours..."):
                import time
                time.sleep(2)
                st.success("✅ Modèle entraîné avec succès!")
                st.metric("Précision", "87.3%", delta="↑ 3.2%")
    
    with col2:
        st.subheader("Résultats")
        
        st.markdown("""
        **Métriques de performance:**
        - Précision: 87.3%
        - Rappel: 84.1%
        - F1-Score: 85.6%
        - RMSE: 2.34
        """)
        
        # Graphique de prédiction
        df_pred = pd.DataFrame({
            'Valeur réelle': [65, 67, 66, 68, 70, 69],
            'Valeur prédite': [64, 68, 65, 69, 71, 68]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(len(df_pred))), 
                                y=df_pred['Valeur réelle'],
                                mode='lines+markers', name='Réel'))
        fig.add_trace(go.Scatter(x=list(range(len(df_pred))), 
                                y=df_pred['Valeur prédite'],
                                mode='lines+markers', name='Prédit'))
        fig.update_layout(title="Comparaison Réel vs Prédit")
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>ElectioAnalytics ETL Pipeline | EPSI Y4 MSPR 1 | 2026</p>
    <p>Technologies: Python • Pandas • PostgreSQL • Streamlit • Scikit-learn</p>
</div>
""", unsafe_allow_html=True)
