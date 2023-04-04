-- this file was manually created
INSERT INTO
  public.users (display_name, email, handle, cognito_user_id)
VALUES
  (
    'Andrew Brown',
    'test1@test.co',
    'andrewbrown',
    'MOCK'
  ),
  ('Andrew Bayko', 'test2@test.co', 'bayko', 'MOCK');
INSERT INTO
  public.activities (user_uuid, message, expires_at)
VALUES
  (
    (
      SELECT
        uuid
      from
        public.users
      WHERE
        users.handle = 'andrewbrown'
      LIMIT
        1
    ), 'This was imported as seed data!', current_timestamp + interval '10 day'
  ),
  (
    (
      SELECT
        uuid
      from
        public.users
      WHERE
        users.handle = 'bayko'
      LIMIT
        1
    ), 'Another seed import!', current_timestamp + interval '10 day'
  );
