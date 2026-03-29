import numpy as np

def calculer_capacite_branche(diametre, nb_voies_anneau, nb_voies_entree):
    """
    Calcule la capacité théorique d'une branche (C) en fonction de la géométrie.
    Ceci est une simplification pédagogique des formules Girabase.
    """
    # La capacité de base augmente avec le diamètre et le nombre de voies
    capa_theorique = 1500 + (diametre * 10) + (nb_voies_entree * 200)
    
    if nb_voies_anneau > 1:
        capa_theorique *= 1.2
        
    return round(capa_theorique)

def evaluer_performance(debit_entrant, capacite):
    """
    Calcule les indicateurs de performance.
    """
    reserve = max(0, capacite - debit_entrant)
    taux_charge = debit_entrant / capacite if capacite > 0 else 1.0
    return reserve, taux_charge