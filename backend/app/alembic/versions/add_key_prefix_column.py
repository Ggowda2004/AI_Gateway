"""Add key_prefix column to api_keys table for indexed lookups

Revision ID: add_key_prefix_001
Revises: 158dbdf95ad7
Create Date: 2026-06-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_key_prefix_001'
down_revision: Union[str, Sequence[str], None] = '158dbdf95ad7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('api_keys', sa.Column('key_prefix', sa.String(length=20), nullable=False, server_default=''))
    op.create_index(op.f('ix_api_keys_key_prefix'), 'api_keys', ['key_prefix'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_api_keys_key_prefix'), table_name='api_keys')
    op.drop_column('api_keys', 'key_prefix')
