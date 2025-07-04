"""columns name and surname changed to nulllable=True and changed created_at type to datetime in tables UserCurrency and UserBase

Revision ID: d00c045698b7
Revises: 9f80f56263de
Create Date: 2025-06-30 12:32:21.378147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd00c045698b7'
down_revision: Union[str, Sequence[str], None] = '9f80f56263de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(
        """
        ALTER TABLE user_currencies
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING created_at::timestamp without time zone
        """
    )
    op.alter_column('users', 'name',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('users', 'surname',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING created_at::timestamp without time zone
        """
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'created_at',
               existing_type=sa.DateTime(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.alter_column('users', 'surname',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('users', 'name',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('user_currencies', 'created_at',
               existing_type=sa.DateTime(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    # ### end Alembic commands ###
