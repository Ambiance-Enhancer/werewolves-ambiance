from dataclasses import dataclass, field
from random import shuffle
from typing import List, Dict, Optional, Type
from enum import Enum
import uuid
import click
import inquirer
from .role_distributor import Role, set_lineup


class GameStatus(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    FINISHED = "finished"


class State(Enum):
    START_UP = "start_up"
    CUPIDON = "cupidon"
    AMOUREUX = "amoureux"
    VOLEUR = "voleur"
    VOYANTE = "voyante"
    LOUP_GAROU = "loup_garou"
    SORCIERE = "sorciere"
    MAYOR_ELECTION = "mayor_election"
    DAY_VOTE = "vote"
    COMPLETED = "completed"


class NightState(Enum):
    """States used during night phases"""

    START_UP = "start_up"
    VOYANTE = "voyante"
    LOUP_GAROU = "loup_garou"
    SORCIERE = "sorciere"
    COMPLETED = "completed"


class DayState(Enum):
    """States used during day phases"""

    START_UP = "start_up"
    DAY_VOTE = "vote"
    COMPLETED = "completed"


class Camp(Enum):
    """Represents the team/camp of a player"""

    VILLAGEOIS = "villageois"
    LOUP_GAROU = "loup_garou"
    AMOUREUX = "amoureux"


class ActionType(Enum):
    VOTE = "vote"
    KILL = "kill"
    HEAL = "heal"
    POISON = "poison"
    REVEAL = "reveal"
    CHOOSE_LOVERS = "choose_lovers"
    STEAL_ROLE = "steal_role"
    REVENGE_KILL = "revenge_kill"


@dataclass
class Player:
    """Represents a player in a game."""

    name: str
    role: Optional[Role] = None
    alive: bool = True
    is_revealed: bool = False
    is_mayor: bool = False

    @property
    def camp(self) -> Camp:
        """Determine the player's camp (Team)."""
        # If part of a mixed couple (Wolf + Villager), they form a separate camp
        if self.lover and self.role and self.lover.role:
            my_is_wolf = self.role == Role.LOUP_GAROU
            lover_is_wolf = self.lover.role == Role.LOUP_GAROU

            # XOR: if one is wolf and the other is not
            if my_is_wolf != lover_is_wolf:
                return Camp.AMOUREUX

        # Otherwise, camp is determined by role
        if self.role == Role.LOUP_GAROU:
            return Camp.LOUP_GAROU

        return Camp.VILLAGEOIS

    lover: Optional["Player"] = None

    def kill(self) -> None:
        """Mark the player as dead; if they have an alive lover, also kill them."""
        self.alive = False
        if self.lover and self.lover.alive:
            self.lover.kill()


@dataclass
class Action:
    """Represents an action taken by some actor targeting a player."""

    actor: Player
    action: ActionType
    target: Player


@dataclass
class Log:
    """Log for a single round/period with recorded actions."""

    round_number: int
    period: State
    actions: List[Action]


@dataclass
class Game:
    """Main game object holding players, roles, and logs."""

    uid: str
    status: GameStatus
    period: State
    round_number: int
    players: List[Player] = field(default_factory=list)
    lineup: Dict[Role, int] = field(default_factory=dict)
    game_log: List[Log] = field(default_factory=list)
    recently_killed: List[Player] = field(default_factory=list)

    def __init__(self, num_players: int) -> None:
        self.uid = str(uuid.uuid4())[:8]
        self.status = GameStatus.WAITING
        self.period = State.START_UP
        self.round_number = 1
        self.players = []
        self.lineup = {}
        self.game_log = []
        self.recently_killed = []

        try:
            if num_players == -1:
                questions = [
                    inquirer.List(
                        "num_players",
                        message="How many players?",
                        choices=[str(i) for i in range(4, 13)],
                        default="6",
                        carousel=True,
                    ),
                ]

                answers = inquirer.prompt(questions)
                if not answers:
                    click.echo(click.style("❌ Game setup cancelled", fg="yellow"))
                    return

                num_players = int(answers["num_players"])

            for i in range(num_players):
                questions = [
                    inquirer.Text(
                        "name",
                        message=f"Enter name for player {i+1}",
                        default=f"Player{i+1}",
                        validate=lambda _, x: len(x.strip()) > 0
                        or "Name cannot be empty",
                    ),
                ]

                answers = inquirer.prompt(questions)
                if not answers:
                    click.echo(click.style("❌ Player creation cancelled", fg="yellow"))
                    return

                name = answers["name"].strip() or f"Player{i+1}"
                self.players.append(Player(name=name))

            if self.players:
                try:
                    self.lineup = set_lineup(len(self.players))
                    self.distribute_roles()
                    click.echo(
                        click.style(
                            f"✅ Game created successfully with {len(self.players)} players",
                            fg="green",
                        )
                    )
                except Exception as e:
                    click.echo(click.style(f"❌ Error setting up roles: {e}", fg="red"))
            else:
                click.echo(click.style("❌ No players were created", fg="red"))

        except KeyboardInterrupt:
            click.echo(click.style("\n❌ Game creation cancelled", fg="yellow"))
        except Exception as e:
            click.echo(click.style(f"❌ Error: {e}", fg="red"))

    def elect_mayor(self, players: List[Player]) -> bool:
        """Elect a mayor by inputting the name of the chosen player (external vote)."""
        chosen = self.select_player(alive=True)
        if chosen:
            for p in self.players:
                p.is_mayor = False
            chosen.is_mayor = True
            click.echo(f"👑 {chosen.name} is now the Mayor!")
            return True
        return False

    def village_vote_input(self) -> Optional[Player]:
        """Input the name of the player chosen by the village to be eliminated."""
        chosen = self.select_player(alive=True)
        if chosen:
            self.village_vote(chosen)
            click.echo(f"💀 {chosen.name} has been eliminated by the village!")
            return chosen
        return None

    def save_action(self, actor: Player, action: ActionType, target: Player) -> None:
        """Save an action to the current game's log."""
        if not self.game_log:
            # create a log entry for the current round/period if missing
            self.game_log.append(
                Log(round_number=self.round_number, period=self.period, actions=[])
            )

        self.game_log[self.round_number - 1].actions.append(
            Action(actor=actor, action=action, target=target)
        )

    def show_players(self) -> None:
        """Print players and minimal status info."""
        if not self.players:
            click.echo(click.style("❌ No players in the game", fg="red"))
            return

        click.echo(f"\n👥 Players in Game {self.uid}:")
        click.echo("=" * 50)

        for i, player in enumerate(self.players, 1):
            status = "💀  " if not player.alive else "❤️  "
            mayor = "👑  " if player.is_mayor else ""
            revealed = "🔍  " if player.is_revealed else ""
            lover = f"💕 {player.lover.name}" if player.lover else ""
            role = (
                player.role.value.replace("_", " ").title()
                if player.role
                else "No Role"
            )

            click.echo(f"{i:2d}. {player.name:<15} {status}{mayor}{revealed}")
            click.echo(f"    Role: {role}")
            if lover:
                click.echo(f"    Lover: {lover}")
            click.echo()

    def select_player(
        self,
        author: Optional[Player] = None,
        players: Optional[List[Player]] = None,
        alive: Optional[bool] = True,
        is_revealed: Optional[bool] = None,
        can_select_self: bool = False,
        can_select_none: bool = False,
    ) -> Optional[Player]:
        """Prompt user to select a player filtered by criteria. Returns the Player or None."""
        if players is None:
            players = self.players

        filtered_players = [
            player
            for player in players
            if (alive is None or player.alive == alive)
            and (is_revealed is None or player.is_revealed == is_revealed)
            and (can_select_self or player != author)
        ]

        choices = [player.name for player in filtered_players]
        if can_select_none:
            choices.insert(0, "None")
        if not choices:
            click.echo("No players available for selection.")
            return None

        questions = [
            inquirer.List(
                "player", message="Select a player:", choices=choices, carousel=True
            ),
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return None
        choice = answers["player"]
        if choice == "None":
            return None
        return self.get_player_by_name(choice)

    def show_game_state(self) -> None:
        """Show overall game state summary."""
        click.echo(f"\n🎮 Game State: {self.uid}")
        click.echo("=" * 30)
        click.echo(f"Status: {self.status.value}")
        click.echo(f"Period: {self.period.value.replace('_', ' ').title()}")
        click.echo(f"Round: {self.round_number}")
        click.echo(f"Players Alive: {sum(1 for p in self.players if p.alive)}")
        click.echo(f"Players Total: {len(self.players)}")

    def loup_garou_kill(self) -> None:
        """Kill a selected player during wolf night action."""
        target = self.select_player(alive=True, can_select_self=False)
        if target:
            self.recently_killed.append(target)
            target.kill()

    def village_vote(self, target: Player) -> None:
        """Execute a village vote result to kill a player."""
        target.kill()

    def distribute_roles(self) -> None:
        """Distribute roles to players according to `self.lineup`. Imports role classes at runtime to avoid circular imports."""
        if len(self.players) != sum(self.lineup.values()):
            raise ValueError("Number of players must match role distribution")

        roles_list: List[Role] = []
        for role, count in self.lineup.items():
            roles_list.extend([role] * count)

        shuffle(roles_list)

        # Import role classes here to avoid circular imports
        from .roles import Cupidon, Voyante, Sorciere, Chasseur, Voleur

        role_class_map = {
            Role.CUPIDON: Cupidon,
            Role.VOYANTE: Voyante,
            Role.SORCIERE: Sorciere,
            Role.CHASSEUR: Chasseur,
            Role.VOLEUR: Voleur,
            Role.LOUP_GAROU: Player,
            Role.VILLAGEOIS: Player,
        }

        for i, player in enumerate(self.players):
            role_enum = roles_list[i]
            role_class = role_class_map.get(role_enum, Player)
            new_player = role_class(name=player.name)
            new_player.role = role_enum
            self.players[i] = new_player

    def get_role_instance(self, role_class: Type[Role]) -> Optional[Player]:
        """Return the first player instance that matches a Role enum derived from `role_class` name."""
        role_enum_name = role_class.__name__.upper()
        try:
            role_enum = Role[role_enum_name]
        except KeyError:
            return None

        for player in self.players:
            if player.role == role_enum:
                return player
        return None

    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Find a player by name (exact match)."""
        for player in self.players:
            if player.name == name:
                return player
        return None

    def is_over(self) -> bool:
        """Check if the game is over based on Camps."""
        alive_players = [p for p in self.players if p.alive]

        if not alive_players:
            click.echo("\n💀 Everyone is dead. Nobody wins.")
            self.status = GameStatus.FINISHED
            return True

        # Count players per camp
        counts = {Camp.VILLAGEOIS: 0, Camp.LOUP_GAROU: 0, Camp.AMOUREUX: 0}

        for p in alive_players:
            counts[p.camp] += 1

        # villagers_count = counts[Camp.VILLAGEOIS]
        wolves_count = counts[Camp.LOUP_GAROU]
        lovers_count = counts[Camp.AMOUREUX]

        # Count how many camps have players
        camps_alive = sum(1 for count in counts.values() if count > 0)

        # Game ends only when all remaining players are from the same camp
        if camps_alive == 1:
            if lovers_count > 0:
                click.echo("\n💕 The Lovers have won! Love conquers all.")
            elif wolves_count > 0:
                click.echo("\n🐺 The Werewolves have won!")
            else:
                click.echo("\n🎉 The Village has won!")
            self.status = GameStatus.FINISHED
            return True

        return False
