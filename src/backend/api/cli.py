#!/usr/bin/env python3
"""
CLI tool for testing Werewolves game models
"""
import click
import inquirer
import sys
import os
from typing import List, Optional

from core.models import Game, GameStatus, State, Role, Sorciere, Voyante, LoupGarou, Chasseur, Cupidon, Voleur
from core.role_distributor import RoleDistributor
import uuid

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)


class WerewolvesCLI:
    def __init__(self):
        self.game: Optional[Game] = None
        self.distributor = RoleDistributor()

    def create_game(self, player_names: List[str], interactive: bool = True) -> bool:
        """Create a new game with given players"""
        try:
            num_players = len(player_names)
            if num_players < 4:
                click.echo(click.style("❌ Error: Minimum 4 players required", fg='red'))
                return False

            # Distribute roles with GM selection
            players = self.distributor.distribute_roles(player_names, num_players, interactive)

            # Create game
            game_id = str(uuid.uuid4())[:8]
            self.game = Game(
                uid=game_id,
                status=GameStatus.WAITING,
                period=State.START_UP,
                players=players
            )

            click.echo(click.style(f"🎮 Game created with ID: {game_id}", fg='green'))
            click.echo(f"👥 Players: {num_players}")

            # Show final role distribution
            role_counts = {}
            for player in players:
                role_name = player.role.value
                role_counts[role_name] = role_counts.get(role_name, 0) + 1

            click.echo("\n📊 Final Role Distribution:")
            for role, count in role_counts.items():
                click.echo(f"  {role.replace('_', ' ').title()}: {count}")

            return True

        except Exception as e:
            click.echo(click.style(f"❌ Error creating game: {e}", fg='red'))
            return False

    def show_players(self):
        """Display all players and their information"""
        if not self.game:
            click.echo(click.style("❌ No game active. Create a game first.", fg='red'))
            return

        click.echo(f"\n👥 Players in Game {self.game.uid}:")
        click.echo("=" * 50)

        for i, player in enumerate(self.game.players, 1):
            status = "💀" if not player.alive else "❤️"
            mayor = "👑" if player.isMayor else ""
            revealed = "🔍" if player.isRevealed else ""
            lover = f"💕 {player.lover.name}" if player.lover else ""

            click.echo(f"{i:2d}. {player.name:<15} {status} {mayor} {revealed}")
            click.echo(f"     Role: {player.role.value.replace('_', ' ').title()}")
            if lover:
                click.echo(f"     Lover: {lover}")
            click.echo()

    def show_game_state(self):
        """Display current game state"""
        if not self.game:
            click.echo(click.style("❌ No game active. Create a game first.", fg='red'))
            return

        click.echo(f"\n🎮 Game State: {self.game.uid}")
        click.echo("=" * 30)
        click.echo(f"Status: {self.game.status.value}")
        click.echo(f"Period: {self.game.period.value.replace('_', ' ').title()}")
        click.echo(f"Round: {self.game.round_number}")
        click.echo(f"Players Alive: {sum(1 for p in self.game.players if p.alive)}")
        click.echo(f"Players Total: {len(self.game.players)}")

    def elect_mayor(self):
        """Simulate mayor election using inquirer"""
        if not self.game:
            click.echo(click.style("❌ No game active. Create a game first.", fg='red'))
            return

        alive_players = [p for p in self.game.players if p.alive]
        if not alive_players:
            click.echo(click.style("❌ No players alive!", fg='red'))
            return

        click.echo(click.style("\n👑 Mayor Election", fg='yellow', bold=True))

        try:
            questions = [
                inquirer.List(
                    'mayor',
                    message="Select the new mayor",
                    choices=[f"{player.name} ({player.role.value.replace('_', ' ').title()})" for player in alive_players],
                    carousel=True
                ),
            ]

            answers = inquirer.prompt(questions)
            if answers:
                # Extract player name from the choice
                selected_name = answers['mayor'].split(' (')[0]
                selected_player = next(p for p in alive_players if p.name == selected_name)
                selected_player.isMayor = True
                click.echo(click.style(f"👑 {selected_player.name} is now the mayor!", fg='green'))
        except KeyboardInterrupt:
            click.echo(click.style("\n❌ Mayor election cancelled", fg='yellow'))

    def test_role_abilities(self):
        """Test role-specific abilities using inquirer"""
        if not self.game:
            click.echo(click.style("❌ No game active. Create a game first.", fg='red'))
            return

        # Find players with special abilities
        special_players = []
        for player in self.game.players:
            if isinstance(player, (Sorciere, Voyante, LoupGarou, Chasseur, Cupidon, Voleur)):
                role_type = type(player).__name__
                special_players.append((player, role_type))

        if not special_players:
            click.echo(click.style("❌ No players with special abilities found", fg='red'))
            return

        click.echo(click.style("\n🔮 Role Ability Testing", fg='cyan', bold=True))

        try:
            questions = [
                inquirer.List(
                    'player',
                    message="Select player to test abilities",
                    choices=[f"{player.name} ({role_type})" for player, role_type in special_players],
                    carousel=True
                ),
            ]

            answers = inquirer.prompt(questions)
            if answers:
                selected_name = answers['player'].split(' (')[0]
                selected_player = next(p for p, _ in special_players if p.name == selected_name)
                self._test_specific_role_abilities(selected_player)
        except KeyboardInterrupt:
            click.echo(click.style("\n❌ Role testing cancelled", fg='yellow'))

    def _test_specific_role_abilities(self, player):
        """Test abilities for a specific player using inquirer"""
        click.echo(f"\n🔮 Testing abilities for {click.style(player.name, fg='cyan')}")

        if isinstance(player, Sorciere):
            click.echo("🧙‍♀️ Sorciere Abilities:")
            click.echo(f"  Can heal: {not player.potion_soin_utilisee}")
            click.echo(f"  Can poison: {not player.potion_poison_utilisee}")

            abilities = []
            if not player.potion_soin_utilisee:
                abilities.append("Use Healing Potion")
            if not player.potion_poison_utilisee:
                abilities.append("Use Poison Potion")
            abilities.append("Back")

            if len(abilities) > 1:
                questions = [
                    inquirer.List(
                        'ability',
                        message="Select ability to test",
                        choices=abilities,
                        carousel=True
                    ),
                ]

                try:
                    answers = inquirer.prompt(questions)
                    if answers and answers['ability'] != "Back":
                        if answers['ability'] == "Use Healing Potion":
                            result = player.heal("test_target")
                            click.echo(click.style(f"  ✅ Healing potion used: {result}", fg='green'))
                        elif answers['ability'] == "Use Poison Potion":
                            result = player.poison("test_target")
                            click.echo(click.style(f"  ☠️ Poison potion used: {result}", fg='red'))
                except KeyboardInterrupt:
                    pass

        elif isinstance(player, Voyante):
            click.echo("🔮 Voyante Abilities:")
            click.echo(f"  Investigations made: {len(player.investigations)}")

            other_players = [p for p in self.game.players if p != player and p.alive]
            if other_players:
                questions = [
                    inquirer.List(
                        'target',
                        message="Select player to investigate",
                        choices=[p.name for p in other_players] + ["Back"],
                        carousel=True
                    ),
                ]

                try:
                    answers = inquirer.prompt(questions)
                    if answers and answers['target'] != "Back":
                        target = next(p for p in other_players if p.name == answers['target'])
                        result = player.reveal(target)
                        if result:
                            click.echo(click.style(f"  🔍 Investigated {target.name}: {target.role.value}", fg='blue'))
                        else:
                            click.echo(click.style(f"  ❌ Already investigated {target.name}", fg='yellow'))
                except KeyboardInterrupt:
                    pass

        elif isinstance(player, LoupGarou):
            click.echo("🐺 Loup Garou Abilities:")
            click.echo(f"  Current vote: {player.vote.name if player.vote else 'None'}")

            villagers = [p for p in self.game.players if p.role != Role.LOUP_GAROU and p.alive]
            if villagers:
                questions = [
                    inquirer.List(
                        'target',
                        message="Select target for night kill vote",
                        choices=[p.name for p in villagers] + ["Back"],
                        carousel=True
                    ),
                ]

                try:
                    answers = inquirer.prompt(questions)
                    if answers and answers['target'] != "Back":
                        target = next(p for p in villagers if p.name == answers['target'])
                        result = player.vote_kill(target)
                        click.echo(click.style(f"  🗳️ Voted to kill {target.name}: {result}", fg='red'))
                except KeyboardInterrupt:
                    pass

        elif isinstance(player, Chasseur):
            click.echo("🏹 Chasseur Abilities:")
            click.echo(f"  Current vote: {player.vote.name if player.vote else 'None'}")

            villagers = [p for p in self.game.players if p.role != Role.LOUP_GAROU and p.alive]
            if villagers:
                questions = [
                    inquirer.List(
                        'target',
                        message="Select target for night kill vote",
                        choices=[p.name for p in villagers] + ["Back"],
                        carousel=True
                    ),
                ]

                try:
                    answers = inquirer.prompt(questions)
                    if answers and answers['target'] != "Back":
                        target = next(p for p in villagers if p.name == answers['target'])
                        result = player.vote_kill(target)
                        click.echo(click.style(f"  🗳️ Voted to kill {target.name}: {result}", fg='red'))
                except KeyboardInterrupt:
                    pass

        elif isinstance(player, Cupidon):
            click.echo("💘 Cupidon Abilities:")

            villagers = [p for p in self.game.players if p.alive]
            if len(villagers) >= 2:
                questions = [
                    inquirer.List(
                        'lover1',
                        message="Select first lover",
                        choices=[p.name for p in villagers],
                        carousel=True
                    ),
                ]
                answers1 = inquirer.prompt(questions)
                if not answers1 or answers1['lover1'] == "Back":
                    return

                remaining_villagers = [p for p in villagers if p.name != answers1['lover1']]
                questions = [
                    inquirer.List(
                        'lover2',
                        message="Select second lover",
                        choices=[p.name for p in remaining_villagers],
                        carousel=True
                    ),
                ]
                answers2 = inquirer.prompt(questions)
                if not answers2 or answers2['lover2'] == "Back":
                    return

                player1 = next(p for p in villagers if p.name == answers1['lover1'])
                player2 = next(p for p in villagers if p.name == answers2['lover2'])

                result = player.choose_lovers(player1, player2)
                click.echo(click.style(f"  💞 Connected {player1.name} and {player2.name} as lovers", fg='magenta'))
            else:
                click.echo(click.style("❌ Not enough alive players to select lovers.", fg='red'))

    def simulate_lover_death(self):
        """Test lover death cascade with user selection using inquirer"""
        if not self.game:
            click.echo(click.style("❌ No game active. Create a game first.", fg='red'))
            return

        alive_players = [p for p in self.game.players if p.alive]
        if len(alive_players) < 2:
            click.echo(click.style("❌ Need at least 2 alive players for lover test", fg='red'))
            return

        click.echo(click.style("\n💕 Lover Death Simulation", fg='magenta', bold=True))

        try:
            # Select first lover
            questions = [
                inquirer.List(
                    'player1',
                    message="Select first lover",
                    choices=[p.name for p in alive_players],
                    carousel=True
                ),
            ]

            answers = inquirer.prompt(questions)
            if not answers:
                return

            player1 = next(p for p in alive_players if p.name == answers['player1'])
            remaining_players = [p for p in alive_players if p != player1]

            # Select second lover
            questions = [
                inquirer.List(
                    'player2',
                    message="Select second lover",
                    choices=[p.name for p in remaining_players],
                    carousel=True
                ),
            ]

            answers = inquirer.prompt(questions)
            if not answers:
                return

            player2 = next(p for p in remaining_players if p.name == answers['player2'])

            # Set as lovers
            player1.lover = player2
            player2.lover = player1

            click.echo(f"\n💕 {player1.name} and {player2.name} are now lovers")
            click.echo(f"Before: {player1.name} alive: {player1.alive}, {player2.name} alive: {player2.alive}")

            # Ask which lover to kill
            questions = [
                inquirer.List(
                    'victim',
                    message="Which lover should die first?",
                    choices=[player1.name, player2.name],
                    carousel=True
                ),
            ]

            answers = inquirer.prompt(questions)
            if answers:
                victim = player1 if answers['victim'] == player1.name else player2
                victim.Kill()
                click.echo(click.style(f"After killing {victim.name}: {player1.name} alive: {player1.alive}, {player2.name} alive: {player2.alive}", fg='red'))

        except KeyboardInterrupt:
            click.echo(click.style("\n❌ Lover death simulation cancelled", fg='yellow'))

    def show_role_distribution_rules(self):
        """Show role distribution for different player counts"""
        click.echo(click.style("\n📊 Role Distribution Rules:", fg='cyan', bold=True))
        click.echo("=" * 60)

        for num_players in sorted(self.distributor.ROLE_DISTRIBUTIONS.keys()):
            variants = self.distributor.ROLE_DISTRIBUTIONS[num_players]
            click.echo(f"\n{click.style(f'{num_players} players:', fg='yellow')} ({len(variants)} variant{'s' if len(variants) > 1 else ''})")

            for i, variant in enumerate(variants):
                balance = self.distributor._calculate_balance_score(variant)
                click.echo(f"  Variant {i+1} ({balance}):")
                for role, count in variant.items():
                    role_name = role.value.replace('_', ' ').title()
                    click.echo(f"    {role_name}: {count}")


