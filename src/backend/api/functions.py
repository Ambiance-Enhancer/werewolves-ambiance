import click
from typing import List, Type
from ..core.game import Game
from ..core.roles import Cupidon, Voyante, Sorciere, Voleur, Chasseur
from ..core.roles_order import get_roles_order_for_game


def first_night_process(game: Game) -> None:
    """Process the first night steps"""
    click.echo("\n\n🌙 First night")
    click.echo("=" * 50)
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
    return


def get_night_roles_order(game: Game) -> List[Type]:
    """
    Retourne l'ordre des rôles à appeler dans la nuit en fonction des rôles présents dans la partie.
    Utilise la logique définie dans core.roles_order.
    """
    return get_roles_order_for_game(game)


def process_night(game: Game) -> None:
    """Process the night steps based on present roles"""
    click.echo("\n\n🌙 Night Phase")
    click.echo("=" * 50)

    # Reset recently killed for this night
    game.recently_killed = []

    roles_order = get_night_roles_order(game)
    wolves_acted = False

    for role_class in roles_order:
        # Process Wolves (between Voyante and Sorciere, or if Sorciere is next)
        # We ensure Wolves act before Sorciere
        if role_class == Sorciere and not wolves_acted:
            click.echo("LoupGarou is choosing a player to eliminate...")
            game.loup_garou_kill()
            wolves_acted = True

        instance = game.get_role_instance(role_class)
        if not instance:
            continue

        if role_class == Cupidon:
            if not instance.lovers_chosen:
                click.echo("Cupidon is choosing lovers...")
                instance.choose_lovers(game)

        elif role_class == Voleur:
            if not instance.role_stolen and hasattr(instance, "choose_player_to_steal"):
                click.echo("Voleur is choosing a player to steal their role...")
                instance.choose_player_to_steal(game)

        elif role_class == Voyante:
            click.echo("Voyante is choosing a player to see...")
            instance.choose_player_to_see(game)

        elif role_class == Sorciere:
            click.echo("Sorciere is choosing a player to save or kill...")
            instance.choose_player_to_save_or_kill(game)

    # If wolves haven't acted yet (e.g. no Sorciere present), they act now
    if not wolves_acted:
        click.echo("LoupGarou is choosing a player to eliminate...")
        game.loup_garou_kill()

    click.echo("Night phase ended.")


def process_day(game: Game) -> None:
    """Process the day steps: Hunter revenge, Mayor checks (election/succession) and Village Vote."""
    click.echo("\n\n☀️ Day Phase")
    click.echo("=" * 50)

    # 0. Check for dead Hunter (Chasseur) who hasn't retaliated yet
    chasseur = game.get_role_instance(Chasseur)
    if chasseur and not chasseur.alive and chasseur.revenge_target is None:
        click.echo(f"\n🔫 The Hunter {chasseur.name} has died!")
        click.echo("They must choose a target to take with them!")

        # Determine valid targets (all alive players)
        # Note: target.kill() is called inside choose_revenge_target
        target = game.select_player(author=chasseur, alive=True, can_select_self=False)

        if target:
            chasseur.choose_revenge_target(target)
            click.echo(
                f"💥 {chasseur.name} shoots {target.name} with their dying breath!"
            )
        else:
            click.echo(f"{chasseur.name} died without shooting anyone.")

    # 1. Check for dead Mayor and handle succession
    current_mayor = next((p for p in game.players if p.is_mayor), None)

    if current_mayor and not current_mayor.alive:
        click.echo(f"⚠️ The Mayor {current_mayor.name} has died!")
        click.echo("They must nominate a successor.")

        # Dead mayor chooses successor among alive players
        alive_players = [p for p in game.players if p.alive]
        successor = game.select_player(
            author=current_mayor,
            players=alive_players,
            alive=True,
            can_select_self=False,
        )

        if successor:
            current_mayor.is_mayor = False
            successor.is_mayor = True
            click.echo(
                f"👑 {current_mayor.name} has appointed {successor.name} as the new Mayor."
            )
            current_mayor = successor
        else:
            click.echo(
                "No successor selected. The Village remains without a Mayor for now (or a new election will occur)."
            )
            current_mayor.is_mayor = False
            current_mayor = None

    # 2. If no Mayor exists (start of game or failed succession), hold an election
    if current_mayor is None:
        click.echo("📢 No Mayor currently. Holding an election!")
        alive_players = [p for p in game.players if p.alive]
        if game.elect_mayor(alive_players):
            current_mayor = next((p for p in game.players if p.is_mayor), None)
            if current_mayor:
                click.echo(f"👑 New Mayor elected: {current_mayor.name}")
        else:
            click.echo("❌ Election failed (tie or no votes).")

    # 3. Village Vote
    click.echo("\n🗳️ Village Vote")
    eliminated = game.village_vote_input()

    # 4. Check if the eliminated player was the mayor - immediate succession
    if eliminated and eliminated.is_mayor:
        click.echo(f"\n⚠️ The Mayor {eliminated.name} has been eliminated!")
        click.echo("They must nominate a successor immediately.")
        alive_players = [p for p in game.players if p.alive]
        if alive_players:
            successor = game.select_player(
                author=eliminated,
                players=alive_players,
                alive=True,
                can_select_self=False,
            )
            if successor:
                eliminated.is_mayor = False
                successor.is_mayor = True
                click.echo(
                    f"👑 {eliminated.name} has appointed {successor.name} as the new Mayor."
                )
            else:
                click.echo(
                    "No successor selected. The Village remains without a Mayor."
                )
                eliminated.is_mayor = False
