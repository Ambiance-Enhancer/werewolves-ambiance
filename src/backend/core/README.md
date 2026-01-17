Brief overview — main file and main function

- `game.py`: Core game model and flow.
  - Main concept: `Game` class manages players, periods, and logs.
  - Primary interface: `Game(num_players: int)` (constructor) and `Game.distribute_roles() -> None`.

- `roles.py`: Role implementations.
  - Main concept: role classes implementing role-specific behavior.
  - Primary methods: `Sorciere.choose_player_to_save_or_kill(game)`, `Voyante.choose_player_to_see(game)`, `Cupidon.choose_lovers(game)`, `Voleur.steal_role(target)`, `Chasseur.choose_revenge_target(target)`.

- `role_distributor.py`: Role distribution helpers.
  - Main concept: contains `Role` enum and distributions plus a lineup selection helper.
  - Primary function: `set_lineup(num_players: int) -> Dict[Role, int]`.

- `models.py`: Compatibility shim.
  - Main concept: re-exports symbols from `game.py` and `roles.py` for backward compatibility.
