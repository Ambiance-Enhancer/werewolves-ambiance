-- Werewolves Ambiance - PostgreSQL init

BEGIN;

-- Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Keep things namespaced
CREATE SCHEMA IF NOT EXISTS werewolves;
SET search_path TO werewolves, public;

-- Enums mirrored from src/backend/core/*.py
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role_enum') THEN
    CREATE TYPE role_enum AS ENUM (
      'villageois',
      'loup_garou',
      'petite_fille',
      'chasseur',
      'sorciere',
      'voyante',
      'cupidon',
      'voleur'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'game_status_enum') THEN
    CREATE TYPE game_status_enum AS ENUM ('initializing', 'waiting', 'in_progress', 'completed');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'period_enum') THEN
    -- "State" values (and a couple phase markers) from src/backend/core/game.py
    CREATE TYPE period_enum AS ENUM (
      'start_up',
      'cupidon',
      'amoureux',
      'voleur',
      'voyante',
      'loup_garou',
      'sorciere',
      'mayor_election',
      'vote',
      'completed'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'action_type_enum') THEN
    CREATE TYPE action_type_enum AS ENUM (
      'vote',
      'kill',
      'heal',
      'poison',
      'reveal',
      'choose_lovers',
      'steal_role',
      'revenge_kill'
    );
  END IF;
END $$;

-- Utility: updated_at trigger
CREATE OR REPLACE FUNCTION werewolves.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

-- Rebuild tables to match the provided diagram (Game / Player / Logs only)
DROP TABLE IF EXISTS werewolves.logs CASCADE;
DROP TABLE IF EXISTS werewolves.actions CASCADE;
DROP TABLE IF EXISTS werewolves.investigations CASCADE;
DROP TABLE IF EXISTS werewolves.players CASCADE;
DROP TABLE IF EXISTS werewolves.game_lineup CASCADE;
DROP TABLE IF EXISTS werewolves.games CASCADE;

-- Game
CREATE TABLE werewolves.games (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_lineup jsonb NOT NULL DEFAULT '{}'::jsonb,
  status game_status_enum NOT NULL DEFAULT 'in_progress',
  period period_enum NOT NULL DEFAULT 'start_up',
  round_number integer NOT NULL DEFAULT 1 CHECK (round_number > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_games_updated_at ON werewolves.games;
CREATE TRIGGER trg_games_updated_at
BEFORE UPDATE ON werewolves.games
FOR EACH ROW
EXECUTE FUNCTION werewolves.set_updated_at();

-- Player
CREATE TABLE werewolves.players (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id uuid NOT NULL REFERENCES werewolves.games(id) ON DELETE CASCADE,
  role role_enum NULL,
  role_properties jsonb NOT NULL DEFAULT '{}'::jsonb,
  is_alive boolean NOT NULL DEFAULT true,
  name text NOT NULL,
  is_revealed boolean NOT NULL DEFAULT false,
  is_mayor boolean NOT NULL DEFAULT false,
  lover_player_id uuid NULL
    REFERENCES werewolves.players(id)
    DEFERRABLE INITIALLY DEFERRED,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_players_game_name UNIQUE (game_id, name),
  CONSTRAINT ck_players_no_self_lover CHECK (lover_player_id IS NULL OR lover_player_id <> id)
);

DROP TRIGGER IF EXISTS trg_players_updated_at ON werewolves.players;
CREATE TRIGGER trg_players_updated_at
BEFORE UPDATE ON werewolves.players
FOR EACH ROW
EXECUTE FUNCTION werewolves.set_updated_at();

CREATE INDEX idx_players_game_id ON werewolves.players(game_id);
CREATE INDEX idx_players_game_alive ON werewolves.players(game_id, is_alive) WHERE is_alive;

-- Logs
CREATE TABLE werewolves.logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id uuid NOT NULL REFERENCES werewolves.games(id) ON DELETE CASCADE,
  round_number integer NOT NULL CHECK (round_number > 0),
  period period_enum NOT NULL,
  action action_type_enum NOT NULL,
  actor_role role_enum NULL,
  target_player_id uuid NOT NULL REFERENCES werewolves.players(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_logs_game_created_at ON werewolves.logs(game_id, created_at);
CREATE INDEX idx_logs_game_round_period ON werewolves.logs(game_id, round_number, period);
CREATE INDEX idx_logs_target_player ON werewolves.logs(target_player_id);

COMMIT;
