from src.backend.core.roles import Sorciere, Voyante, Chasseur, Cupidon, Voleur
from src.backend.core.game import Player
from src.backend.core.role_distributor import Role


def test_sorciere_heal_and_poison():
    witch = Sorciere(name="Witch")
    sick = Player(name="Sick")
    sick.alive = False

    witch.heal(sick)
    assert sick.alive is True
    assert witch.potion_soin_utilisee is True

    victim = Player(name="Victim")
    witch2 = Sorciere(name="W2")
    witch2.poison(victim)
    assert victim.alive is False
    assert witch2.potion_poison_utilisee is True


def test_voyante_investigation_with_stub_game():
    seer = Voyante(name="Seer")
    target = Player(name="T")
    target.role = Role.VILLAGEOIS

    class StubGame:
        def select_player(self, author=None, **kwargs):
            return target

    seer.choose_player_to_see(StubGame())
    assert 'T' in seer.investigations
    assert seer.investigations['T'] == Role.VILLAGEOIS


def test_cupidon_sets_lovers_with_stub_game():
    cupid = Cupidon(name="Cupid")
    p1 = Player(name="A")
    p2 = Player(name="B")

    class StubGame:
        def __init__(self):
            self.players = [p1, p2]

        def select_player(self, author=None, players=None, **kwargs):
            if players is None:
                return p1
            return players[0]

    cupid.choose_lovers(StubGame())
    assert p1.lover is p2
    assert p2.lover is p1


def test_voleur_steal_role_swaps_roles():
    thief = Voleur(name="Thief")
    victim = Player(name="V")
    victim.role = Role.VOYANTE

    thief.steal_role(victim)
    assert thief.role == Role.VOYANTE
    assert victim.role is None


def test_chasseur_revenge_target():
    hunter = Chasseur(name="Hunter")
    target = Player(name="Target")
    hunter.alive = False

    hunter.choose_revenge_target(target)
    assert hunter.revenge_target is target
    assert target.alive is False
