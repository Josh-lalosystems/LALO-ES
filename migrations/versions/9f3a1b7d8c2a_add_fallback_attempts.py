"""add fallback_attempts to requests

Revision ID: 9f3a1b7d8c2a
Revises: 62de3ab69c1b_add_api_keys_table
Create Date: 2025-10-10 08:40:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9f3a1b7d8c2a'
down_revision = '62de3ab69c1b_add_api_keys_table'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        # Use batch operations for SQLite
        with op.batch_alter_table('requests') as batch_op:
            batch_op.add_column(sa.Column('fallback_attempts', sa.JSON(), nullable=True))
    else:
        op.add_column('requests', sa.Column('fallback_attempts', sa.JSON(), nullable=True))


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        with op.batch_alter_table('requests') as batch_op:
            batch_op.drop_column('fallback_attempts')
    else:
        op.drop_column('requests', 'fallback_attempts')
