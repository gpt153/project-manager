"""
Database initialization script.

This script creates the database tables using SQLAlchemy models.
For production, use Alembic migrations instead.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import init_db


async def main():
    """Initialize the database."""
    print("Initializing database tables...")
    try:
        await init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
