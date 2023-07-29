-- https://www.postgresql.org/docs/current/uuid-ossp.html
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- forcefully drop our tables if they already exist
DROP TABLE IF EXISTS public.users cascade;
DROP TABLE IF EXISTS public.activities;

DROP TABLE IF EXISTS public.schema_information;

CREATE TABLE IF NOT EXISTS public.schema_information (
  id integer UNIQUE,
  last_successful_run text
);
INSERT INTO public.schema_information (id, last_successful_run)
VALUES(1, '0')
ON CONFLICT (id) DO NOTHING;


CREATE TABLE public.users (
  uuid UUID default uuid_generate_v4() primary key,
  display_name text NOT NULL,
  handle text NOT NULL,
  email text NOT NULL,
  cognito_user_id text NOT NULL,
  created_at timestamp default current_timestamp NOT NULL
);
CREATE TABLE public.activities (
  uuid UUID default uuid_generate_v4() primary key,
  user_uuid UUID NOT NULL,
  message text NOT NULL,
  replies_count integer default 0,
  reposts_count integer default 0,
  likes_count integer default 0,
  reply_to_activity_uuid integer,
  expires_at timestamp,
  created_at timestamp default current_timestamp NOT NULL
);

-- Add the postgres_iam user: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.DBAccounts.html#UsingWithRDS.IAMDBAuth.DBAccounts.PostgreSQL
CREATE USER postgres_iam;
GRANT rds_iam TO postgres_iam;
-- DROP TRIGGER IF EXISTS trig_users_updated_at ON users;
-- DROP TRIGGER IF EXISTS trig_activities_updated_at ON activities;
-- DROP FUNCTION IF EXISTS func_updated_at();
-- CREATE FUNCTION func_updated_at() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = now();
-- RETURN NEW;
-- END;
-- $$ language 'plpgsql';
-- CREATE TRIGGER trig_users_updated_at BEFORE
-- UPDATE
--   ON users FOR EACH ROW EXECUTE PROCEDURE func_updated_at();
-- CREATE TRIGGER trig_activities_updated_at BEFORE
-- UPDATE
--   ON activities FOR EACH ROW EXECUTE PROCEDURE func_updated_at();
