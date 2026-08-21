"""add scrape_cache table

Revision ID: 51a14e9a036d
Revises: aa7c9965a439
Create Date: 2026-08-21 17:13:58.636428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '51a14e9a036d'
down_revision: Union[str, Sequence[str], None] = 'aa7c9965a439'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('scrape_cache',
    sa.Column('url', sa.Text(), nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('url')
    )
    op.add_column('accommodations', sa.Column('scrape_status', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('accommodations', 'scrape_status')
    op.drop_table('scrape_cache')
