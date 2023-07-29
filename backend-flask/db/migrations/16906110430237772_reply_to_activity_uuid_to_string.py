from lib.db import db


class ReplyToActivityUuidToStringMigration:
    @staticmethod
    def migrate_sql() -> str:
        data = """
    ALTER TABLE activities DROP COLUMN reply_to_activity_uuid;
    ALTER TABLE activities ADD COLUMN reply_to_activity_uuid uuid;
    """
        return data

    @staticmethod
    def rollback_sql() -> str:
        data = """
    ALTER TABLE activities DROP COLUMN reply_to_activity_uuid;
    ALTER TABLE activities ADD COLUMN reply_to_activity_uuid integer;
    """
        return data

    @staticmethod
    def migrate() -> None:
        db.query_commit(ReplyToActivityUuidToStringMigration.migrate_sql(), {})

    @staticmethod
    def rollback() -> None:
        db.query_commit(ReplyToActivityUuidToStringMigration.rollback_sql(), {})


migration = ReplyToActivityUuidToStringMigration
