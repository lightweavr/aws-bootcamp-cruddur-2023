create = """INSERT INTO public.activities (
  user_uuid,
  message,
  expires_at
)
VALUES (
  (SELECT uuid
    FROM public.users
    WHERE users.cognito_user_id = %(cognito_user_id)s
    LIMIT 1
  ),
  %(message)s,
  %(expires_at)s
) RETURNING uuid;
"""

home = """SELECT
  activities.uuid,
  users.display_name,
  users.handle,
  users.cognito_user_id,
  activities.message,
  activities.replies_count,
  activities.reposts_count,
  activities.likes_count,
  activities.expires_at,
  activities.created_at
FROM public.activities
LEFT JOIN public.users ON users.uuid = activities.user_uuid
ORDER BY activities.created_at DESC
"""

activities_object = """SELECT
  activities.uuid,
  users.display_name,
  users.handle,
  users.cognito_user_id,
  activities.message,
  activities.created_at,
  activities.expires_at,
  activities.reply_to_activity_uuid
FROM public.activities
INNER JOIN public.users ON users.uuid = activities.user_uuid
WHERE
  activities.uuid = %(uuid)s
"""


get_user_activities = """SELECT
  (SELECT COALESCE(row_to_json(object_row),'{}'::json) FROM (
    SELECT
      users.uuid,
      users.cognito_user_id as cognito_user_uuid,
      users.handle,
      users.display_name,
      users.bio,
      (
       SELECT
        count(true)
       FROM public.activities
       WHERE
        activities.user_uuid = users.uuid
       ) as cruds_count
  ) object_row) as profile,
  (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
    SELECT
      activities.uuid,
      users.display_name,
      users.handle,
      users.cognito_user_id,
      activities.message,
      activities.created_at,
      activities.expires_at
    FROM public.activities
    WHERE
      activities.user_uuid = users.uuid
    ORDER BY activities.created_at DESC
    LIMIT 40
  ) array_row) as activities
FROM public.users
WHERE
  users.handle = %(handle)s
"""

update_user_profile = """UPDATE public.users
SET
  bio = %(bio)s,
  display_name= %(display_name)s
WHERE
  users.cognito_user_id = %(cognito_user_id)s
RETURNING handle;
"""

user_short = """SELECT
  users.uuid,
  users.handle,
  users.display_name
  FROM public.users
WHERE
  users.handle = %(handle)s
"""

reply = """INSERT INTO public.activities (
  user_uuid,
  message,
  reply_to_activity_uuid
)
VALUES (
  (SELECT uuid
    FROM public.users
    WHERE users.cognito_user_id = %(cognito_user_id)s
    LIMIT 1
  ),
  %(message)s,
  %(reply_to_activity_uuid)s
) RETURNING uuid;
"""

show = """SELECT
  (SELECT COALESCE(row_to_json(object_row),'{}'::json) FROM (
    SELECT
      activities.uuid,
      users.display_name,
      users.handle,
      activities.message,
      activities.replies_count,
      activities.reposts_count,
      activities.likes_count,
      activities.expires_at,
      activities.created_at
  ) object_row) as activity,
  (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
  SELECT
    replies.uuid,
    reply_users.display_name,
    reply_users.handle,
    replies.message,
    replies.replies_count,
    replies.reposts_count,
    replies.likes_count,
    replies.reply_to_activity_uuid,
    replies.created_at
  FROM public.activities replies
  LEFT JOIN public.users reply_users ON reply_users.uuid = replies.user_uuid
  WHERE
    replies.reply_to_activity_uuid = activities.uuid
  ORDER BY  activities.created_at ASC
  ) array_row) as replies
FROM public.activities
LEFT JOIN public.users ON users.uuid = activities.user_uuid
WHERE activities.uuid = %(uuid)s
ORDER BY activities.created_at DESC
"""
