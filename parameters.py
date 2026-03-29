# Seuils de taux de charge (V/C ratio) pour le code couleur
SEUILS_CHARGE = {
    "excellent": 0.7,  # Vert en dessous de 70%
    "limite": 0.85,    # Orange entre 70% et 85%
    "critique": 1.0    # Rouge au dessus de 85% / 100%
}

def get_color(taux_charge):
    """Retourne une couleur hexadécimale selon le taux de charge."""
    if taux_charge < SEUILS_CHARGE["excellent"]:
        return "#28a745" # Vert
    elif taux_charge < SEUILS_CHARGE["limite"]:
        return "#ffc107" # Orange/Jaune
    else:
        return "#dc3545" # Rouge