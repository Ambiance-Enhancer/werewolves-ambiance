Brief overview — test files and main tests

- `test_game.py`: Tests core game behavior.
  - Main tests: `test_player_kill_also_kills_lover()`, `test_get_player_by_name_and_manual_players_list()`, `test_distribute_roles_simple_assignment()`.

- `test_roles.py`: Tests role-specific behaviors.
  - Main tests: `test_sorciere_heal_and_poison()`, `test_voyante_investigation_with_stub_game()`, `test_cupidon_sets_lovers_with_stub_game()`, `test_voleur_steal_role_swaps_roles()`, `test_chasseur_revenge_target()`.

Note: tests rely on `tests/conftest.py` to make the project's `src` package importable during test runs.
