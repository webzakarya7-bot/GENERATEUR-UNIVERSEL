"""
============================================================
GENERATEUR UNIVERSEL DE GRAPHIQUES v4.0
Compatible avec n'importe quel fichier Excel
Menu interactif - L'utilisateur CHOISIT ce qu'il veut generer
============================================================
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import os
import sys
import re
from matplotlib.backends.backend_pdf import PdfPages

# Configuration du style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['grid.linestyle'] = '-'

COULEURS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', 
            '#e67e22', '#1abc9c', '#34495e', '#95a5a6', '#d35400',
            '#c0392b', '#7f8c8d', '#16a085', '#2980b9', '#8e44ad']

PIE_COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', 
              '#e67e22', '#1abc9c', '#34495e']


def detecter_type_colonne(series):
    """Detecte automatiquement le type de donnees dans une colonne"""
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

    if ratio > 0.8:
        return 'numerique'
    else:
        return 'texte'


def extraire_numerique(valeur):
    """Extrait le premier nombre trouve dans une chaine"""
    if pd.isna(valeur):
        return None
    texte = str(valeur).lower()
    unites = ['j', 'min', 'dh', 'h', 'seance', 'séance', '%', '°', 'kg', 'cm', 'm', 'ml', 'mg', 'ans', 'mois']
    for unite in unites:
        texte = texte.replace(unite, '')
    texte = texte.replace(',', '.').strip()

    nombres = re.findall(r'\d+\.?\d*', texte)
    if nombres:
        try:
            return float(nombres[0])
        except:
            return None
    return None


def categoriser_numeriques(valeurs, n_bins=5):
    """Categorise des valeurs numeriques en intervalles"""
    valeurs = [v for v in valeurs if v is not None]
    if not valeurs:
        return {}, []

    min_val = min(valeurs)
    max_val = max(valeurs)
    valeurs_uniques = sorted(set(valeurs))

    if len(valeurs_uniques) > 15:
        n_bins = min(10, len(valeurs_uniques) // 2 + 1)

    if len(valeurs_uniques) <= 8:
        counts = {}
        for v in valeurs_uniques:
            counts[str(int(v)) if v == int(v) else str(v)] = valeurs.count(v)
        return counts, list(counts.keys())

    intervalle = (max_val - min_val) / n_bins
    bins = []
    labels = []

    for i in range(n_bins):
        debut = min_val + i * intervalle
        fin = min_val + (i + 1) * intervalle
        if i == n_bins - 1:
            fin = max_val + 0.001
        bins.append((debut, fin))
        if intervalle >= 1:
            labels.append(f"{int(debut)}-{int(fin)}")
        else:
            labels.append(f"{debut:.1f}-{fin:.1f}")

    counts = {label: 0 for label in labels}
    for v in valeurs:
        for i, (debut, fin) in enumerate(bins):
            if debut <= v < fin:
                counts[labels[i]] += 1
                break

    counts = {k: v for k, v in counts.items() if v > 0}
    return counts, list(counts.keys())


def nettoyer_texte(valeur):
    """Nettoie et standardise un texte"""
    if pd.isna(valeur):
        return "Non precise"
    texte = str(valeur).strip()
    if texte.lower() in ['', 'nan', 'none', 'null', 'na', 'n/a', '-']:
        return "Non precise"
    return texte


def generer_graphique_barres(categories, effectifs, titre_colonne, nom_fichier, n_total, horizontal=False):
    """Genere un graphique en barres"""
    if not categories or not effectifs:
        print(f"  ⚠️ Aucune donnee pour {titre_colonne}")
        return False

    if len(categories) > 12:
        combined = list(zip(categories, effectifs))
        combined.sort(key=lambda x: x[1], reverse=True)
        top = combined[:11]
        others_sum = sum(x[1] for x in combined[11:])
        categories = [x[0] for x in top] + ["Autres"]
        effectifs = [x[1] for x in top] + [others_sum]
        horizontal = True

    percents = [(c / n_total) * 100 for c in effectifs]

    fig, ax = plt.subplots(figsize=(12 if horizontal else 10, 8 if horizontal else 7))

    titre_principal = titre_colonne.upper().replace('_', ' ')
    fig.suptitle(f'{titre_principal} - Resultats en POURCENTAGE (n={n_total})', 
                 fontsize=13, fontweight='bold', y=0.98)

    colors = COULEURS[:len(categories)]

    if horizontal:
        bars = ax.barh(range(len(categories)), percents, color=colors, edgecolor='white', height=0.6)
        for i, (bar, pct, cnt) in enumerate(zip(bars, percents, effectifs)):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                    f'{pct:.1f}%\n(n={cnt})', ha='left', va='center', 
                    fontsize=9, fontweight='bold')
        ax.set_yticks(range(len(categories)))
        ax.set_yticklabels(categories)
        ax.set_xlabel('Pourcentage (%)', fontsize=11)
        ax.invert_yaxis()
    else:
        bars = ax.bar(range(len(categories)), percents, color=colors, edgecolor='white', width=0.6)
        for i, (bar, pct, cnt) in enumerate(zip(bars, percents, effectifs)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{pct:.1f}%\n(n={cnt})', ha='center', va='bottom', 
                    fontsize=9, fontweight='bold')
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=30, ha='right', fontsize=9)
        ax.set_ylabel('Pourcentage (%)', fontsize=11)

    ax.set_title(f'Repartition par {titre_colonne.replace("_", " ").title()}', 
                 fontsize=12, fontweight='bold', pad=15)

    if horizontal:
        ax.set_xlim(0, max(percents) + 10)
    else:
        ax.set_ylim(0, max(percents) + 8)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    if nom_fichier:
        plt.savefig(nom_fichier, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close()
    return True


def generer_graphique_circulaire(categories, effectifs, titre_colonne, nom_fichier, n_total):
    """Genere un graphique circulaire (pie chart)"""
    if not categories or not effectifs:
        return False
    if len(categories) > 8:
        combined = list(zip(categories, effectifs))
        combined.sort(key=lambda x: x[1], reverse=True)
        top = combined[:7]
        others_sum = sum(x[1] for x in combined[7:])
        categories = [x[0] for x in top] + ["Autres"]
        effectifs = [x[1] for x in top] + [others_sum]

    percents = [(c / n_total) * 100 for c in effectifs]
    colors = PIE_COLORS[:len(categories)]

    fig, ax = plt.subplots(figsize=(10, 8))
    titre_principal = titre_colonne.upper().replace('_', ' ')
    fig.suptitle(f'{titre_principal} - Repartition en POURCENTAGE (n={n_total})', 
                 fontsize=13, fontweight='bold', y=0.98)

    explode = [0.05 if i == 0 else 0 for i in range(len(categories))]

    wedges, texts, autotexts = ax.pie(
        percents, 
        explode=explode,
        labels=categories,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        shadow=True,
        textprops={'fontsize': 10}
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)

    ax.set_title(f'Repartition par {titre_colonne.replace("_", " ").title()}', 
                 fontsize=12, fontweight='bold', pad=20)

    legend_labels = [f'{cat} (n={eff})' for cat, eff in zip(categories, effectifs)]
    ax.legend(wedges, legend_labels, title="Categories", loc="center left", 
              bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)

    plt.tight_layout(rect=[0, 0, 0.85, 0.95])
    if nom_fichier:
        plt.savefig(nom_fichier, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close()
    return True


def generer_tableau_croise(df, col1, col2, dossier_sortie, n_total):
    """Genere un tableau croise avec graphique en barres groupees"""
    print(f"\n📊 Tableau croise : {col1} × {col2}")

    tableau = pd.crosstab(df[col1], df[col2], margins=True)
    tableau_pct = pd.crosstab(df[col1], df[col2], normalize='index') * 100

    tableau.index = [nettoyer_texte(i) for i in tableau.index]
    tableau.columns = [nettoyer_texte(c) for c in tableau.columns]

    print("\n📋 Tableau des effectifs :")
    print(tableau.to_string())
    print("\n📋 Tableau des pourcentages (%) :")
    print(tableau_pct.round(1).to_string())

    tableau_graph = tableau.drop('All', errors='ignore').drop('All', axis=1, errors='ignore')

    if tableau_graph.empty or len(tableau_graph.columns) == 0:
        print("  ⚠️ Donnees insuffisantes pour le graphique croise")
        return

    fig, ax = plt.subplots(figsize=(14, 8))
    titre_principal = f"{col1.upper().replace('_', ' ')} × {col2.upper().replace('_', ' ')}"
    fig.suptitle(f'{titre_principal} - TABLEAU CROISE (n={n_total})', 
                 fontsize=13, fontweight='bold', y=0.98)

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
    ax.set_title('Distribution croisee', fontsize=12, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(tableau_graph.index, rotation=30, ha='right')
    ax.legend(title=col2.replace('_', ' ').title(), loc='upper right')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    nom_fichier = os.path.join(dossier_sortie, f"croise_{col1.lower().replace(' ', '_')}_{col2.lower().replace(' ', '_')}.png")
    plt.savefig(nom_fichier, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close()

    print(f"  ✅ Graphique croise sauvegarde : {os.path.basename(nom_fichier)}")

    excel_croise = os.path.join(dossier_sortie, f"croise_{col1.lower().replace(' ', '_')}_{col2.lower().replace(' ', '_')}.xlsx")
    with pd.ExcelWriter(excel_croise, engine='openpyxl') as writer:
        tableau.to_excel(writer, sheet_name='Effectifs')
        tableau_pct.round(2).to_excel(writer, sheet_name='Pourcentages')
    print(f"  ✅ Tableaux Excel sauvegardes : {os.path.basename(excel_croise)}")


def analyser_colonne(df, nom_colonne, dossier_sortie, n_total, type_graphique='barres'):
    """Analyse une colonne et genere le graphique approprie"""
    print(f"\n📊 Analyse : {nom_colonne} (Type: {type_graphique})")

    series = df[nom_colonne]
    type_colonne = detecter_type_colonne(series)

    if type_colonne == 'vide':
        print(f"  ⚠️ Colonne vide, ignoree")
        return

    nom_fichier_base = nom_colonne.lower().replace(' ', '_').replace('/', '_')[:50]

    if type_colonne == 'numerique':
        valeurs = [extraire_numerique(v) for v in series]
        valeurs = [v for v in valeurs if v is not None]
        if not valeurs:
            print(f"  ⚠️ Aucune valeur numerique exploitable")
            return
        counts, categories = categoriser_numeriques(valeurs)
        effectifs = [counts[cat] for cat in categories]
        horizontal = len(categories) > 6
    else:
        valeurs = [nettoyer_texte(v) for v in series]
        counts = Counter(valeurs)
        categories = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
        effectifs = [counts[cat] for cat in categories]
        horizontal = len(categories) > 5 or max(len(str(c)) for c in categories) > 12

    if type_graphique == 'circulaire' and len(categories) <= 8:
        chemin_fichier = os.path.join(dossier_sortie, f"{nom_fichier_base}_pie.png")
        generer_graphique_circulaire(categories, effectifs, nom_colonne, chemin_fichier, n_total)
    else:
        if type_graphique == 'circulaire':
            print(f"  ℹ️ Trop de categories pour un graphique circulaire, utilisation des barres")
        chemin_fichier = os.path.join(dossier_sortie, f"{nom_fichier_base}.png")
        generer_graphique_barres(categories, effectifs, nom_colonne, chemin_fichier, n_total, horizontal)


def generer_pdf_rapport(dossier_sortie, nom_pdf="rapport_graphiques.pdf"):
    """Genere un PDF regroupant tous les graphiques PNG du dossier"""
    chemin_pdf = os.path.join(dossier_sortie, nom_pdf)

    fichiers_png = sorted([f for f in os.listdir(dossier_sortie) if f.endswith('.png')])

    if not fichiers_png:
        print("\n⚠️ Aucun graphique PNG trouve pour le PDF")
        return

    print(f"\n📄 Generation du PDF : {nom_pdf}")

    with PdfPages(chemin_pdf) as pdf:
        for fichier in fichiers_png:
            chemin_img = os.path.join(dossier_sortie, fichier)
            fig, ax = plt.subplots(figsize=(11.69, 8.27))
            ax.imshow(plt.imread(chemin_img))
            ax.axis('off')
            ax.set_title(fichier.replace('.png', '').replace('_', ' ').title(), 
                        fontsize=10, pad=10)
            pdf.savefig(fig, bbox_inches='tight', facecolor='white')
            plt.close()

        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        ax.axis('off')
        ax.text(0.5, 0.9, 'RAPPORT DE GRAPHIQUES', ha='center', va='top', 
                fontsize=20, fontweight='bold', transform=ax.transAxes)
        ax.text(0.5, 0.8, f'Nombre de graphiques : {len(fichiers_png)}', 
                ha='center', va='top', fontsize=12, transform=ax.transAxes)
        ax.text(0.5, 0.7, f'Date de generation : {pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")}', 
                ha='center', va='top', fontsize=12, transform=ax.transAxes)

        y_pos = 0.6
        for i, fichier in enumerate(fichiers_png, 1):
            ax.text(0.1, y_pos, f'{i}. {fichier.replace(".png", "").replace("_", " ").title()}', 
                    ha='left', va='top', fontsize=10, transform=ax.transAxes)
            y_pos -= 0.05

        pdf.savefig(fig, bbox_inches='tight', facecolor='white')
        plt.close()

    print(f"  ✅ PDF genere : {nom_pdf} ({len(fichiers_png)+1} pages)")


def menu_principal(df, dossier_sortie, n_total):
    """Menu interactif principal - L'utilisateur CHOISIT"""

    while True:
        print("\n" + "=" * 60)
        print("  MENU PRINCIPAL - Que voulez-vous generer ?")
        print("=" * 60)
        print("  1. 📊 Graphiques en BARRES (toutes les colonnes)")
        print("  2. 🥧 Graphiques CIRCULAIRES (choisir les colonnes)")
        print("  3. 📋 TABLEAUX CROISES (2 variables)")
        print("  4. 📄 Rapport PDF (tous les graphiques existants)")
        print("  5. 🎉 TOUT GENERER (barres + circulaires + PDF)")
        print("  0. ❌ Quitter")
        print("=" * 60)

        choix = input("Votre choix (0-5) : ").strip()

        if choix == '0':
            print("\n👋 Au revoir !")
            break

        elif choix == '1':
            print("\n" + "=" * 60)
            print("  GENERATION DES GRAPHES EN BARRES")
            print("=" * 60)
            choix_colonnes = input("Colonnes a traiter (ex: 1,3,5 ou 'all' pour toutes) : ").strip().lower()

            if choix_colonnes == 'all':
                colonnes_a_traiter = list(df.columns)
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in choix_colonnes.split(',')]
                    colonnes_a_traiter = [df.columns[i] for i in indices if 0 <= i < len(df.columns)]
                except:
                    print("❌ Choix invalide")
                    continue

            for col in colonnes_a_traiter:
                try:
                    analyser_colonne(df, col, dossier_sortie, n_total, type_graphique='barres')
                except Exception as e:
                    print(f"  ❌ Erreur sur {col} : {e}")

            print(f"\n✅ {len(colonnes_a_traiter)} graphique(s) en barres genere(s)")

        elif choix == '2':
            print("\n" + "=" * 60)
            print("  GENERATION DES GRAPHES CIRCULAIRES")
            print("=" * 60)
            print("  Colonnes disponibles :")
            for i, col in enumerate(df.columns, 1):
                print(f"    {i}. {col}")

            choix_colonnes = input("\nNumeros des colonnes pour graphiques circulaires (ex: 2,5,8) : ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in choix_colonnes.split(',')]
                colonnes_pie = [df.columns[i] for i in indices if 0 <= i < len(df.columns)]
            except:
                print("❌ Choix invalide")
                continue

            for col in colonnes_pie:
                try:
                    analyser_colonne(df, col, dossier_sortie, n_total, type_graphique='circulaire')
                except Exception as e:
                    print(f"  ❌ Erreur sur {col} : {e}")

            print(f"\n✅ {len(colonnes_pie)} graphique(s) circulaire(s) genere(s)")

        elif choix == '3':
            print("\n" + "=" * 60)
            print("  GENERATION DES TABLEAUX CROISES")
            print("=" * 60)
            print("  Colonnes disponibles :")
            for i, col in enumerate(df.columns, 1):
                print(f"    {i}. {col}")

            while True:
                paire = input("\nPaire a croiser (ex: 1,3) ou 'fin' : ").strip().lower()
                if paire in ['fin', '']:
                    break
                try:
                    idx1, idx2 = [int(x.strip()) - 1 for x in paire.split(',')]
                    if 0 <= idx1 < len(df.columns) and 0 <= idx2 < len(df.columns):
                        generer_tableau_croise(df, df.columns[idx1], df.columns[idx2], dossier_sortie, n_total)
                    else:
                        print("  ❌ Numero de colonne invalide")
                except Exception as e:
                    print(f"  ❌ Erreur : {e}")

        elif choix == '4':
            print("\n" + "=" * 60)
            print("  GENERATION DU RAPPORT PDF")
            print("=" * 60)
            nom_pdf = input("Nom du PDF [rapport_graphiques.pdf] : ").strip()
            if not nom_pdf:
                nom_pdf = "rapport_graphiques.pdf"
            generer_pdf_rapport(dossier_sortie, nom_pdf)

        elif choix == '5':
            print("\n" + "=" * 60)
            print("  GENERATION COMPLETE (Barres + Circulaires + PDF)")
            print("=" * 60)

            # Barres
            for col in df.columns:
                try:
                    analyser_colonne(df, col, dossier_sortie, n_total, type_graphique='barres')
                except Exception as e:
                    print(f"  ❌ Erreur sur {col} : {e}")

            # Circulaires pour variables binaires
            colonnes_binaires = []
            for col in df.columns:
                valeurs_uniques = set(str(v).strip().lower() for v in df[col].dropna().unique())
                if len(valeurs_uniques) == 2 and any(v in ['oui', 'non', 'féminin', 'masculin', 'homme', 'femme', 'yes', 'no'] for v in valeurs_uniques):
                    colonnes_binaires.append(col)

            print(f"\n🥧 Variables binaires detectees : {len(colonnes_binaires)}")
            for col in colonnes_binaires:
                try:
                    analyser_colonne(df, col, dossier_sortie, n_total, type_graphique='circulaire')
                except Exception as e:
                    print(f"  ❌ Erreur sur {col} : {e}")

            # PDF
            generer_pdf_rapport(dossier_sortie, "rapport_complet.pdf")

            print("\n🎉 Generation complete terminee !")

        else:
            print("\n❌ Choix invalide. Veuillez entrer un nombre entre 0 et 5.")


def main():
    """Fonction principale"""
    print("=" * 70)
    print("  GENERATEUR UNIVERSEL DE GRAPHIQUES v4.0")
    print("  Menu interactif - VOUS choisissez ce que vous voulez generer")
    print("=" * 70)
    print()

    chemin_excel = input("📁 Entrez le chemin du fichier Excel : ").strip().strip('"')

    if not os.path.exists(chemin_excel):
        print(f"\n❌ Erreur : Fichier non trouve : {chemin_excel}")
        print("\nExemple de chemin : C:\\Users\\hp\\Desktop\\mon_fichier.xlsx")
        return

    dossier_sortie_default = os.path.join(os.path.dirname(chemin_excel), "Graphiques_Generes")
    dossier_sortie = input(f"\n📂 Dossier de sortie [{dossier_sortie_default}] : ").strip().strip('"')
    if not dossier_sortie:
        dossier_sortie = dossier_sortie_default

    os.makedirs(dossier_sortie, exist_ok=True)

    print(f"\n📖 Lecture de : {chemin_excel}")
    try:
        df = pd.read_excel(chemin_excel, engine='openpyxl')
    except:
        try:
            df = pd.read_excel(chemin_excel, engine='xlrd')
        except Exception as e:
            print(f"❌ Erreur lors de la lecture : {e}")
            return

    n_total = len(df)
    print(f"✅ {n_total} lignes lues")
    print(f"📋 Colonnes trouvees : {len(df.columns)}")
    print()

    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")

    # Lancer le menu interactif
    menu_principal(df, dossier_sortie, n_total)

    # Bilan final
    n_graphiques = len([f for f in os.listdir(dossier_sortie) if f.endswith('.png')])
    n_excel = len([f for f in os.listdir(dossier_sortie) if f.endswith('.xlsx')])
    n_pdf = len([f for f in os.listdir(dossier_sortie) if f.endswith('.pdf')])

    print("\n" + "=" * 70)
    print(f"📊 BILAN FINAL")
    print(f"   📁 Dossier : {dossier_sortie}")
    print(f"   📊 {n_graphiques} graphiques PNG")
    print(f"   📊 {n_excel} tableaux Excel")
    print(f"   📄 {n_pdf} rapport PDF")
    print("=" * 70)


if __name__ == '__main__':
    main()
