import streamlit as st
import pandas as pd
from engine import calculer_capacite_branche, evaluer_performance
from parameters import get_color

st.set_page_config(page_title="Girabase Lite - Streamlit", layout="wide")

st.title("🚦 Évaluation de Capacité de Giratoire")
st.markdown("Outil basé sur les principes de calcul de **Girabase (CEREMA)**.")

# --- BARRE LATÉRALE : Géométrie ---
st.sidebar.header("📐 Caractéristiques Géométriques")
diametre = st.sidebar.slider("Diamètre extérieur (m)", 20, 100, 40)
nb_voies_anneau = st.sidebar.selectbox("Nombre de voies dans l'anneau", [1, 2])
nb_branches = st.sidebar.number_input("Nombre de branches convergentes", 3, 6, 4)

# --- CORPS PRINCIPAL : Saisie des débits ---
st.header("🚗 Flux de trafic")
st.write(f"Saisissez les débits horaires pour les {nb_branches} branches :")

cols = st.columns(nb_branches)
donnees_entree = []

for i in range(nb_branches):
    with cols[i]:
        st.subheader(f"Branche {i+1}")
        voies_entree = st.selectbox(f"Voies entrée B{i+1}", [1, 2], key=f"v_{i}")
        debit = st.number_input(f"Débit (uvp/h) B{i+1}", 0, 3000, 400, step=50, key=f"d_{i}")
        donnees_entree.append({"id": i+1, "voies": voies_entree, "debit": debit})

# --- CALCULS ET RÉSULTATS ---
if st.button("Calculer les performances"):
    st.header("📊 Résultats de l'analyse")
    
    resultats = []
    
    for branche in donnees_entree:
        # Calcul de la capacité via le moteur engine.py
        capa = calculer_capacite_branche(diametre, nb_voies_anneau, branche["voies"])
        # Calcul de la performance
        reserve, taux = evaluer_performance(branche["debit"], capa)
        
        resultats.append({
            "Branche": f"Branche {branche['id']}",
            "Capacité (uvp/h)": capa,
            "Débit": branche["debit"],
            "Réserve (uvp/h)": reserve,
            "Taux de charge": round(taux * 100, 1),
            "Couleur": get_color(taux)
        })

    # Affichage sous forme de cartes (Metrics)
    res_cols = st.columns(nb_branches)
    for idx, res in enumerate(resultats):
        with res_cols[idx]:
            st.markdown(
                f"""
                <div style="background-color:{res['Couleur']}; padding:20px; border-radius:10px; text-align:center; color:white;">
                    <h3>{res['Branche']}</h3>
                    <p style="font-size: 24px; font-weight: bold;">{res['Taux de charge']}%</p>
                    <p>Réserve : {res['Réserve (uvp/h)']} uvp/h</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

    # Tableau récapitulatif
    st.write("---")
    df_res = pd.DataFrame(resultats).drop(columns=["Couleur"])
    st.table(df_res)
    
    st.success("Analyse terminée. Un taux > 85% indique un risque de congestion important.")