import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Wedge, Rectangle
import matplotlib.transforms as transforms
import matplotlib.cm as cm

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

def dessiner_schema_giratoire(donnees_branches, diametre_exterieur, matrice_od): # NOUVEAU : argument matrice_od
    """
    Génère un schéma vectoriel du giratoire coloré selon la charge,
    avec des flèches courbes montrant les flux O/D.
    """
    nb_branches = len(donnees_branches)
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # --- Paramètres de dessin fixes ---
    r_ext = diametre_exterieur / 10  # Rayon graphique de l'anneau extérieur
    largeur_chaussee_annulaire = 8.0 
    r_int = max(2.0, r_ext - (largeur_chaussee_annulaire / 5))  # Rayon graphique de l'îlot central
    longueur_branche_graphique = 4.0 # Longueur visuelle des branches
    
    # --- Facteur d'échelle pour la largeur ---
    Echelle_Largeur = 1.0 / 3.5 
    
    # --- palette de couleurs pour les origines ---
    # Nous utilisons une palette de couleurs distinctes, une par branche
    color_palette = cm.get_cmap('tab10', nb_branches)
    
    # --- 1. Dessin de l'anneau (gris clair) ---
    anneau = Wedge((0, 0), r_ext, 0, 360, width=r_ext-r_int, 
                   facecolor='#ecf0f1', edgecolor='#34495e', linewidth=2, zorder=1) # zorder 1
    ax.add_patch(anneau)
    
    ilot_central = Circle((0, 0), r_int, facecolor='#bdc3c7', 
                          edgecolor='#34495e', linewidth=1, zorder=2)
    ax.add_patch(ilot_central)

    # --- 2. Dessin et coloration des branches (zorder 10, dessus) ---
    angles = np.linspace(0, 360, nb_branches, endpoint=False)
    
    for i, angle_deg in enumerate(angles):
        angle_rad = np.deg2rad(angle_deg)
        info = donnees_branches[i]
        
        couleur_saturation = info['Couleur']
        largeur_reelle_metres = info['Largeur']
        largeur_graphique = largeur_reelle_metres * Echelle_Largeur
        x_base = r_ext
        y_base = -largeur_graphique / 2
        
        # zorder 10 pour que les branches soient bien visibles
        rect = Rectangle((x_base, y_base), longueur_branche_graphique, largeur_graphique, 
                         facecolor=couleur_saturation, edgecolor='#2c3e50', alpha=0.9, linewidth=1.5, zorder=10)
        
        t_start = ax.transData
        t = transforms.Affine2D().rotate_deg(angle_deg) + t_start
        rect.set_transform(t)
        ax.add_patch(rect)
        
        # Textes (Nom, Charge et Largeur)
        distance_texte = r_ext + longueur_branche_graphique + 1.2
        xt = distance_texte * np.cos(angle_rad)
        yt = distance_texte * np.sin(angle_rad)
        
        ax.text(xt, yt + 0.5, f"Branche {i+1}", 
                fontweight='bold', fontsize=11, ha='center', va='center', zorder=11,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))
        
        ax.text(xt, yt - 0.1, f"{info['Taux de charge']:.1f}%", 
                fontsize=10, ha='center', va='center', color='black', fontweight='semibold', zorder=11)
        
        ax.text(xt, yt - 0.6, f"L={largeur_reelle_metres:.1f}m", 
                fontsize=9, ha='center', va='center', color='#7f8c8d', style='italic', zorder=11)

    # --- 3. NOUVEAU : Dessin des flèches courbes (zorder 5, milieu) ---
    # Cette section ajoute les transferts de flux.
    
    # Échelle pour l'épaisseur de la flèche (uvp/h -> unités graphiques)
    max_flow = np.max(matrice_od)
    if max_flow == 0: max_flow = 1 # Éviter division par 0
    echelle_epaisseur_flux = 0.8 / max_flow # L'épaisseur max sera de 0.8
    
    # Définition de la "zone de dessin" des flèches à l'intérieur de l'anneau
    r_max_flèches = r_ext - 0.3
    r_min_flèches = r_int + 0.3
    largeur_anneau_flèches = r_max_flèches - r_min_flèches

    for i_ori in range(nb_branches): # Ligne (Origine)
        for i_des in range(nb_branches): # Colonne (Destination)
            if i_ori == i_des: continue
            
            debit = matrice_od[i_ori][i_des]
            if debit <= 50: continue # Ignorer les flux très faibles pour la clarté
            
            # 1. Calcul des angles de début et de fin (Wedge utilise le sens anti-horaire)
            # Les angles graphiques sont dans le repère standard, il faut les ajuster
            angle_start_ori = angles[i_ori]
            angle_end_des = angles[i_des]
            
            # Pour un giratoire standard (tourne à droite d'abord), l'arc est toujours anti-horaire
            # Mais les angles calculés par `linspace` peuvent surprendre.
            # Pour s'assurer d'un arc correct, on force l'angle de fin > angle de début
            if angle_end_des < angle_start_ori:
                angle_end_des += 360
            
            # 2. Gestion de l'empilement (Superposition)
            # On calcule la "longueur angulaire" parcourue sur l'anneau
            delta_angle = angle_end_des - angle_start_ori
            
            # Plus le tour est long, plus on rapproche l'arc du centre
            # r_max_flèches (flux courts) -> r_min_flèches (demi-tour/flux longs)
            fract_longueur = (delta_angle - (360/nb_branches)) / 360
            fract_longueur = max(0, min(1, fract_longueur)) # Borner entre 0 et 1
            
            rayon_arc = r_max_flèches - (largeur_anneau_flèches * fract_longueur)
            
            # 3. Calcul de l'épaisseur de l'arc
            épaisseur_arc = debit * echelle_epaisseur_flux
            
            # 4. Couleur et Transparence
            couleur_arc = color_palette(i_ori) # Couleur de la branche d'origine
            
            # alpha (transparence) : plus de transparence si le flux est long
            alpha_arc = 0.6 - (fract_longueur * 0.3)
            alpha_arc = max(0.2, min(0.6, alpha_arc))

            # 5. Dessin de l'arc
            # Un Wedge (arc de cercle) sans width dessine un segment d'anneau (flèche courbe)
            flèche_courbe = Wedge((0, 0), rayon_arc, angle_start_ori, angle_end_des, width=épaisseur_arc, 
                                  facecolor=couleur_arc, edgecolor='none', alpha=alpha_arc, zorder=5) # zorder milieu
            ax.add_patch(flèche_courbe)

            # Optionnel : Ajouter une pointe de flèche à la destination
            # Pour la clarté, nous ne dessinerons que l'arc épais. L'épaisseur indique le volume.

    # --- Nettoyage et cadrage ---
    limite = distance_texte + 2.0
    ax.set_xlim(-limite, limite)
    ax.set_ylim(-limite, limite)
    ax.set_aspect('equal')
    ax.axis('off')
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