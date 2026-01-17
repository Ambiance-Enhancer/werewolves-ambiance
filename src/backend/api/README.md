Brief overview — main file and main function

- `cli.py`: CLI entrypoint. Main idea: create a `Game` instance and trigger the first-night flow.

- `functions.py`: High-level flow helpers.
	- Main function: `first_night_process(game: Game) -> None` — runs the first-night sequence (cupidon, voyante, wolf kill, sorciere, voleur).

Note: the thief (`Voleur`) helper method name differs between `functions.py` and `roles.py` (one uses a chooser-style method, the other exposes `steal_role`). Update either side when embedding into an API.

