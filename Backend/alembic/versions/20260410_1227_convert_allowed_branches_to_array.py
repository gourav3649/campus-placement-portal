"""Convert allowed_branches from TEXT to ARRAY

Revision ID: convert_allowed_branches_array
Revises: simple_add_placement_policies
Create Date: 2026-04-10 12:27:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'convert_allowed_branches_array'
down_revision = 'simple_add_placement_policies'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert text column (containing JSON strings) to ARRAY(String)
    # The current data is stored as text like '["CS", "IT"]'
    # This needs to be converted to actual PostgreSQL array
    op.alter_column(
        'jobs',
        'allowed_branches',
        type_=postgresql.ARRAY(sa.String()),
        postgresql_using="""
        CASE 
            WHEN allowed_branches IS NULL THEN NULL::text[]
            WHEN allowed_branches = '' THEN NULL::text[]
            ELSE string_to_array(
                TRIM(
                    TRIM(allowed_branches, '[]') , '"'
                ), 
                '","'
            )
        END
        """
    )


def downgrade() -> None:
    # Convert back to TEXT
    op.alter_column(
        'jobs',
        'allowed_branches',
        type_=sa.Text()
    )
