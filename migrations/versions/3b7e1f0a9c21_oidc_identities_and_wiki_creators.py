"""OIDC sign-in: user_identities table and users.can_create_wikis

Revision ID: 3b7e1f0a9c21
Revises: 2c56258041a7
Create Date: 2026-10-10 17:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '3b7e1f0a9c21'
down_revision = '2c56258041a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user_identities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('issuer', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('issuer', 'subject', name='uq_user_identities_issuer_subject'),
    )
    op.create_index('ix_user_identities_user_id', 'user_identities', ['user_id'])
    op.add_column('users', sa.Column('can_create_wikis', sa.Boolean(), nullable=False,
                                     server_default=sa.false()))


def downgrade():
    op.drop_column('users', 'can_create_wikis')
    op.drop_index('ix_user_identities_user_id', table_name='user_identities')
    op.drop_table('user_identities')
