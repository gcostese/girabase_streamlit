import streamlit as st
import pandas as pd
import numpy as np
from parameters import get_color
from engine import calculer_flux_circulant, calculer_capacite_girabase, calculer_capacite_sortie
from visualizations import generer_heatmap_od, dessiner_schema_giratoire, plot_saturation_curve, plot_comparaison_barres, plot_chord_diagram

st.set_page_config(page_title="Girabase", 
                   page_icon="🚗",
                   layout="wide")

st.title("🔄🛣️ Estimation de la capacité d'un carrefour giratoire")

st.markdown("""
            Bienvenue dans cette application interactive dédiée à l'analyse de la capacité 
            des carrefours giratoires selon la méthode **Girabase** du Cerema.  
            
            Le logiciel Girabase est un outil de référence en ingénierie routière, 
            spécifiquement conçu pour l'analyse et le dimensionnement des carrefours giratoires. 
            Développé historiquement par le réseau technique de l'État 
            (notamment le Setra et le Certu, aujourd'hui intégrés au [Cerema](https://www.cerema.fr/)), 
            il est utilisé par les bureaux d'études et les gestionnaires routiers
            pour valider la **faisabilité technique** de projets d'aménagement, 
            du mini-giratoire aux structures complexes de 3 à 8 branches,
            ou pour établir un **diagnostic d'un aménagement existant**.

            Le logiciel Girabase n'est plus maintenu et 
            son code est en [open source](https://github.com/CEREMA/territoires-ville.Girabase).

            L'objectif principal du logiciel est d'évaluer la capacité de débit 
            d'un carrefour en fonction des flux de trafic prévisibles 
            et des caractéristiques géométriques de l'infrastructure 
            (rayon de l'anneau, largeur des entrées, inclinaison, etc.). 
            Sa base de calcul repose sur des modèles mathématiques d'acceptation d'intervalles 
            (comme la formule simplifiée de Siegloch ou celle plus détaillée de Harders), 
            qui simulent l'interaction entre le trafic entrant et le trafic circulant sur l'anneau.
            """)

# --- SIDEBAR : GEOMETRIE ---
st.sidebar.image("BlocMarque_RF-Cerema_horizontal.jpg", 
                 use_container_width=True)
st.sidebar.header("📐 Géométrie du carrefour")
nb_branches = st.sidebar.slider("Nombre de branches", 3, 6, 4)
diametre = st.sidebar.number_input(
    "Diamètre extérieur (m)", 20, 100, 40, 
    help="Distance entre les bords extérieurs de la chaussée. Un grand diamètre facilite l'insertion."
)

branches_config = []
for i in range(nb_branches):
    st.sidebar.subheader(f"Branche {i+1}")
    voies = st.sidebar.selectbox(f"Voies B{i+1}", [1, 2], key=f"v_{i}")
    # Fixe une largeur par défaut logique selon le nb de voies
    l_defaut = 3.5 if voies == 1 else 7.0
    largeur = st.sidebar.slider(f"Largeur B{i+1} (m)", 3.0, 8.0, l_defaut, key=f"l_{i}")
    branches_config.append({"voies": voies, "largeur": largeur})

# --- PARAMÈTRES AVANCÉS ---
with st.sidebar.expander("⚙️ Paramètres avancés (Expert)"):
    mode_expert = st.checkbox("Utiliser modèle théorique (t0/ts)")
    t0 = st.slider("Intervalle critique (t0) en s", 2.0, 6.0, 4.0)
    ts = st.slider("Temps de suivi (ts) en s", 1.0, 4.0, 2.0)

# --- CELLULE D'INFORMATION PÉDAGOGIQUE ---
with st.expander("ℹ️ Comprendre la méthode de calcul (Girabase / Cerema)", expanded=False):
    st.markdown("""
    ### Qu'est-ce que la capacité d'un giratoire ?
    La capacité d'une entrée de giratoire est le débit maximal de véhicules qui peuvent s'y insérer en une heure. Elle dépend de deux facteurs principaux :
    
    1.  **La géométrie :** Plus l'entrée est large et le diamètre du carrefour grand, plus il est facile de s'insérer.
    2.  **Le flux gênant ($Q_g$) :** C'est le trafic qui circule déjà sur l'anneau devant vous. Plus ce flux est dense, moins il y a d'intervalles ("creux") pour entrer.
    """)

    # Utilisation d'une image ou d'un schéma explicatif
    st.info("**Principe de la loi de Harders :** La capacité diminue de façon exponentielle à mesure que le trafic sur l'anneau augmente.")
    
    st.latex(r"C = A \cdot e^{-B \cdot Q_g}")
    
    st.markdown("""
    * **A** : Capacité théorique maximale (si l'anneau était vide).
    * **B** : Sensibilité des conducteurs au trafic prioritaire.
    * **$Q_g$** : Flux prioritaire sur l'anneau (calculé via la matrice Origine-Destination).
    
    **Interprétation des résultats :**
    * 🟢 **< 70%** : Circulation fluide.
    * 🟡 **70% à 85%** : Zone de vigilance, apparition de files d'attente aux heures de pointe.
    * 🔴 **> 85%** : Risque de congestion saturation et blocage du carrefour.
    """)

# --- CORPS : MATRICE O/D ---
st.header("📝 Matrice Origine-Destination (uvp/h)")
st.info("Saisissez les flux horaires. Les lignes sont les Origines, les colonnes les Destinations.")

