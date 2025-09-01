from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import uuid
import click
import inquirer
from backend.core.role_distributor import set_lineup, distribute_roles


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


class Role(Enum):
    VILLAGEOIS = "villageois"
    LOUP_GAROU = "loup_garou"
    PETITE_FILLE = "petite_fille"
    CHASSEUR = "chasseur"
    SORCIERE = "sorciere"
    VOYANTE = "voyante"
    CUPIDON = "cupidon"
    VOLEUR = "voleur"


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
    role: Role
    game: Optional['Game'] = None  # Reference to the game instance
    alive: bool = True
    isRevealed: bool = False
    isMayor: bool = False
    lover: Optional['Player'] = None  # Self-reference for lover relationship

    def Kill(self) -> None:
        self.alive = False
        if self.lover and self.lover.alive:
            self.lover.Kill()


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
    round_number: int = 1
    players: List[Player] = field(default_factory=list)
    lineup: Dict[Role, int] = field(default_factory=dict)
    gameLog: List[Log] = field(default_factory=list)

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

    def __init__(self):
        """Initialize a player by asking the user game parameters"""
        self.uid = str(uuid.uuid4())[:8]

        # Initialize players list
        self.players = []
        try:
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
                    return

                name = answers['name'].strip() or f"Player{i+1}"
                self.players.append(Player(name=name, game=self))

        except KeyboardInterrupt:
            click.echo(click.style("\n❌ Game creation cancelled", fg='yellow'))
        except Exception as e:
            click.echo(click.style(f"❌ Error: {e}", fg='red'))

        # Ask for a lineup selection and assign roles
        self.lineup = set_lineup(len(self.players))
        self.players = distribute_roles(self.lineup, self.players)

    def save_action(self, actor: Player, action: ActionType, target: Player):
        """Save an action to the game log"""
        self.gameLog[self.round_number - 1].actions.append(Action(
            actor=actor,
            action=action,
            target=target
        ))


@dataclass
class Sorciere(Player):
    potion_soin_utilisee: bool = False
    potion_poison_utilisee: bool = False

    def heal(self, target: str):
        if not self.potion_soin_utilisee:
            self.potion_soin_utilisee = True
            target.isAlive = True
            self.game.save_action(self, ActionType.HEAL, target)

    def poison(self, target: str):
        if not self.potion_poison_utilisee:
            self.potion_poison_utilisee = True
            target.isAlive = False
            self.game.save_action(self, ActionType.POISON, target)


@dataclass
class Voyante(Player):
    investigations: Dict[str, Role] = field(default_factory=dict)

    def reveal(self, target: Player):
        """Reveal a player's role during the night"""
        if target not in self.investigations:
            self.investigations[target] = target.role
            self.game.save_action(self, ActionType.REVEAL, target)


@dataclass
class LoupGarou(Player):
    vote: Player = None

    def vote_kill(self, target: Player):
        """Vote to kill a player during the night"""
        self.vote = target  # Reuse the vote field for night kills
        self.game.save_action(self, ActionType.VOTE, target)


@dataclass
class Chasseur(Player):
    revenge_target: Player = None

    def choose_revenge_target(self, target: Player):
        """Choose who to kill when dying"""
        if not self.alive and self.revenge_target is None:
            self.revenge_target = target
            target.Kill()
            self.game.save_action(self, ActionType.REVENGE, target)


@dataclass
class Cupidon(Player):
    lovers_chosen: tuple[Player, Player] = field(default_factory=tuple)

    def choose_lovers(self, player1: Player, player2: Player):
        """Choose two players to be lovers"""
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

    def steal_role(self, target: Player):
        """Steal a role at the beginning of the game"""
        if not self.role_stolen:
            self.original_role = target.role
            target.role = self
            self.role = self.original_role
            self.role_stolen = True
            self.game.save_action(self, ActionType.STEAL_ROLE, target)
