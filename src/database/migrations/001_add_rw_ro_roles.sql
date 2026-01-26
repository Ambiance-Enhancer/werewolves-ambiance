DO $$
DECLARE
    rw_user     text := current_setting('app.rw_user');
    rw_password text := current_setting('app.rw_password');
    ro_user     text := current_setting('app.ro_user');
    ro_password text := current_setting('app.ro_password');
    schema_name text := current_setting('app.postgres_schema');
    db_name     text := current_setting('app.postgres_db');
BEGIN
    -- Roles creation
    EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', rw_user, rw_password);
    EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', ro_user, ro_password);

    -- Grants on database and schema
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO %I, %I', db_name, rw_user, ro_user);
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO %I, %I', schema_name, rw_user, ro_user);

    -- Grants on tables and sequences
    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO %I', schema_name, rw_user);
    EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO %I', schema_name, ro_user);

    -- Default privileges on tables
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I', schema_name, rw_user);
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT ON TABLES TO %I', schema_name, ro_user);

    -- Default privileges on sequences
    EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT USAGE, SELECT ON SEQUENCES TO %I', schema_name, rw_user);
END $$;
