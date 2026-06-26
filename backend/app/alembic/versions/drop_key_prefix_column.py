"""Drop key_prefix column from api_keys table

Revision ID: drop_key_prefix_001
Revises: add_key_prefix_001
Create Date: 2026-06-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'drop_key_prefix_001'
down_revision: Union[str, Sequence[str], None] = 'add_key_prefix_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f('ix_api_keys_key_prefix'), table_name='api_keys')
    op.drop_column('api_keys', 'key_prefix')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('api_keys', sa.Column('key_prefix', sa.String(length=20), nullable=False, server_default=''))
    op.create_index(op.f('ix_api_keys_key_prefix'), 'api_keys', ['key_prefix'])
