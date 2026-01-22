#!/usr/bin/env python3
"""
CLI to run a Werewolves game
"""
import click
from ..core.game import Game
from .functions import first_night_process, process_night, process_day


@click.group(invoke_without_command=True)
@click.argument('num_players', type=int, required=False, default=-1)
def cli(num_players):
    """🐺 Werewolves Game CLI Tool"""
    click.echo("\n" + "="*50)
    click.echo(click.style("🐺 WEREWOLVES GAME CLI TOOL", fg='green', bold=True))
    click.echo("="*50)
    game = Game(num_players)
    game.show_players()
    first_night_process(game)
    game.show_players()
    
    # Main Game Loop
    while not game.is_over():
        click.echo("\n🗳️ Village Vote (Day Phase)")
        process_day(game)
        game.show_players()
        if game.is_over():
            break

        process_night(game)
        game.round_number += 1
        game.show_game_state()
        game.show_players()


if __name__ == "__main__":
    cli()
