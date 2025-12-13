from src.backend.core.game import Player, Game
from src.backend.core.role_distributor import Role


def test_player_kill_also_kills_lover():
    p1 = Player(name="Alice")
    p2 = Player(name="Bob")
    p1.lover = p2
    p2.lover = p1

    p1.kill()

    assert p1.alive is False
    assert p2.alive is False


def test_get_player_by_name_and_manual_players_list():
    game = Game(0)
    game.players = [Player(name="Ann"), Player(name="Ben")]

    assert game.get_player_by_name("Ann") is game.players[0]
    assert game.get_player_by_name("Nonexistent") is None


def test_distribute_roles_simple_assignment():
    # Create a game with two players and force a lineup of two villageois
    game = Game(0)
    game.players = [Player(name="P1"), Player(name="P2")]
    game.lineup = {Role.VILLAGEOIS: 2}

    # Should not raise; role_class_map maps VILLAGEOIS -> Player
    game.distribute_roles()

    assert len(game.players) == 2
    assert all(hasattr(p, 'role') for p in game.players)
    assert all(p.role == Role.VILLAGEOIS for p in game.players)
