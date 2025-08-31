from typing import Dict, List
from .models import Role, Player
import random
import inquirer

class RoleDistributor:
    # Standard role distribution rules for different player counts
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

    def _format_role_distribution(self, distribution: Dict[Role, int]) -> str:
        """Format a role distribution for display"""
        roles_text = []
        for role, count in distribution.items():
            role_name = role.value.replace('_', ' ').title()
            roles_text.append(f"{role_name}: {count}")
        return " | ".join(roles_text)

    def _calculate_balance_score(self, distribution: Dict[Role, int]) -> str:
        """Calculate and return a balance indicator for the distribution"""
        total_players = sum(distribution.values())
        wolves = distribution.get(Role.LOUP_GAROU, 0)
        specials = sum(count for role, count in distribution.items() 
                      if role not in [Role.VILLAGEOIS, Role.LOUP_GAROU])
        
        wolf_ratio = wolves / total_players
        if wolf_ratio >= 0.4:
            return "🐺 Wolf-favored"
        elif wolf_ratio <= 0.2:
            return "👥 Village-favored"
        elif specials >= 3:
            return "🔮 Special-heavy"
        else:
            return "⚖️ Balanced"

    def get_role_counts(self, num_players: int, interactive: bool = True) -> Dict[Role, int]:
        """Calculate optimal role distribution for given number of players with GM selection"""
        if num_players < 4:
            raise ValueError("Minimum 4 players required")
        
        if num_players not in self.ROLE_DISTRIBUTIONS:
            # For larger games, scale from the 12-player distribution
            base_distribution = self.ROLE_DISTRIBUTIONS[12][0].copy()  # Take first variant
            extra_players = num_players - 12
            base_distribution[Role.VILLAGEOIS] += extra_players
            return base_distribution
        
        variants = self.ROLE_DISTRIBUTIONS[num_players]
        
        if not interactive or len(variants) == 1:
            return variants[0].copy()
        
        # Present options to game master
        print(f"\n🎮 Game Master: Choose lineup for {num_players} players")
        print("=" * 60)
        
        choices = []
        for i, variant in enumerate(variants):
            balance = self._calculate_balance_score(variant)
            description = self._format_role_distribution(variant)
            choice_text = f"Variant {i+1} ({balance}): {description}"
            choices.append(choice_text)
        
        questions = [
            inquirer.List(
                'variant',
                message="Select the role distribution variant",
                choices=choices,
                carousel=True
            ),
        ]
        
        try:
            answers = inquirer.prompt(questions)
            if answers:
                # Extract variant index from choice
                selected_index = int(answers['variant'].split()[1]) - 1
                selected_variant = variants[selected_index]
                
                print(f"\n✅ Selected variant: {self._format_role_distribution(selected_variant)}")
                return selected_variant.copy()
            else:
                # Fallback to first variant if cancelled
                return variants[0].copy()
        except (KeyboardInterrupt, EOFError):
            print("\n⚠️ Selection cancelled, using default variant")
            return variants[0].copy()
    
    def distribute_roles(self, player_names: List[str], num_players: int, interactive: bool = True) -> List[Player]:
        """Assign balanced roles to players"""
        if len(player_names) != num_players:
            raise ValueError("Number of player names must match num_players")
        
        role_counts = self.get_role_counts(num_players, interactive)
        
        # Create list of roles based on counts
        roles_list = []
        for role, count in role_counts.items():
            roles_list.extend([role] * count)
        
        # Shuffle roles for random distribution
        random.shuffle(roles_list)
        
        # Create Player objects with proper role-specific classes
        players = []
        for i, name in enumerate(player_names):
            role = roles_list[i]
            
            # Create role-specific player instances
            if role == Role.SORCIERE:
                from .models import Sorciere
                player = Sorciere(name=name, role=role)
            elif role == Role.VOYANTE:
                from .models import Voyante
                player = Voyante(name=name, role=role)
            elif role == Role.LOUP_GAROU:
                from .models import LoupGarou
                player = LoupGarou(name=name, role=role)
            elif role == Role.CHASSEUR:
                from .models import Chasseur
                player = Chasseur(name=name, role=role)
            elif role == Role.CUPIDON:
                from .models import Cupidon
                player = Cupidon(name=name, role=role)
            elif role == Role.VOLEUR:
                from .models import Voleur
                player = Voleur(name=name, role=role)
            else:
                # Default to base Player class for villagers and other roles
                from .models import Player
                player = Player(name=name, role=role)
            
            players.append(player)
        
        return players