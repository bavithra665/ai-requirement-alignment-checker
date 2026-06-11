"""reporting layer - extend mismatch_reports with review workflow fields

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-10 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── mismatch_reports: add reporting layer columns ────────────────────
    op.add_column('mismatch_reports', sa.Column('status', sa.String(), nullable=False, server_default='Open'))
    op.add_column('mismatch_reports', sa.Column('severity', sa.String(), nullable=False, server_default='Medium'))
    op.add_column('mismatch_reports', sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('mismatch_reports', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('mismatch_reports', sa.Column('resolution_notes', sa.Text(), nullable=True))

    # Foreign key constraint for reviewed_by_id → users.id
    op.create_foreign_key(
        'fk_mismatch_reports_reviewed_by',
        'mismatch_reports', 'users',
        ['reviewed_by_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_mismatch_reports_reviewed_by', 'mismatch_reports', type_='foreignkey')
    op.drop_column('mismatch_reports', 'resolution_notes')
    op.drop_column('mismatch_reports', 'reviewed_at')
    op.drop_column('mismatch_reports', 'reviewed_by_id')
    op.drop_column('mismatch_reports', 'severity')
    op.drop_column('mismatch_reports', 'status')
