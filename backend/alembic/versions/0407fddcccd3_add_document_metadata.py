"""add document metadata

Revision ID: 0407fddcccd3
Revises: e6450b0c5509
Create Date: 2026-06-25 18:46:43.010667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0407fddcccd3'
down_revision: Union[str, Sequence[str], None] = 'e6450b0c5509'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS authors TEXT")
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS abstract TEXT")
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS page_count INTEGER")


def downgrade() -> None:
    op.drop_column("documents", "page_count")
    op.drop_column("documents", "abstract")
    op.drop_column("documents", "authors")
