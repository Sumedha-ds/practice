"""Database utility functions."""
from __future__ import annotations

from sqlalchemy.engine import Engine


def ensure_jobs_table_schema(engine: Engine) -> None:
    """Ensure the `jobs` table has required columns for job postings."""
    # Only applicable for SQLite; silently return if execution fails.
    with engine.connect() as connection:
        result = connection.exec_driver_sql("PRAGMA table_info(jobs);")
        existing_columns = {row[1] for row in result}  # type: ignore[index]

        if not existing_columns:
            # Table does not exist yet; nothing to alter.
            return

        if "jobUuid" not in existing_columns:
            connection.exec_driver_sql("ALTER TABLE jobs ADD COLUMN jobUuid VARCHAR(36);")

        if "audioFilePath" not in existing_columns:
            connection.exec_driver_sql("ALTER TABLE jobs ADD COLUMN audioFilePath VARCHAR(255);")

        connection.commit()

