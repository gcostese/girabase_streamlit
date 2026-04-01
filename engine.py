import numpy as np

def calculer_capacite_girabase(Q_genant, largeur_entree, nb_voies_entree, diametre_exterieur, t0=None, ts=None):
    """
    Calcule la capacité d'une branche selon une approche inspirée du modèle SETRA/CEREMA.
    
    Paramètres :
    - Q_genant : Débit sur l'anneau (uvp/h) qui coupe la trajectoire d'entrée.
    - largeur_entree : Largeur de la chaussée en entrée (m).
    - nb_voies_entree : Nombre de voies de la branche.
    - diametre_exterieur : Diamètre extérieur de l'anneau (m).
    """
    nb_voies_entree = int(nb_voies_entree)
    
    if t0 and ts:
        # Modèle théorique (Type Harders simplifié)
        A = 3600 / ts
        B = (t0 - (ts / 2)) / 3600
        capacite = A * np.exp(-B * Q_genant)
    else:
        # Modèle empirique Girabase standard
        if nb_voies_entree == 1:
            A = 1350 + 10 * (largeur_entree - 3.5)
            B = 0.0007
        else:
            A = 2100 + 15 * (largeur_entree - 7.0)
            B = 0.0006
            
        if diametre_exterieur < 25: A *= 0.85
        elif diametre_exterieur > 50: A *= 1.05
        capacite = A * np.exp(-B * Q_genant)
    
    return round(float(capacite))

def calculer_capacite_sortie(largeur_sortie, nb_voies_sortie):
    """
    Estime la capacité d'évacuation d'une branche.
    Standard : ~1200 à 1500 uvp/h par voie de sortie.
    """
    return int(nb_voies_sortie) * 1500 + (100 * (largeur_sortie - (int(nb_voies_sortie) * 3.5)))

def calculer_flux_circulant(matrice_od):
    """
    Calcule le flux circulant (Qg) devant chaque entrée i.
    Logique : Un flux de l'origine j vers la destination k gêne l'entrée i 
    si l'entrée i se trouve physiquement entre j et k sur l'anneau.
    """
    n = len(matrice_od)
    q_genant = [0] * n
    q_sortant = [0] * n
    
    for i in range(n):
        flux_cumule = 0
        # On parcourt toutes les combinaisons Origine (j) -> Destination (k)
        for j in range(n):
            for k in range(n):
                if j == k:
                    continue
                
                # Flux sortant à la branche i
                if k == i:
                    q_sortant[i] += matrice_od[j][k]
                
                # Un véhicule venant de j et allant vers k gêne l'entrée i si :
                # 1. Il n'est pas originaire de i (j != i)
                # 2. Il ne sort pas à i (k != i)
                # 3. Son trajet sur l'anneau passe devant l'entrée i.
                
                # Flux gênant devant l'entrée i
                # Pour vérifier si i est sur le chemin entre j et k :
                # On regarde si i est compris entre j et k dans le sens horaire.
                if j < k:
                    if j < i < k:
                        flux_cumule += matrice_od[j][k]
                else:
                    if i > j or i < k:
                        flux_cumule += matrice_od[j][k]
                    
        q_genant[i] = flux_cumule
        
    return q_genant, q_sortant

def evaluer_performance(debit_entrant, capacite):
    """
    Calcule les indicateurs de performance.
    """
    reserve = max(0, capacite - debit_entrant)
    taux_charge = debit_entrant / capacite if capacite > 0 else 1.0
    return reserve, taux_charge