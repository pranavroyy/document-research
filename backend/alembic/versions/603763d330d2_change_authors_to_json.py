"""change authors to json

Revision ID: 603763d330d2
Revises: 0407fddcccd3
Create Date: 2026-06-25 23:44:37.702343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '603763d330d2'
down_revision: Union[str, Sequence[str], None] = '0407fddcccd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None




def upgrade() -> None:
    op.alter_column(
        "documents",
        "authors",
        existing_type=sa.Text(),
        type_=postgresql.JSONB(),
        postgresql_using="to_jsonb(authors)",
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "documents",
        "authors",
        existing_type=postgresql.JSONB(),
        type_=sa.Text(),
        postgresql_using="authors::text",
        nullable=True,
    )
