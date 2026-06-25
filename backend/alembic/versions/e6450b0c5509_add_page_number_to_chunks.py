"""add page number to chunks

Revision ID: e6450b0c5509
Revises: eb20f7d5651a
Create Date: 2026-06-25 18:42:41.136235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6450b0c5509'
down_revision: Union[str, Sequence[str], None] = 'eb20f7d5651a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE chunks
        ADD COLUMN IF NOT EXISTS page_number INTEGER
    """)


def downgrade() -> None:
    op.drop_column("chunks", "page_number")
