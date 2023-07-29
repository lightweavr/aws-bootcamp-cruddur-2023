from lib.db import db


class AddBioColumnMigration:
    @staticmethod
    def migrate_sql() -> str:
        data = """
    ALTER TABLE public.users ADD COLUMN bio text;
    """
        return data

    @staticmethod
    def rollback_sql() -> str:
        data = """
    ALTER TABLE public.users DROP COLUMN bio;
    """
        return data

    @staticmethod
    def migrate() -> None:
        db.query_commit(AddBioColumnMigration.migrate_sql(), {})

    @staticmethod
    def rollback() -> None:
        db.query_commit(AddBioColumnMigration.rollback_sql(), {})


migration = AddBioColumnMigration
