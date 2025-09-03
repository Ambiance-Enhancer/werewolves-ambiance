from dataclasses import dataclass, field
from random import shuffle
from typing import List, Dict, Optional
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


class FirstNightState(Enum):
    START_UP = "start_up"
    CUPIDON = "cupidon"
    AMOUREUX = "amoureux"
    VOLEUR = "voleur"
    VOYANTE = "voyante"
    LOUP_GAROU = "loup_garou"
    SORCIERE = "sorciere"
    COMPLETED = "completed"


class NightState(Enum):
    START_UP = "start_up"
    VOYANTE = "voyante"
    LOUP_GAROU = "loup_garou"
    SORCIERE = "sorciere"
    COMPLETED = "completed"


class FirstDayState(Enum):
    START_UP = "start_up"
    MAYOR_ELECTION = "mayor_election"
    DAY_VOTE = "vote"
    COMPLETED = "completed"


class DayState(Enum):
    START_UP = "start_up"
    DAY_VOTE = "vote"
    COMPLETED = "completed"


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
    name: str
    role: Optional[Role] = None
    game: Optional['Game'] = None  # Reference to the game instance
    alive: bool = True
    isRevealed: bool = False
    isMayor: bool = False
    lover: Optional['Player'] = None  # Self-reference for lover relationship

    def kill(self) -> None:
        self.alive = False
        if self.lover and self.lover.alive:
            self.lover.kill()


@dataclass
class Action:
    actor: Player
    action: ActionType
    target: Player


@dataclass
class Log:
    round_number: int
    period: State
    actions: List[Action]


