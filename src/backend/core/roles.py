from dataclasses import dataclass, field
from typing import Optional, Dict
import click
from .game import Player, Game
from .role_distributor import Role


@dataclass
class Sorciere(Player):
    """Witch role: can heal or poison once."""

    potion_soin_utilisee: bool = False
    potion_poison_utilisee: bool = False

    def heal(self, target: Player) -> None:
        if not self.potion_soin_utilisee:
            self.potion_soin_utilisee = True
            target.alive = True

    def poison(self, target: Player) -> None:
        if not self.potion_poison_utilisee:
            self.potion_poison_utilisee = True
            target.kill()

    def choose_player_to_save_or_kill(self, game: "Game") -> None:  # type: ignore[name-defined]
        if not self.potion_soin_utilisee and game.recently_killed:

            save_choice = game.select_player(
                author=self,
                players=game.recently_killed,
                alive=False,
                can_select_self=True,
                can_select_none=True,
            )
            if save_choice:
                self.heal(save_choice)
                game.recently_killed.remove(save_choice)

        if not self.potion_poison_utilisee:
            poison_choice = game.select_player(
                author=self, alive=True, can_select_self=True, can_select_none=True
            )
            if poison_choice:
                self.poison(poison_choice)


@dataclass
class Voyante(Player):
    """Seer role: can reveal a player's role."""

    investigations: Dict[str, Role] = field(default_factory=dict)

    def choose_player_to_see(self, game: "Game") -> None:  # type: ignore[name-defined]
        available_players = [
            player
            for player in game.players
            if player.name not in self.investigations
        ]
        target = game.select_player(
            author=self,
            players=available_players,
            alive=True,
            can_select_self=False,
        )
        if target and target.name not in self.investigations:
            self.investigations[target.name] = target.role
            click.echo(
                f"🔍 Voyante {self.name} sees that {target.name} is a {target.role.value.replace('_', ' ').title()}"
            )


@dataclass
class Chasseur(Player):
    """Hunter role: chooses a revenge target when dying."""

    revenge_target: Optional[Player] = None

    def choose_revenge_target(self, target: Player) -> None:
        if not self.alive and self.revenge_target is None:
            self.revenge_target = target
            target.kill()


@dataclass
class Cupidon(Player):
    """Cupid: binds two players as lovers."""

    lovers_chosen: tuple = field(default_factory=tuple)

    def choose_lovers(self, game: "Game") -> None:  # type: ignore[name-defined]
        player1 = game.select_player(author=self, alive=True, can_select_self=True)
        if not player1:
            return
        player2 = game.select_player(
            author=self,
            players=[p for p in game.players if p != player1],
            alive=True,
            can_select_self=True,
        )
        if player2 and not self.lovers_chosen:
            self.lovers_chosen = (player1, player2)
            player1.lover = player2
            player2.lover = player1


@dataclass
class Voleur(Player):
    """Thief: can steal another player's role at the beginning."""

    role_stolen: bool = False
    original_role: Optional[Role] = None

    def steal_role(self, target: Player) -> None:
        if not self.role_stolen:
            self.original_role = target.role
            target.role = self.role
            self.role = self.original_role
            self.role_stolen = True
