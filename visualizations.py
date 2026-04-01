import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Wedge, Rectangle
import matplotlib.transforms as transforms

def generer_heatmap_od(matrice_od):
    """Génère une heatmap Seaborn à partir de la matrice O/D."""
    n = len(matrice_od)
    cols = [f"Vers B{i+1}" for i in range(n)]
    idx = [f"Depuis B{i+1}" for i in range(n)]
    df = pd.DataFrame(matrice_od, columns=cols, index=idx)
    
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(df, annot=True, fmt=".0f", cmap="YlOrRd", ax=ax, cbar_kws={'label': 'uvp/h'})
    ax.set_title("Intensité des flux Origine-Destination")
    plt.tight_layout()
    return fig

def dessiner_schema_giratoire(donnees_branches, diametre_exterieur):
    """
    Génère un schéma vectoriel du giratoire coloré selon la charge.
    L'épaisseur des branches varie proportionnellement à leur largeur réelle.
    """
    nb_branches = len(donnees_branches)
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # --- Paramètres de dessin fixes ---
    r_ext = 5.0  # Rayon graphique de l'anneau extérieur
    r_int = 3.0  # Rayon graphique de l'îlot central
    longueur_branche_graphique = 4.0 # Longueur visuelle des branches
    
    # --- Facteur d'échelle pour la largeur ---
    # On définit qu'une voie standard de 3.5m correspond à une unité graphique de 1.0
    Echelle_Largeur = 1.0 / 3.5 
    
    # --- 1. Dessin de l'anneau ---
    # L'anneau est dessiné en gris clair pour simuler la chaussée
    anneau = Wedge((0, 0), r_ext, 0, 360, width=r_ext-r_int, 
                   facecolor='#ecf0f1', edgecolor='#34495e', linewidth=2, zorder=2)
    ax.add_patch(anneau)
    
    # --- 2. Dessin et coloration des branches ---
    # Calcul des angles pour répartir les branches uniformément autour du cercle
    angles = np.linspace(0, 360, nb_branches, endpoint=False)
    
    for i, angle_deg in enumerate(angles):
        angle_rad = np.deg2rad(angle_deg)
        info = donnees_branches[i]
        
        # Récupération des données réelles
        couleur = info['Couleur']
        largeur_reelle_metres = info['Largeur'] # <-- NOUVEAU : récupère la largeur saisie
        
        # --- Calcul de la largeur graphique (épaisseur du rectangle) ---
        largeur_graphique = largeur_reelle_metres * Echelle_Largeur
        
        # --- Dessin géométrique de la branche (Rectangle orienté) ---
        # Le point d'ancrage (x_base, y_base) est le coin inférieur gauche du rectangle.
        # Pour que la branche soit centrée sur l'axe radial, on décale y_base de la moitié de sa largeur.
        x_base = r_ext
        y_base = -largeur_graphique / 2 # <-- AJUSTEMENT pour centrage
        
        # Création du rectangle (facecolor=couleur de charge, edgecolor=contour)
        rect = Rectangle((x_base, y_base), longueur_branche_graphique, largeur_graphique, 
                         facecolor=couleur, edgecolor='#2c3e50', alpha=0.8, linewidth=1.5, zorder=1)
        
        # Application de la rotation centrée sur l'origine du repère (0,0)
        # plt.transforms permet de combiner une rotation et l'application aux coordonnées du graphique
        t_start = ax.transData
        t = transforms.Affine2D().rotate_deg(angle_deg) + t_start
        rect.set_transform(t)
        ax.add_patch(rect)
        
        # --- 3. Ajout des textes (Nom, Charge et Largeur) ---
        # Calcul de la position du texte (au bout de la branche dessinée)
        distance_texte = r_ext + longueur_branche_graphique + 1.2
        xt = distance_texte * np.cos(angle_rad)
        yt = distance_texte * np.sin(angle_rad)
        
        # Texte 1 : Nom de la branche (ex: Branche 1)
        ax.text(xt, yt + 0.5, f"Branche {i+1}", 
                fontweight='bold', fontsize=11, ha='center', va='center', 
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))
        
        # Texte 2 : Taux de charge (ex: 75.2%)
        ax.text(xt, yt - 0.1, f"{info['Taux de charge']:.1f}%", 
                fontsize=10, ha='center', va='center', color='black', fontweight='semibold')
        
        # Texte 3 : Largeur réelle (ex: L=3.5m) <-- NOUVEAU
        ax.text(xt, yt - 0.6, f"L={largeur_reelle_metres:.1f}m", 
                fontsize=9, ha='center', va='center', color='#7f8c8d', style='italic')

    # --- Nettoyage et cadrage du graphique ---
    limite = distance_texte + 2.0 # Définit les limites de vue pour ne pas couper les textes
    ax.set_xlim(-limite, limite)
    ax.set_ylim(-limite, limite)
    ax.set_aspect('equal') # Force un ratio 1:1 pour que le cercle reste un cercle
    ax.axis('off') # Cache les axes X et Y pour un rendu propre
    plt.tight_layout()
    
    return fig

def plot_saturation_curve(A, B, q_g, q_e, nom_branche):
    fig, ax = plt.subplots(figsize=(5, 3))
    x = np.linspace(0, 2000, 100)
    y = A * np.exp(-B * x)
    ax.plot(x, y, color='#3498db', label="Courbe de capacité théorique")
    ax.scatter(q_g, q_e, color='red', s=50, zorder=5, label="Point de fonctionnement actuel")
    ax.set_title(f"Saturation de la branche {nom_branche}", fontsize=10)
    ax.set_xlabel("Flux gênant Qg (uvp/h)", fontsize=8)
    ax.set_ylabel("Capacité d'entrée (uvp/h)", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.legend(prop={'size': 7})
    return fig

def plot_comparaison_barres(labels, flux, capacites):
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Flux Réel', x=labels, y=flux, marker_color='#34495e'))
    fig.add_trace(go.Bar(name='Capacité Totale', x=labels, y=capacites, marker_color='#2ecc71'))
    fig.update_layout(barmode='group', height=300, margin=dict(l=20, r=20, t=30, b=20))
    return fig

def plot_chord_diagram(matrice_od):
    # Version simplifiée via Plotly Sankey (plus lisible qu'un Chord pour les flux routiers)
    n = len(matrice_od)
    sources, targets, values = [], [], []
    for i in range(n):
        for j in range(n):
            if matrice_od[i][j] > 0:
                sources.append(i)
                targets.append(j + n)
                values.append(matrice_od[i][j])
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
                  label=[f"Entrée B{i+1}" for i in range(n)] + [f"Sortie B{i+1}" for i in range(n)]),
        link=dict(source=sources, target=targets, value=values)
    )])
    fig.update_layout(title_text="Répartition des transferts", font_size=10)
    return fig