@dataclass
class Game:
    uid: str
    status: GameStatus
    period: State
    round_number: int
    players: List[Player] = field(default_factory=list)
    lineup: Dict[Role, int] = field(default_factory=dict)
    gameLog: List[Log] = field(default_factory=list)

    def __init__(self, num_players: int):
        """Initialize a player by asking the user game parameters"""
        self.uid = str(uuid.uuid4())[:8]
        self.status = GameStatus.WAITING
        self.period = State.START_UP
        self.round_number = 1
        self.players = []
        self.lineup = {}
        self.gameLog = []

        try:
            if num_players == -1:
                # Select number of players
                questions = [
                    inquirer.List(
                        'num_players',
                        message="How many players?",
                        choices=[str(i) for i in range(4, 13)],
                        default="6",
                        carousel=True
                    ),
                ]

                answers = inquirer.prompt(questions)
                if not answers:
                    click.echo(click.style("❌ Game setup cancelled", fg='yellow'))
                    return

                num_players = int(answers['num_players'])

            for i in range(num_players):
                questions = [
                    inquirer.Text(
                        'name',
                        message=f"Enter name for player {i+1}",
                        default=f"Player{i+1}",
                        validate=lambda _, x: len(x.strip()) > 0 or "Name cannot be empty"
                    ),
                ]

                answers = inquirer.prompt(questions)
                if not answers:
                    click.echo(click.style("❌ Player creation cancelled", fg='yellow'))
                    return

                name = answers['name'].strip() or f"Player{i+1}"
                self.players.append(Player(name=name, game=self))

            if self.players:
                try:
                    self.lineup = set_lineup(len(self.players))
                    self.distribute_roles()
                    click.echo(click.style(f"✅ Game created successfully with {len(self.players)} players", fg='green'))
                except Exception as e:
                    click.echo(click.style(f"❌ Error setting up roles: {e}", fg='red'))
            else:
                click.echo(click.style("❌ No players were created", fg='red'))

        except KeyboardInterrupt:
            click.echo(click.style("\n❌ Game creation cancelled", fg='yellow'))
        except Exception as e:
            click.echo(click.style(f"❌ Error: {e}", fg='red'))

    def electMayor(self, players: List[Player]) -> bool:
        """Elect a mayor among the players"""
        voteResults = {}
        for player in players:
            input_vote = input(f"{player.name}, vote for a mayor: ")
            if input_vote in voteResults:
                voteResults[input_vote] += 1
            else:
                voteResults[input_vote] = 1
            # Add vote action to the log
            self.gameLog[self.round_number - 1].actions.append(Action(
                actor=player,
                action=ActionType.VOTE,
                target=self.getPlayerByName(input_vote)))
        if not voteResults:
            return False

        # Find the player with the most votes
        max_votes = max(voteResults.values())
        candidates = [
            self.getPlayerByName(name)
            for name, votes in voteResults.items()
            if votes == max_votes
        ]

        # If there's a tie, vote again with only the tied candidates
        if len(candidates) > 1:
            self.electMayor(candidates)

        # Elect the mayor
        new_mayor = candidates[0]
        if new_mayor:
            new_mayor.isMayor = True
            return True
        return False

    def save_action(self, actor: Player, action: ActionType, target: Player):
        """Save an action to the game log"""
        self.gameLog[self.round_number - 1].actions.append(Action(
            actor=actor,
            action=action,
            target=target
        ))

    def show_players(self):
        """Display all players and their information"""
        if not self.players:
            click.echo(click.style("❌ No players in the game", fg='red'))
            return

        click.echo(f"\n👥 Players in Game {self.uid}:")
        click.echo("=" * 50)

        for i, player in enumerate(self.players, 1):
            status = "💀  " if not player.alive else "❤️  "
            mayor = "👑  " if player.isMayor else ""
            revealed = "🔍  " if player.isRevealed else ""
            lover = f"💕 {player.lover.name}" if player.lover else ""
            role = player.role.value.replace('_', ' ').title() if player.role else "No Role"

            click.echo(f"{i:2d}. {player.name:<15} {status}{mayor}{revealed}")
            click.echo(f"    Role: {role}")
            if lover:
                click.echo(f"    Lover: {lover}")
            click.echo()

    def select_player(self, author: Player = None, players: Optional[List[Player]] = None, alive: bool = True, isRevealed: Optional[bool] = None, can_select_self: bool = False) -> Player:
        """
        Prompt the user to select one or more players from the list, filtered by given attributes.
        Args:
            players (Optional[List[Player]]): List of players to filter.
            alive (Optional[bool]): Filter by alive status.
            isRevealed (Optional[bool]): Filter by revealed status.
            can_select_self (bool): Allow selecting self.
        Returns:
            Player: Selected player(s) or None.
        """
        if players is None:
            players = self.players

        filtered_players = [
            player for player in players
            if (alive is None or player.alive == alive)
            and (isRevealed is None or player.isRevealed == isRevealed)
            and (can_select_self or player != author)
        ]

        choices = [player.name for player in filtered_players]
        if not choices:
            click.echo("No players available for selection.")
            return None

        questions = [
            inquirer.List(
                'player',
                message="Select a player:",
                choices=choices,
                carousel=True
            ),
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return None
        return [self.getPlayerByName(answers['player'])]

    def show_game_state(self):
        """Display current game state"""
        click.echo(f"\n🎮 Game State: {self.uid}")
        click.echo("=" * 30)
        click.echo(f"Status: {self.status.value}")
        click.echo(f"Period: {self.period.value.replace('_', ' ').title()}")
        click.echo(f"Round: {self.round_number}")
        click.echo(f"Players Alive: {sum(1 for p in self.players if p.alive)}")
        click.echo(f"Players Total: {len(self.players)}")

    def loup_garou_kill(self):
        """Vote to kill a player during the night"""
        target = self.get_target_player()
        target.kill()
        self.game.save_action(self, ActionType.KILL, target)

    def village_vote(self):
        """Vote to kill a player during the day"""
        target = self.get_target_player()
        target.kill()
        self.game.save_action(self, ActionType.VOTE, target)

    def distribute_roles(self):
        """Assign balanced roles to players"""
        if len(self.players) != sum(self.lineup.values()):
            raise ValueError("Number of players must match role distribution")

        # Create list of roles based on counts
        roles_list: List[Role] = []
        for role, count in self.lineup.items():
            roles_list.extend([role] * count)

        # Shuffle roles for random distribution
        shuffle(roles_list)

        for i, player in enumerate(self.players):
            player.role = roles_list[i]


@dataclass
class Sorciere(Player):
    potion_soin_utilisee: bool = False
    potion_poison_utilisee: bool = False

    def heal(self):
        if not self.potion_soin_utilisee:
            self.potion_soin_utilisee = True
            target = self.game.get_target_player(author=self, alive=False, can_select_self=True)
            target.isAlive = True
            self.game.save_action(self, ActionType.HEAL, target)

    def poison(self):
        if not self.potion_poison_utilisee:
            self.potion_poison_utilisee = True
            target = self.game.get_target_player(author=self, alive=True, can_select_self=True)
            target.isAlive = False
            self.game.save_action(self, ActionType.POISON, target)


@dataclass
class Voyante(Player):
    investigations: Dict[str, Role] = field(default_factory=dict)

    def reveal(self):
        """Reveal a player's role during the night"""
        target = self.game.get_target_player(author=self, alive=True)
        if target not in self.investigations:
            self.investigations[target] = target.role
            self.game.save_action(self, ActionType.REVEAL, target)


@dataclass
class Chasseur(Player):
    revenge_target: Player = None

    def choose_revenge_target(self):
        """Choose who to kill when dying"""
        target = self.game.get_target_player(author=self, alive=True)
        if not self.alive and self.revenge_target is None:
            self.revenge_target = target
            target.Kill()
            self.game.save_action(self, ActionType.REVENGE, target)


@dataclass
class Cupidon(Player):
    lovers_chosen: tuple[Player, Player] = field(default_factory=tuple)

    def choose_lovers(self):
        """Choose two players to be lovers"""
        player1 = self.game.get_target_player(author=self, alive=True, can_select_self=True)
        filtered_players = [p for p in self.game.players if p.alive and p != player1]
        player2 = self.game.get_target_player(author=self, players=filtered_players, alive=True, can_select_self=True)
        if not self.lovers_chosen:
            self.lovers_chosen = (player1, player2)
            player1.lover = player2
            player2.lover = player1
            self.game.save_action(self, ActionType.CHOOSE_LOVERS, player1)
            self.game.save_action(self, ActionType.CHOOSE_LOVERS, player2)


@dataclass
class Voleur(Player):
    role_stolen: bool = False
    original_role: Optional[Role] = None

    def steal_role(self):
        """Steal a role at the beginning of the game"""
        target = self.game.get_target_player(author=self, alive=True)
        if not self.role_stolen:
            self.original_role = target.role
            target.role = self
            self.role = self.original_role
            self.role_stolen = True
            self.game.save_action(self, ActionType.STEAL_ROLE, target)
