from enum import Enum
from typing import Dict
import inquirer


class Role(Enum):
    VILLAGEOIS = "villageois"
    LOUP_GAROU = "loup_garou"
    PETITE_FILLE = "petite_fille"
    CHASSEUR = "chasseur"
    SORCIERE = "sorciere"
    VOYANTE = "voyante"
    CUPIDON = "cupidon"
    VOLEUR = "voleur"


ROLE_DISTRIBUTIONS = {
    4: [
        {Role.VILLAGEOIS: 2, Role.LOUP_GAROU: 1, Role.VOYANTE: 1},
        {Role.VILLAGEOIS: 3, Role.LOUP_GAROU: 1},  # simpler variant
    ],
    5: [
        {Role.VILLAGEOIS: 2, Role.LOUP_GAROU: 1, Role.VOYANTE: 1, Role.SORCIERE: 1},
        {Role.VILLAGEOIS: 3, Role.LOUP_GAROU: 2},  # more wolves, no specials
    ],
    6: [
        {Role.VILLAGEOIS: 2, Role.LOUP_GAROU: 2, Role.VOYANTE: 1, Role.SORCIERE: 1},
        {Role.VILLAGEOIS: 3, Role.LOUP_GAROU: 2, Role.VOYANTE: 1},  # no witch
    ],
    7: [
        {Role.VILLAGEOIS: 3, Role.LOUP_GAROU: 2, Role.VOYANTE: 1, Role.SORCIERE: 1},
        {Role.VILLAGEOIS: 4, Role.LOUP_GAROU: 2, Role.VOYANTE: 1},  # lighter variant
    ],
    8: [
        {Role.VILLAGEOIS: 3, Role.LOUP_GAROU: 2, Role.VOYANTE: 1, Role.SORCIERE: 1, Role.CUPIDON: 1},
        {Role.VILLAGEOIS: 4, Role.LOUP_GAROU: 3, Role.VOYANTE: 1},  # tougher for villagers
    ],
    9: [
        {Role.VILLAGEOIS: 4, Role.LOUP_GAROU: 2, Role.VOYANTE: 1, Role.SORCIERE: 1, Role.CUPIDON: 1},
        {Role.VILLAGEOIS: 3, Role.LOUP_GAROU: 3, Role.VOYANTE: 1, Role.SORCIERE: 1},  # stronger wolves
    ],
    10: [
        {Role.VILLAGEOIS: 4, Role.LOUP_GAROU: 3, Role.VOYANTE: 1, Role.SORCIERE: 1, Role.CUPIDON: 1},
        {Role.VILLAGEOIS: 5, Role.LOUP_GAROU: 3, Role.VOYANTE: 1, Role.CHASSEUR: 1},  # replace witch
    ],
    11: [
        {Role.VILLAGEOIS: 5, Role.LOUP_GAROU: 3, Role.VOYANTE: 1, Role.SORCIERE: 1, Role.CUPIDON: 1},
        {Role.VILLAGEOIS: 4, Role.LOUP_GAROU: 3, Role.VOYANTE: 1, Role.SORCIERE: 1, Role.CHASSEUR: 1},  # adds hunter
    ],
    12: [
        {Role.VILLAGEOIS: 4, Role.LOUP_GAROU: 3, Role.VOYANTE: 1, Role.SORCIERE: 1, Role.CUPIDON: 1, Role.CHASSEUR: 1},
        {Role.VILLAGEOIS: 5, Role.LOUP_GAROU: 3, Role.VOYANTE: 1, Role.SORCIERE: 1, Role.CHASSEUR: 1},  # no cupid
        {Role.VILLAGEOIS: 5, Role.LOUP_GAROU: 4, Role.VOYANTE: 1, Role.SORCIERE: 1},  # stronger wolves variant
    ],
}


def _format_role_distribution(distribution: Dict[Role, int]) -> str:
    """Format a role distribution for display"""
    roles_text = []
    for role, count in distribution.items():
        role_name = role.value.replace('_', ' ').title()
        roles_text.append(f"{role_name}: {count}")
    return " | ".join(roles_text)


def _calculate_balance_score(distribution: Dict[Role, int]) -> str:
    """Calculate and return a balance indicator for the distribution"""
    total_players = sum(distribution.values())
    wolves = distribution.get(Role.LOUP_GAROU, 0)
    specials = sum(count for role, count in distribution.items() if role not in [Role.VILLAGEOIS, Role.LOUP_GAROU])

    wolf_ratio = wolves / total_players
    if wolf_ratio >= 0.4:
        return "🐺 Wolf-favored"
    elif wolf_ratio <= 0.2:
        return "👥 Village-favored"
    elif specials >= 3:
        return "🔮 Special-heavy"
    else:
        return "⚖️ Balanced"


def set_lineup(num_players: int) -> Dict[Role, int]:
    """Calculate optimal role distribution for given number of players with GM selection"""
    variants = ROLE_DISTRIBUTIONS[num_players]

    # Present options to game master
    print(f"\n🎮 Game Master: Choose lineup for {num_players} players")
    print("=" * 60)

    choices = []
    for i, variant in enumerate(variants):
        balance = _calculate_balance_score(variant)
        description = _format_role_distribution(variant)
        choice_text = f"Lineup {i+1} ({balance}): {description}"
        choices.append(choice_text)

    questions = [
        inquirer.List(
            'lineup',
            message="Select a lineup",
            choices=choices,
            carousel=True
        ),
    ]

    try:
        answers = inquirer.prompt(questions)
        if answers:
            # Extract lineup index from choice
            selected_index = int(answers['lineup'].split()[1]) - 1
            selected_variant = variants[selected_index]

            print(f"\n✅ Selected lineup: {_format_role_distribution(selected_variant)}")
            return selected_variant.copy()
        else:
            # Fallback to first variant if cancelled
            return variants[0].copy()
    except (KeyboardInterrupt, EOFError):
        print("\n⚠️ Selection cancelled, using default variant")
        return variants[0].copy()
