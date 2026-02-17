"""
Seed the database with test data.

Run after `alembic upgrade head`. Requires DATABASE_URL or DEV_DATABASE_URL in .env.

Usage:
    python -m alembic.seed
    # or from repo root:
    python -c "import asyncio; from alembic.seed import run_seed; asyncio.run(run_seed())"
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date
from pathlib import Path

# Ensure app is importable when run as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import (
    Category,
    MonitoredUrl,
    ScheduleConfig,
    State,
)


async def seed(session: AsyncSession) -> None:
    """Insert test data. Idempotent: skips if data already present."""
    # States
    r = await session.execute(select(State).limit(1))
    if r.scalar_one_or_none() is not None:
        print("States already present, skipping seed.")
        return

    ca = State(name="California", abbreviation="CA", is_active=True)
    ny = State(name="New York", abbreviation="NY", is_active=True)
    session.add_all([ca, ny])
    await session.flush()

    # Categories (California)
    cat_forms = Category(
        name="Court Forms",
        description="Official court forms",
        state_id=ca.id,
        full_path="/Court Forms",
        parent_category_id=None,
    )
    session.add(cat_forms)
    await session.flush()

    cat_family = Category(
        name="Family",
        description="Family law forms",
        state_id=ca.id,
        full_path="/Court Forms/Family",
        parent_category_id=cat_forms.id,
    )
    session.add(cat_family)
    await session.flush()

    # Monitored URL (sample)
    url = MonitoredUrl(
        url="https://www.courts.ca.gov/documents/sample-form.pdf",
        title="Sample Court Form",
        form_number="FORM-001",
        revision_date=date(2025, 1, 15),
        state_id=ca.id,
        category_id=cat_family.id,
        is_enabled=True,
        status="active",
    )
    session.add(url)

    # Default schedule config
    schedule = ScheduleConfig(
        cron_expression="0 2 * * *",  # 2 AM daily
        is_enabled=True,
        last_run=None,
        next_run=None,
    )
    session.add(schedule)

    await session.commit()
    print("Seed complete: states (CA, NY), categories (Court Forms, Family), 1 URL, schedule_config.")


async def run_seed() -> None:
    """Create engine and session, run seed."""
    settings = get_settings()
    engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session_factory() as session:
        try:
            await seed(session)
        except Exception as e:
            await session.rollback()
            print(f"Seed failed: {e}", file=sys.stderr)
            raise
    await engine.dispose()


def main() -> None:
    asyncio.run(run_seed())


if __name__ == "__main__":
    main()
