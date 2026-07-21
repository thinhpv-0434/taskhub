"""Configuration for database and other settings."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Using SQLite async for local development. Change to asyncpg for Postgres.
DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR / 'taskhub.db'}"
