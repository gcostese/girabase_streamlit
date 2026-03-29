import numpy as np

def calculer_capacite_girabase(Q_genant, largeur_entree, nb_voies_entree, diametre_exterieur):
    """
    Calcule la capacité d'une branche selon une approche inspirée du modèle SETRA/CEREMA.
    
    Paramètres :
    - Q_genant : Débit sur l'anneau (uvp/h) qui coupe la trajectoire d'entrée.
    - largeur_entree : Largeur de la chaussée en entrée (m).
    - nb_voies_entree : Nombre de voies de la branche.
    - diametre_exterieur : Diamètre extérieur de l'anneau (m).
    """
    
    # 1. Ajustement des paramètres A et B (Base Girabase/SETRA)
    # A représente la capacité maximale théorique quand le débit gênant est nul.
    # B représente la sensibilité au trafic prioritaire.
    
    # Valeurs types pour un giratoire standard (paramètres simplifiés du modèle français)
    if nb_voies_entree == 1:
        A = 1350 + 10 * (largeur_entree - 3.5)
        B = 0.0007  # Sensibilité standard
    else:
        # Pour 2 voies, la capacité de base est plus élevée
        A = 2100 + 15 * (largeur_entree - 7.0)
        B = 0.0006  # Sensibilité moindre car plus de fluidité d'insertion
    
    # 2. Correction liée au diamètre (plus le diamètre est grand, plus l'insertion est aisée)
    # Facteur correctif : les petits giratoires (mini-giratoires) perdent en capacité
    if diametre_exterieur < 25:
        A *= 0.85
    elif diametre_exterieur > 50:
        A *= 1.05

    # 3. Application de la formule exponentielle
    # C = A * exp(-B * Q_g)
    capacite = A * np.exp(-B * Q_genant)
    
    return round(float(capacite))

def calculer_flux_circulant(matrice_od):
    """
    Calcule le flux circulant (Qg) devant chaque entrée i.
    Qg(i) = Somme des flux qui passent devant l'entrée i sans y entrer ni en sortir.
    """
    n = len(matrice_od)
    q_genant = [0] * n
    
    for i in range(n):
        flux = 0
        # Pour chaque flux de l'origine j vers la destination k
        for j in range(n):
            for k in range(n):
                if j == k: continue
                
                # Un flux j->k est gênant pour l'entrée i si i est situé 
                # entre j et k sur l'anneau (sens horaire inversé / sens giratoire)
                # Logique simplifiée : j < i < k (avec gestion circulaire)
                if j < k:
                    if j < i < k:
                        flux += matrice_od[j][k]
                else: # Cas où le flux traverse le point "zéro" de l'indexation
                    if i > j or i < k:
                        flux += matrice_od[j][k]
        q_genant[i] = flux
    return q_genant

def evaluer_performance(debit_entrant, capacite):
    """
    Calcule les indicateurs de performance.
    """
    reserve = max(0, capacite - debit_entrant)
    taux_charge = debit_entrant / capacite if capacite > 0 else 1.0
    return reserve, taux_charge