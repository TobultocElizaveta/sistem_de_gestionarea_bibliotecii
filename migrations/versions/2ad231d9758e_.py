"""empty message

Revision ID: 2ad231d9758e
Revises: 9bd50a76fba0
Create Date: 2023-08-26 00:18:50.058027

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2ad231d9758e'
down_revision = '9bd50a76fba0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('member', schema=None) as batch_op:
        batch_op.add_column(sa.Column('outstanding_debt', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('member', schema=None) as batch_op:
        batch_op.drop_column('outstanding_debt')

    # ### end Alembic commands ###
