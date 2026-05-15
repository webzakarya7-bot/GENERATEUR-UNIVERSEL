# app.py - À sauvegarder
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import os
import re
import base64
from io import BytesIO

# Configuration
st.set_page_config(page_title="Générateur de Graphiques", layout="wide")

# CSS personnalisé (style académique)
st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    .stButton>button {background-color: #3498db; color: white; font-weight: bold;}
    h1 {color: #2c3e50; text-align: center;}
    h2 {color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

COULEURS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', 
            '#e67e22', '#1abc9c', '#34495e', '#95a5a6', '#d35400']

# Fonctions de traitement (identiques à votre programme)
def detecter_type_colonne(series):
    valeurs_non_nulles = series.dropna()
    if len(valeurs_non_nulles) == 0:
        return 'vide'
    count_numerique = 0
    for val in valeurs_non_nulles.head(100):
        try:
            float(str(val).replace('j', '').replace('min', '').replace('dh', '').replace(' ', ''))
            count_numerique += 1
        except:
            pass
    ratio = count_numerique / min(len(valeurs_non_nulles), 100)
    return 'numerique' if ratio > 0.8 else 'texte'

def extraire_numerique(valeur):
    if pd.isna(valeur):
        return None
    texte = str(valeur).lower()
    for unite in ['j', 'min', 'dh', 'h', 'seance', 'séance', '%', '°', 'kg', 'cm', 'm', 'ml', 'mg', 'ans', 'mois']:
        texte = texte.replace(unite, '')
    texte = texte.replace(',', '.').strip()
    nombres = re.findall(r'\d+\.?\d*', texte)
    return float(nombres[0]) if nombres else None

def nettoyer_texte(valeur):
    if pd.isna(valeur):
        return "Non précisé"
    texte = str(valeur).strip()
    return "Non précisé" if texte.lower() in ['', 'nan', 'none', 'null', 'na', 'n/a', '-'] else texte

def categoriser_numeriques(valeurs, n_bins=5):
    valeurs = [v for v in valeurs if v is not None]
    if not valeurs:
        return {}, []
    min_val, max_val = min(valeurs), max(valeurs)
    valeurs_uniques = sorted(set(valeurs))
    if len(valeurs_uniques) <= 8:
        counts = {str(int(v)) if v == int(v) else str(v): valeurs.count(v) for v in valeurs_uniques}
        return counts, list(counts.keys())
    intervalle = (max_val - min_val) / n_bins
    bins, labels = [], []
    for i in range(n_bins):
        debut, fin = min_val + i * intervalle, min_val + (i + 1) * intervalle
        if i == n_bins - 1:
            fin = max_val + 0.001
        bins.append((debut, fin))
        labels.append(f"{int(debut)}-{int(fin)}" if intervalle >= 1 else f"{debut:.1f}-{fin:.1f}")
    counts = {label: 0 for label in labels}
    for v in valeurs:
        for i, (debut, fin) in enumerate(bins):
            if debut <= v < fin:
                counts[labels[i]] += 1
                break
    return {k: v for k, v in counts.items() if v > 0}, list(counts.keys())

def generer_graphique_barres(categories, effectifs, titre_colonne, n_total, horizontal=False):
    if len(categories) > 12:
        combined = sorted(zip(categories, effectifs), key=lambda x: x[1], reverse=True)
        top, others_sum = combined[:11], sum(x[1] for x in combined[11:])
        categories = [x[0] for x in top] + ["Autres"]
        effectifs = [x[1] for x in top] + [others_sum]
        horizontal = True
    
    percents = [(c / n_total) * 100 for c in effectifs]
    fig, ax = plt.subplots(figsize=(12 if horizontal else 10, 7 if horizontal else 6))
    
    titre_principal = titre_colonne.upper().replace('_', ' ')
    fig.suptitle(f'{titre_principal} - Résultats en POURCENTAGE (n={n_total})', 
                 fontsize=13, fontweight='bold', y=0.98)
    
    colors = COULEURS[:len(categories)]
    
    if horizontal:
        bars = ax.barh(range(len(categories)), percents, color=colors, edgecolor='white', height=0.6)
        for i, (bar, pct, cnt) in enumerate(zip(bars, percents, effectifs)):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                    f'{pct:.1f}%\n(n={cnt})', ha='left', va='center', fontsize=9, fontweight='bold')
        ax.set_yticks(range(len(categories)))
        ax.set_yticklabels(categories)
        ax.set_xlabel('Pourcentage (%)', fontsize=11)
        ax.invert_yaxis()
    else:
        bars = ax.bar(range(len(categories)), percents, color=colors, edgecolor='white', width=0.6)
        for i, (bar, pct, cnt) in enumerate(zip(bars, percents, effectifs)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{pct:.1f}%\n(n={cnt})', ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=30, ha='right', fontsize=9)
        ax.set_ylabel('Pourcentage (%)', fontsize=11)
    
    ax.set_title(f'Répartition par {titre_colonne.replace("_", " ").title()}', 
                 fontsize=12, fontweight='bold', pad=15)
    ax.set_xlim(0, max(percents) + 10) if horizontal else ax.set_ylim(0, max(percents) + 8)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig

def generer_graphique_circulaire(categories, effectifs, titre_colonne, n_total):
    if len(categories) > 8:
        combined = sorted(zip(categories, effectifs), key=lambda x: x[1], reverse=True)
        top, others_sum = combined[:7], sum(x[1] for x in combined[7:])
        categories = [x[0] for x in top] + ["Autres"]
        effectifs = [x[1] for x in top] + [others_sum]
    
    percents = [(c / n_total) * 100 for c in effectifs]
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#e67e22', '#1abc9c', '#34495e'][:len(categories)]
    
    fig, ax = plt.subplots(figsize=(9, 7))
    explode = [0.05 if i == 0 else 0 for i in range(len(categories))]
    
    wedges, texts, autotexts = ax.pie(percents, explode=explode, labels=categories, colors=colors,
                                       autopct='%1.1f%%', startangle=90, shadow=True, textprops={'fontsize': 10})
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)
    
    ax.set_title(f'Répartition par {titre_colonne.replace("_", " ").title()}', 
                 fontsize=12, fontweight='bold', pad=20)
    
    legend_labels = [f'{cat} (n={eff})' for cat, eff in zip(categories, effectifs)]
    ax.legend(wedges, legend_labels, title="Catégories", loc="center left", 
              bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
    
    plt.tight_layout(rect=[0, 0, 0.85, 0.95])
    return fig

def generer_tableau_croise(df, col1, col2, n_total):
    tableau = pd.crosstab(df[col1], df[col2], margins=True)
    tableau_pct = pd.crosstab(df[col1], df[col2], normalize='index') * 100
    
    tableau_graph = tableau.drop('All', errors='ignore').drop('All', axis=1, errors='ignore')
    
    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(tableau_graph.index))
    width = 0.8 / len(tableau_graph.columns)
    
    for i, col in enumerate(tableau_graph.columns):
        offset = (i - len(tableau_graph.columns)/2 + 0.5) * width
        bars = ax.bar(x + offset, tableau_graph[col], width, 
                      label=col, color=COULEURS[i % len(COULEURS)], 
                      edgecolor='white', alpha=0.9)
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                        f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    ax.set_xlabel(col1.replace('_', ' ').title(), fontsize=11)
    ax.set_ylabel('Effectifs (n)', fontsize=11)
    ax.set_title(f'Tableau croisé : {col1.replace("_", " ").title()} × {col2.replace("_", " ").title()}', 
                 fontsize=12, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(tableau_graph.index, rotation=30, ha='right')
    ax.legend(title=col2.replace('_', ' ').title(), loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    return fig, tableau, tableau_pct

def get_image_download_link(fig, filename, text):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    return f'<a href="data:file/png;base64,{b64}" download="{filename}">📥 {text}</a>'

# ==================== INTERFACE ====================

st.title("📊 Générateur Universel de Graphiques")
st.markdown("*Compatible avec n'importe quel fichier Excel*")

# Upload fichier
uploaded_file = st.file_uploader("📁 Glissez-déposez votre fichier Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    n_total = len(df)
    
    st.success(f"✅ {n_total} lignes | {len(df.columns)} colonnes chargées")
    
    # Afficher les colonnes
    st.subheader("📋 Colonnes disponibles")
    cols_display = ", ".join([f"**{i+1}.** {col}" for i, col in enumerate(df.columns)])
    st.markdown(cols_display)
    
    # Onglets
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Barres", "🥧 Circulaires", "📋 Tableaux croisés", "📊 Aperçu données"])
    
    # === ONGLET 1 : BARRES ===
    with tab1:
        st.subheader("Graphiques en barres")
        choix_barres = st.multiselect("Sélectionnez les colonnes :", df.columns, default=df.columns[:3])
        type_barres = st.radio("Orientation :", ["Auto (recommandé)", "Vertical", "Horizontal"])
        
        if st.button("🚀 Générer les graphiques en barres", key="btn_barres"):
            for col in choix_barres:
                series = df[col]
                type_colonne = detecter_type_colonne(series)
                
                if type_colonne == 'vide':
                    st.warning(f"⚠️ {col} : colonne vide")
                    continue
                
                if type_colonne == 'numerique':
                    valeurs = [extraire_numerique(v) for v in series]
                    valeurs = [v for v in valeurs if v is not None]
                    if not valeurs:
                        st.warning(f"⚠️ {col} : aucune valeur numérique")
                        continue
                    counts, categories = categoriser_numeriques(valeurs)
                    effectifs = [counts[cat] for cat in categories]
                    horizontal = len(categories) > 6 or type_barres == "Horizontal"
                else:
                    valeurs = [nettoyer_texte(v) for v in series]
                    counts = Counter(valeurs)
                    categories = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
                    effectifs = [counts[cat] for cat in categories]
                    horizontal = len(categories) > 5 or max(len(str(c)) for c in categories) > 12 or type_barres == "Horizontal"
                
                fig = generer_graphique_barres(categories, effectifs, col, n_total, horizontal)
                st.pyplot(fig)
                st.markdown(get_image_download_link(fig, f"{col.replace(' ', '_')}.png", f"Télécharger {col}.png"), 
                           unsafe_allow_html=True)
                plt.close(fig)
    
    # === ONGLET 2 : CIRCULAIRES ===
    with tab2:
        st.subheader("Graphiques circulaires")
        choix_pie = st.multiselect("Sélectionnez les colonnes (idéalement binaires) :", df.columns)
        
        if st.button("🚀 Générer les graphiques circulaires", key="btn_pie"):
            for col in choix_pie:
                series = df[col]
                valeurs = [nettoyer_texte(v) for v in series]
                counts = Counter(valeurs)
                categories = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
                effectifs = [counts[cat] for cat in categories]
                
                if len(categories) > 8:
                    st.warning(f"⚠️ {col} : trop de catégories ({len(categories)}), fusion automatique")
                
                fig = generer_graphique_circulaire(categories, effectifs, col, n_total)
                st.pyplot(fig)
                st.markdown(get_image_download_link(fig, f"{col.replace(' ', '_')}_pie.png", f"Télécharger {col}_pie.png"), 
                           unsafe_allow_html=True)
                plt.close(fig)
    
    # === ONGLET 3 : TABLEAUX CROISÉS ===
    with tab3:
        st.subheader("Tableaux croisés")
        col1 = st.selectbox("Variable 1 (lignes) :", df.columns, key="cross1")
        col2 = st.selectbox("Variable 2 (colonnes) :", df.columns, key="cross2", index=1)
        
        if st.button("🚀 Générer le tableau croisé", key="btn_cross"):
            fig, tableau, tableau_pct = generer_tableau_croise(df, col1, col2, n_total)
            
            st.pyplot(fig)
            st.markdown(get_image_download_link(fig, f"croise_{col1}_{col2}.png", "Télécharger le graphique"), 
                       unsafe_allow_html=True)
            plt.close(fig)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Tableau des effectifs**")
                st.dataframe(tableau)
            with col_b:
                st.markdown("**Tableau des pourcentages (%)**")
                st.dataframe(tableau_pct.round(1))
    
    # === ONGLET 4 : APERÇU ===
    with tab4:
        st.subheader("Aperçu des données")
        st.dataframe(df.head(20))
        st.markdown(f"**Dimensions :** {df.shape[0]} lignes × {df.shape[1]} colonnes")

else:
    st.info("👆 Veuillez charger un fichier Excel pour commencer")
    
    # Exemple visuel
    st.subheader("📌 Exemple de résultat")
    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        st.markdown("""
        **Graphique en barres :**
        - Pourcentages affichés
        - Effectifs (n=) indiqués
        - Orientation auto ou manuelle
        """)
    with col_ex2:
        st.markdown("""
        **Graphique circulaire :**
        - Pourcentages intégrés
        - Légende avec effectifs
        - Slice principale détachée
        """)