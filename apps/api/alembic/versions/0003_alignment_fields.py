"""alignment fields - extend alignment_results with relationship-aware scoring

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-10 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── alignment_results: add new columns ──────────────────────────
    op.add_column('alignment_results', sa.Column('code_artifact_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('alignment_results', sa.Column('requirement_jira_score', sa.Integer(), nullable=True))
    op.add_column('alignment_results', sa.Column('jira_pr_score', sa.Integer(), nullable=True))
    op.add_column('alignment_results', sa.Column('pr_artifact_score', sa.Integer(), nullable=True))
    op.add_column('alignment_results', sa.Column('overall_alignment_score', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('alignment_results', sa.Column('alignment_status', sa.String(), nullable=False, server_default='Aligned'))
    op.add_column('alignment_results', sa.Column('confidence', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('alignment_results', sa.Column('explanation', sa.Text(), nullable=True))

    # Foreign key constraint
    op.create_foreign_key(
        'fk_alignment_results_code_artifacts',
        'alignment_results', 'code_artifacts',
        ['code_artifact_id'], ['id'],
        ondelete='SET NULL'
    )

    op.create_index(op.f('ix_alignment_results_code_artifact_id'), 'alignment_results', ['code_artifact_id'], unique=False)


def downgrade() -> None:
    op.drop_constraint('fk_alignment_results_code_artifacts', 'alignment_results', type_='foreignkey')
    op.drop_index(op.f('ix_alignment_results_code_artifact_id'), table_name='alignment_results')
    
    op.drop_column('alignment_results', 'explanation')
    op.drop_column('alignment_results', 'confidence')
    op.drop_column('alignment_results', 'alignment_status')
    op.drop_column('alignment_results', 'overall_alignment_score')
    op.drop_column('alignment_results', 'pr_artifact_score')
    op.drop_column('alignment_results', 'jira_pr_score')
    op.drop_column('alignment_results', 'requirement_jira_score')
    op.drop_column('alignment_results', 'code_artifact_id')
