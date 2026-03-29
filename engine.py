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
    Logique : Un flux de l'origine j vers la destination k gêne l'entrée i 
    si l'entrée i se trouve physiquement entre j et k sur l'anneau.
    """
    n = len(matrice_od)
    q_genant = [0] * n
    
    for i in range(n):
        flux_cumule = 0
        # On parcourt toutes les combinaisons Origine (j) -> Destination (k)
        for j in range(n):
            for k in range(n):
                if j == k:
                    continue
                
                # Un véhicule venant de j et allant vers k gêne l'entrée i si :
                # 1. Il n'est pas originaire de i (j != i)
                # 2. Il ne sort pas à i (k != i)
                # 3. Son trajet sur l'anneau passe devant l'entrée i.
                
                # Pour vérifier si i est sur le chemin entre j et k :
                # On regarde si i est compris entre j et k dans le sens horaire.
                est_sur_le_chemin = False
                if j < k:
                    # Trajet simple (ex: de 0 vers 2, passe par 1)
                    if j < i < k:
                        est_sur_le_chemin = True
                else:
                    # Trajet passant par le point de bouclage (ex: de 3 vers 1, passe par 0)
                    if i > j or i < k:
                        est_sur_le_chemin = True
                
                if est_sur_le_chemin:
                    flux_cumule += matrice_od[j][k]
                    
        q_genant[i] = flux_cumule
        
    return q_genant

def evaluer_performance(debit_entrant, capacite):
    """
    Calcule les indicateurs de performance.
    """
    reserve = max(0, capacite - debit_entrant)
    taux_charge = debit_entrant / capacite if capacite > 0 else 1.0
    return reserve, taux_charge