# Global CLI instance
cli_instance = WerewolvesCLI()


@click.group(invoke_without_command=True)
@click.option('--players', '-p', multiple=True, help='Player names for quick game creation')
@click.pass_context
def cli(ctx, players):
    """🐺 Werewolves Game CLI Tool"""
    if ctx.invoked_subcommand is None:
        if players:
            # Quick mode: create game directly
            if cli_instance.create_game(list(players), interactive=False):
                cli_instance.show_players()
                cli_instance.show_game_state()
        else:
            # Interactive mode
            interactive_menu()


@cli.command()
@click.argument('player_names', nargs=-1, required=True)
def create(player_names):
    """Create a new game with specified players"""
    if cli_instance.create_game(list(player_names), interactive=False):
        cli_instance.show_players()


@cli.command()
def players():
    """Show all players in the current game"""
    cli_instance.show_players()


@cli.command()
def state():
    """Show current game state"""
    cli_instance.show_game_state()


@cli.command()
def mayor():
    """Elect a mayor"""
    cli_instance.elect_mayor()


@cli.command()
def abilities():
    """Test role-specific abilities"""
    cli_instance.test_role_abilities()


@cli.command()
def lovers():
    """Simulate lover death cascade"""
    cli_instance.simulate_lover_death()


@cli.command()
def rules():
    """Show role distribution rules"""
    cli_instance.show_role_distribution_rules()


