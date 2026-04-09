"""Add placement_policies table

Revision ID: simple_add_placement_policies
Revises: aa642a79b7ac
Create Date: 2026-04-10 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'simple_add_placement_policies'
down_revision = 'aa642a79b7ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('placement_policies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('max_offers_per_student', sa.Integer(), nullable=True),
    sa.Column('allow_multiple_offers', sa.Boolean(), nullable=True),
    sa.Column('dream_company_ctc_threshold', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('is_active', name='one_active_policy')
    )
    op.create_index(op.f('ix_placement_policies_id'), 'placement_policies', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_placement_policies_id'), table_name='placement_policies')
    op.drop_table('placement_policies')
