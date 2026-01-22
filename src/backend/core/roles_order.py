# roles_order.py
"""
Définit l'ordre prédéfini d'appel des rôles pour le jeu du Loup-Garou.
Inclut une fonction utilitaire pour déterminer l'ordre des rôles à appeler selon les rôles présents dans la partie.
"""

from typing import List, Type
from src.backend.core.roles import Cupidon, Voleur, Voyante, Sorciere, Chasseur

# Ordre classique des rôles pour la nuit du Loup-Garou
ROLES_ORDER: List[Type] = [
    Cupidon,    # Cupidon agit en premier (première nuit)
    Voleur,     # Voleur (première nuit)
    Voyante,    # Voyante
    Sorciere,   # Sorcière
    Chasseur,   # Chasseur (agit à la mort, mais on le garde pour l'ordre)
]

def get_roles_order_for_game(game) -> List[Type]:
    """
    Retourne la liste ordonnée des classes de rôles à appeler selon les rôles présents dans la partie.
    :param game: instance de Game
    :return: liste ordonnée des classes de rôles présents dans la partie
    """
    present_roles = set(type(player) for player in game.players)
    return [role for role in ROLES_ORDER if role in present_roles]
