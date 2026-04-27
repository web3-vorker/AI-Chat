"""Fix user_id type in chats table

Revision ID: fix_user_id_type
Revises: 9553e64805ec
Create Date: 2026-04-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fix_user_id_type'
down_revision: Union[str, Sequence[str], None] = '9553e64805ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert user_id from VARCHAR to INTEGER
    op.execute('ALTER TABLE chats ALTER COLUMN user_id TYPE INTEGER USING user_id::integer')


def downgrade() -> None:
    op.execute('ALTER TABLE chats ALTER COLUMN user_id TYPE VARCHAR(255)')