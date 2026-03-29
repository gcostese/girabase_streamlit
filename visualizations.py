import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Wedge, Rectangle

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
    """
    nb_branches = len(donnees_branches)
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Paramètres de dessin
    r_ext = 5.0  # Rayon graphique fixe pour le dessin
    r_int = 3.0
    largeur_branche = 1.0
    longueur_branche = 4.0
    
    # --- 1. Dessin de l'anneau ---
    anneau = Wedge((0, 0), r_ext, 0, 360, width=r_ext-r_int, facecolor='#ecf0f1', edgecolor='#34495e', zorder=2)
    ax.add_patch(anneau)
    
    # --- 2. Dessin et coloration des branches ---
    # On itère sur chaque branche pour la positionner angulairement
    angles = np.linspace(0, 360, nb_branches, endpoint=False)
    
    for i, angle_deg in enumerate(angles):
        angle_rad = np.deg2rad(angle_deg)
        info = donnees_branches[i]
        couleur = info['Couleur']
        
        # --- Dessin géométrique de la branche (Rectangle orienté) ---
        # Calcul des coordonnées du coin inférieur gauche du rectangle avant rotation
        x_base = r_ext
        y_base = -largeur_branche / 2
        
        rect = Rectangle((x_base, y_base), longueur_branche, largeur_branche, 
                         facecolor=couleur, edgecolor='#2c3e50', alpha=0.8, zorder=1)
        
        # Application de la rotation centrée sur l'origine
        t = plt.transforms.Affine2D().rotate_deg(angle_deg) + ax.transData
        rect.set_transform(t)
        ax.add_patch(rect)
        
        # --- 3. Ajout des textes (Nom et Charge) ---
        # Calcul de la position du texte (un peu plus loin que la branche)
        distance_texte = r_ext + longueur_branche + 1.2
        xt = distance_texte * np.cos(angle_rad)
        yt = distance_texte * np.sin(angle_rad)
        
        # Texte 1 : Nom de la branche (ex: Branche 1)
        ax.text(xt, yt + 0.3, f"Branche {i+1}", 
                fontweight='bold', fontsize=11, ha='center', va='center', 
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))
        
        # Texte 2 : Taux de charge (ex: 75.2%)
        ax.text(xt, yt - 0.3, f"{info['Taux de charge']:.1f}%", 
                fontsize=10, ha='center', va='center', color='black')

    # Nettoyage du graphique
    limite = distance_texte + 1.5
    ax.set_xlim(-limite, limite)
    ax.set_ylim(-limite, limite)
    ax.set_aspect('equal')
    ax.axis('off') # Cache les axes
    plt.tight_layout()
    
    return fig