@cli.command()
@click.argument('num_players', type=click.IntRange(4, 12))
def variants(num_players):
    """Show all role distribution variants for a specific number of players"""
    cli_instance.distributor.show_all_variants(num_players)


@cli.command()
def interactive():
    """Start interactive mode"""
    interactive_menu()


def interactive_menu():
    """Interactive menu using inquirer"""
    while True:
        click.echo("\n" + "="*50)
        click.echo(click.style("🐺 WEREWOLVES GAME CLI TOOL", fg='green', bold=True))
        click.echo("="*50)

        if cli_instance.game:
            click.echo(f"Current Game: {click.style(cli_instance.game.uid, fg='cyan')} | Round: {cli_instance.game.round_number}")
        else:
            click.echo(click.style("No active game", fg='yellow'))

        menu_choices = [
            ("Create new game", "create-game"),
            ("Show players", "show-players"),
            ("Show game state", "show-state"),
            ("Elect mayor", "elect-mayor"),
            ("Test role abilities", "test-abilities"),
            ("Test lover death", "test-lovers"),
            ("Show role distribution rules", "show-rules"),
            ("Exit", "exit")
        ]

        try:
            questions = [
                inquirer.List(
                    'action',
                    message="What would you like to do?",
                    choices=[f"{desc} ({key})" for desc, key in menu_choices],
                    carousel=True
                ),
            ]

            answers = inquirer.prompt(questions)
            if not answers:
                break

            # Extract action key from choice
            action_key = answers['action'].split('(')[-1].rstrip(')')

            if action_key == "exit":
                click.echo(click.style("👋 Goodbye!", fg='green'))
                break
            elif action_key == "create-game":
                create_game_interactive()
            elif action_key == "show-players":
                cli_instance.show_players()
            elif action_key == "show-state":
                cli_instance.show_game_state()
            elif action_key == "elect-mayor":
                cli_instance.elect_mayor()
            elif action_key == "test-abilities":
                cli_instance.test_role_abilities()
            elif action_key == "test-lovers":
                cli_instance.simulate_lover_death()
            elif action_key == "show-rules":
                cli_instance.show_role_distribution_rules()

        except KeyboardInterrupt:
            click.echo(click.style("\n👋 Goodbye!", fg='green'))
            break
        except Exception as e:
            click.echo(click.style(f"❌ Error: {e}", fg='red'))


def create_game_interactive():
    """Interactive game creation using inquirer"""
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

        # Get player names
        player_names = []
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
            player_names.append(name)

        # Create game with interactive role selection
        cli_instance.create_game(player_names, interactive=True)

    except KeyboardInterrupt:
        click.echo(click.style("\n❌ Game creation cancelled", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg='red'))


if __name__ == "__main__":
    cli()
