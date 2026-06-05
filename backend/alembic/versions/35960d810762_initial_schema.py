"""initial_schema

Revision ID: 35960d810762
Revises: 
Create Date: 2026-05-19 13:01:29.244769

"""
from typing import Sequence, Union

from alembic import op

from app import models  # noqa: F401
from app.core.database import Base


# revision identifiers, used by Alembic.
revision: str = '35960d810762'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Downgrade schema."""

    Base.metadata.drop_all(bind=op.get_bind())
