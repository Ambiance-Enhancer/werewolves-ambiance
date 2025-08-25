from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

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
    INVESTIGATE = "investigate"
    CHOOSE_LOVERS = "choose_lovers"
    STEAL_ROLE = "steal_role"
    REVEGE_KILL = "revenge_kill"

@dataclass
class Player:
    name: str
    role: Role
    alive: bool = True
    isRevealed: bool = False
    isMayor: bool = False
    lover: Optional['Player'] = None # Self-reference for lover relationship
    
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
    roles_alive: Dict[str, int] = field(default_factory=dict)
    gameLog: List[Log] = field(default_factory=list)
    
    def electMayor(self,players: List[Player]) -> bool:
        """Elect a mayor among the players"""
        voteResults = {}
        for player in players:
            input_vote = input(f"{player.name}, vote for a mayor: ")
            if input_vote in voteResults:
                voteResults[input_vote] += 1
            else:
                voteResults[input_vote] = 1
            # Add vote action to the log
            self.gameLog[self.round_number - 1].actions.append(Action(actor=player, action=ActionType.VOTE, target=self.getPlayerByName(input_vote)))
        if not voteResults:
            return False

        # Find the player with the most votes
        max_votes = max(voteResults.values())
        candidates = [self.getPlayerByName(name) for name, votes in voteResults.items() if votes == max_votes]

        # If there's a tie, vote again with only the tied candidates
        if len(candidates) > 1:
            self.electMayor(candidates)

        # Elect the mayor
        new_mayor = candidates[0]
        if new_mayor:
            new_mayor.isMayor = True
            return True
        
        return False

    def getPlayerByName(self, name: str) -> Optional[Player]:
        for player in self.players:
            if player.name == name:
                return player
        return None

@dataclass
class Sorciere(Player):
    potion_soin_utilisee: bool = False
    potion_poison_utilisee: bool = False

    def heal(self, target: str) -> bool:
        if not self.potion_soin_utilisee:
            self.potion_soin_utilisee = True
            return True
        return False

    def poison(self, target: str) -> bool:
        if not self.potion_poison_utilisee:
            self.potion_poison_utilisee = True
            return True
        return False

@dataclass
class Voyante(Player):
    investigations: Dict[str, Role] = field(default_factory=dict)

    def reveal(self, target: Player) -> bool:
        """Reveal a player's role during the night"""
        if target not in self.investigations:
            self.investigations[target] = target.role
            return True
        return False

@dataclass
class LoupGarou(Player):
    vote: Player = None

    def vote_kill(self, target: Player) -> bool:
        """Vote to kill a player during the night"""
        self.vote = target  # Reuse the vote field for night kills
        return True

@dataclass
class Chasseur(Player):
    revenge_target: Player = None

    def choose_revenge_target(self, target: Player) -> bool:
        """Choose who to kill when dying"""
        if not self.alive and self.revenge_target is None:
            self.revenge_target = target
            target.Kill()
            return True
        return False

@dataclass
class Cupidon(Player):
    lovers_chosen: tuple[Player, Player] = field(default_factory=tuple)

    def choose_lovers(self, player1: Player, player2: Player) -> bool:
        """Choose two players to be lovers"""
        if not self.lovers_chosen:
            self.lovers_chosen = (player1, player2)
            player1.isInLove = True
            player2.isInLove = True
            return True
        return False

@dataclass
class Voleur(Player):
    role_stolen: bool = False
    original_role: Optional[str] = None

    def steal_role(self, target: Player) -> bool:
        """Steal a role at the beginning of the game"""
        if not self.role_stolen:
            self.original_role = self.role
            self.role = target.role
            target.role = self.original_role
            self.role_stolen = True
            return True
        return False

