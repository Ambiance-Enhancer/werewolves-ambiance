import click
from ..core.game import Game
from ..core.roles import Cupidon, Voyante, Sorciere, Voleur


def first_night_process(game: Game) -> None:
    """Process the first night steps"""
    click.echo("\n\n🌙 First night")
    click.echo("="*50)
    cupidon = game.get_role_instance(Cupidon)
    if cupidon is None:
        click.echo("No Cupidon in the game.")
    else:
        click.echo("Cupidon is choosing lovers...")
        cupidon.choose_lovers(game)
    voyante = game.get_role_instance(Voyante)
    if voyante is None:
        click.echo("No Voyante in the game.")
    else:
        click.echo("Voyante is choosing a player to see...")
        voyante.choose_player_to_see(game)

    click.echo("LoupGarou is choosing a player to eliminate...")
    game.loup_garou_kill()

    sorciere = game.get_role_instance(Sorciere)
    if sorciere is None:
        click.echo("No Sorciere in the game.")
    else:
        click.echo("Sorciere is choosing a player to save or kill...")
        sorciere.choose_player_to_save_or_kill(game)

    voleur = game.get_role_instance(Voleur)
    if voleur is None:
        click.echo("No Voleur in the game.")
    else:
        click.echo("Voleur is choosing a player to steal their role...")
        voleur.choose_player_to_steal(game)

    # Kill doomed lovers at the end of the night
    game.kill_doomed_lovers()

    return
