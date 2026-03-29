import streamlit as st
import pandas as pd
import numpy as np
from engine import calculer_flux_circulant, calculer_capacite_girabase
from parameters import get_color
# NOUVEL IMPORT
from visualizations import generer_heatmap_od, dessiner_schema_giratoire

st.set_page_config(page_title="Girabase Pro + Visualisation", layout="wide")

st.title("🚦 Simulateur Giratoire avec Visualisation Dynamique")

# --- SIDEBAR : GEOMETRIE ---
st.sidebar.image("BlocMarque_RF-Cerema_horizontal.jpg", 
                 use_container_width=True)
st.sidebar.header("📐 Géométrie du Carrefour")
nb_branches = st.sidebar.slider("Nombre de branches", 3, 6, 4)
diametre = st.sidebar.number_input("Diamètre extérieur (m)", 20, 100, 40)

branches_config = []
for i in range(nb_branches):
    st.sidebar.subheader(f"Branche {i+1}")
    voies = st.sidebar.selectbox(f"Voies B{i+1}", [1, 2], key=f"v_{i}")
    # Fixe une largeur par défaut logique selon le nb de voies
    l_defaut = 3.5 if voies == 1 else 7.0
    largeur = st.sidebar.slider(f"Largeur B{i+1} (m)", 3.0, 8.0, l_defaut, key=f"l_{i}")
    branches_config.append({"voies": voies, "largeur": largeur})

# --- CORPS : MATRICE O/D ---
st.header("📝 Matrice Origine-Destination (uvp/h)")
st.info("Saisissez les flux horaires. Les lignes sont les Origines, les colonnes les Destinations.")

# Initialisation de la matrice vide
default_matrix = pd.DataFrame(
    np.zeros((nb_branches, nb_branches)),
    columns=[f"Vers B{i+1}" for i in range(nb_branches)],
    index=[f"Depuis B{i+1}" for i in range(nb_branches)]
)

# Éditeur de données interactif
matrice_saisie = st.data_editor(default_matrix, hide_index=False, use_container_width=True)

if st.button("Lancer l'Analyse", type="primary"):
    
    # 1. Traitement des données
    od_values = matrice_saisie.values.tolist()
    list_q_genant = calculer_flux_circulant(od_values)
    list_q_entrant = [sum(row) for row in od_values]
    
    # Stockage structuré pour les visualisations
    structure_resultats = []
    data_recap_table = []
    
    for i in range(nb_branches):
        capa = calculer_capacite_girabase(
            list_q_genant[i], 
            branches_config[i]["largeur"], 
            branches_config[i]["voies"], 
            diametre
        )
        q_e = list_q_entrant[i]
        taux_charge = (q_e / capa if capa > 0 else 1.0) * 100 # En %
        couleur = get_color(taux_charge / 100)
        
        structure_resultats.append({
            'id': i+1,
            'Taux de charge': taux_charge,
            'Couleur': couleur
        })
        
        data_recap_table.append({
            "Branche": i+1,
            "Flux Entrant (Qe)": q_e,
            "Flux Gênant (Qg)": list_q_genant[i],
            "Capacité (C)": capa,
            "Taux de charge (%)": round(taux_charge, 1),
            "Réserve (uvp/h)": max(0, capa - q_e)
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

    # --- 3. Tableau de synthèse ---
    st.write("### Données détaillées")
    st.dataframe(pd.DataFrame(data_recap_table), use_container_width=True, hide_index=True)