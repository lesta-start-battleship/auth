"""Add device_logins table

Revision ID: f6af5f59ca20
Revises: 059e64aa403a
Create Date: 2025-07-04 13:05:49.957529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6af5f59ca20'
down_revision: Union[str, Sequence[str], None] = '059e64aa403a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('device_logins',
    sa.Column('device_code', sa.String(), nullable=False),
    sa.Column('user_code', sa.String(), nullable=False),
    sa.Column('cli_redirect_uri', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('device_code'),
    sa.UniqueConstraint('user_code')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('device_logins')
    # ### end Alembic commands ###