# Initialisation de la matrice vide
default_matrix = pd.DataFrame(
    np.zeros((nb_branches, nb_branches)),
    columns=[f"Vers B{i+1}" for i in range(nb_branches)],
    index=[f"Depuis B{i+1}" for i in range(nb_branches)]
)

# --- AIDE À LA SAISIE MATRICE O/D ---
with st.expander("💡 Comment remplir la matrice des flux ?", expanded=False):
    st.markdown("""
    La matrice permet de décrire **qui va où**. 
    
    * **Les Lignes (Horizontales) :** Représentent la branche d'**ORIGINE** (d'où viennent les voitures).
    * **Les Colonnes (Verticales) :** Représentent la branche de **DESTINATION** (où elles vont).
    
    **Exemple concret :**
    Si 200 véhicules arrivent par la **Branche 1** et veulent sortir à la **Branche 3** :
    1. Trouvez la ligne **"Depuis Branche 1"**.
    2. Trouvez la colonne **"Vers Branche 3"**.
    3. Saisissez **200** dans cette case.
    """)
    
    # Un petit tableau d'exemple statique pour illustrer
    exemple_data = {
        "Vers B1": [0, 50, 100],
        "Vers B2": [150, 0, 30],
        "Vers B3": [200, 80, 0]
    }
    st.table(pd.DataFrame(exemple_data, index=["Depuis B1", "Depuis B2", "Depuis B3"]))
    
    st.warning("⚠️ Les cases diagonales (ex: depuis B1 vers B1) doivent rester à **0**, " \
    "car un véhicule ne ressort pas par la branche où il est entré.")

# Éditeur de données interactif
matrice_saisie = st.data_editor(default_matrix, hide_index=False, use_container_width=True)

# --- ALERTES DE SÉCURITÉ ---
if (matrice_saisie.values < 0).any():
    st.error("⚠️ Alerte : La matrice contient des valeurs négatives. Veuillez corriger les flux.")
    st.stop()

flux_total = matrice_saisie.values.sum()
if flux_total > 10000:
    st.warning(f"⚠️ Volume absurde : {flux_total} uvp/h. Ce carrefour est physiquement incapable de traiter ce flux.")

if st.button("Lancer l'analyse", type="primary"):
    
    # 1. Traitement des données
    od_values = matrice_saisie.values.tolist()
    list_q_genant, q_sortant = calculer_flux_circulant(od_values)
    list_q_entrant = [sum(row) for row in od_values]
    
    # Stockage structuré pour les visualisations
    structure_resultats = []
    data_recap_table = []
    
    for i in range(nb_branches):
        params = {"t0": t0, "ts": ts} if mode_expert else {}
        capa_e = calculer_capacite_girabase(
            list_q_genant[i], 
            branches_config[i]["largeur"], 
            branches_config[i]["voies"], 
            diametre
        )
        capa_s = calculer_capacite_sortie(3.5, 1)
        q_e = list_q_entrant[i]
        taux_charge = (q_e / capa_e if capa_e > 0 else 1.0) * 100 # En %
        couleur = get_color(taux_charge / 100)
        
        structure_resultats.append({
            'id': i+1,
            'Taux de charge': taux_charge,
            'Couleur': couleur,
            'Largeur': branches_config[i]["largeur"],
            "Entrée (Réel/Capa)": f"{q_e} / {capa_e}",
            "Sortie (Réel/Capa)": f"{q_sortant[i]} / {capa_s}",
            "Charge (%)": round((q_e / capa_e)*100, 1) if capa_e > 0 else 100,
            "capa": capa_e, "flux": q_e, "qg": list_q_genant[i]
        })
        
        data_recap_table.append({
            "Branche": i+1,
            "Flux Entrant (Qe)": q_e,
            "Flux Gênant (Qg)": list_q_genant[i],
            "Capacité (C)": capa_e,
            "Taux de charge (%)": round(taux_charge, 1),
            "Réserve (uvp/h)": max(0, capa_e - q_e)
        })

    st.write("---")
    
    # --- 2. Zone des Visualisations ---
    col_map, col_schema = st.columns([1, 1.2])
    
    with col_map:
        st.subheader("Analyse des Flux (Heatmap)")
        fig_heat = generer_heatmap_od(od_values)
        st.pyplot(fig_heat)
        
    with col_schema:
        st.subheader("État de Charge du Carrefour")
        # Appel de la fonction graphique complexe
        fig_schema = dessiner_schema_giratoire(structure_resultats, diametre)
        st.pyplot(fig_schema)

    st.plotly_chart(plot_comparaison_barres([f"B{r['Branche']}" for r in structure_resultats], 
                                           [r['flux'] for r in structure_resultats], 
                                           [r['capa'] for r in structure_resultats]))
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_chord_diagram(matrice_saisie.values), use_container_width=True)
    with col2:
        # Affichage de la courbe pour la branche la plus chargée
        critique = max(structure_resultats, key=lambda x: x['Charge (%)'])
        # Calcul de A et B pour la courbe
        A = (3600/ts) if mode_expert else (1350) # Simplifié pour l'exemple
        B = (t0 - ts/2)/3600 if mode_expert else 0.0007
        st.pyplot(plot_saturation_curve(A, B, critique['qg'], critique['flux'], f"B{critique['Branche']}"))

    st.table(pd.DataFrame(structure_resultats).drop(columns=['capa', 'flux', 'qg']))

    # --- 3. Tableau de synthèse ---
    st.write("### Données détaillées")
    st.dataframe(pd.DataFrame(data_recap_table), use_container_width=True, hide_index=True)