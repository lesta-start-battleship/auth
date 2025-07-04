"""add balance table and user relationship

Revision ID: fd11c14d3a0e
Revises: c1cae8f326dc
Create Date: 2025-06-29 19:43:36.326624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd11c14d3a0e'
down_revision: Union[str, Sequence[str], None] = 'c1cae8f326dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_enum = sa.Enum('ADMINISTRATOR', 'MODERATOR', 'USER', name='role_enum')
    role_enum.create(op.get_bind(), checkfirst=True)

    op.execute("ALTER TABLE users ALTER COLUMN role TYPE role_enum USING role::role_enum")

    op.create_table(
        'balance',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('silver', sa.Integer(), nullable=False),
        sa.Column('gold', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    op.add_column('users', sa.Column('username', sa.String(length=50), nullable=False))
    op.add_column('users', sa.Column('created_at', sa.String(), nullable=False))
    op.alter_column('users', 'h_password',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.create_unique_constraint(None, 'users', ['username'])
    op.drop_column('users', 'datetime')
    op.drop_column('users', 'gold')
    op.drop_column('users', 'silver')

def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('silver', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('gold', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('datetime', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'users', type_='unique')
    op.alter_column('users', 'role',
               existing_type=sa.Enum('ADMINISTRATOR', 'MODERATOR', 'USER', name='role_enum'),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.alter_column('users', 'h_password',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'username')
    op.drop_table('balance')
    # ### end Alembic commands ###
