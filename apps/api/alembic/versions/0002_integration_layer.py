"""integration layer - extend jira_stories, pull_requests, add code_artifacts

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-10 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── jira_stories: add new integration columns ──────────────────────────
    op.add_column('jira_stories', sa.Column('story_type', sa.String(), nullable=True))
    op.add_column('jira_stories', sa.Column('epic_key', sa.String(), nullable=True))
    op.add_column('jira_stories', sa.Column('assignee', sa.String(), nullable=True))
    op.add_column('jira_stories', sa.Column('priority', sa.String(), nullable=True))
    op.add_column('jira_stories', sa.Column('external_url', sa.String(), nullable=True))
    op.add_column('jira_stories', sa.Column('labels', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_index(op.f('ix_jira_stories_epic_key'), 'jira_stories', ['epic_key'], unique=False)

    # ── pull_requests: add new integration columns ──────────────────────────
    op.add_column('pull_requests', sa.Column('pr_description', sa.Text(), nullable=True))
    op.add_column('pull_requests', sa.Column('author', sa.String(), nullable=True))
    op.add_column('pull_requests', sa.Column('branch', sa.String(), nullable=True))
    op.add_column('pull_requests', sa.Column('base_branch', sa.String(), nullable=True))
    op.add_column('pull_requests', sa.Column('head_sha', sa.String(), nullable=True))
    op.add_column('pull_requests', sa.Column('merged_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('pull_requests', sa.Column('changed_files', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # ── code_artifacts: new normalized extraction table ─────────────────────
    op.create_table(
        'code_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column('pull_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'artifact_type',
            sa.Enum('Function', 'Class', 'API Endpoint', name='artifacttype'),
            nullable=False
        ),
        sa.Column('artifact_name', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('artifact_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pull_request_id'], ['pull_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_code_artifacts_id'), 'code_artifacts', ['id'], unique=False)
    op.create_index(op.f('ix_code_artifacts_pull_request_id'), 'code_artifacts', ['pull_request_id'], unique=False)
    op.create_index(op.f('ix_code_artifacts_artifact_type'), 'code_artifacts', ['artifact_type'], unique=False)
    op.create_index(op.f('ix_code_artifacts_artifact_name'), 'code_artifacts', ['artifact_name'], unique=False)
    op.create_index(op.f('ix_code_artifacts_created_at'), 'code_artifacts', ['created_at'], unique=False)
    op.create_index(op.f('ix_code_artifacts_created_by_id'), 'code_artifacts', ['created_by_id'], unique=False)


def downgrade() -> None:
    op.drop_table('code_artifacts')
    op.execute('DROP TYPE IF EXISTS artifacttype;')

    # pull_requests columns
    op.drop_column('pull_requests', 'changed_files')
    op.drop_column('pull_requests', 'merged_at')
    op.drop_column('pull_requests', 'head_sha')
    op.drop_column('pull_requests', 'base_branch')
    op.drop_column('pull_requests', 'branch')
    op.drop_column('pull_requests', 'author')
    op.drop_column('pull_requests', 'pr_description')

    # jira_stories columns
    op.drop_index(op.f('ix_jira_stories_epic_key'), table_name='jira_stories')
    op.drop_column('jira_stories', 'labels')
    op.drop_column('jira_stories', 'external_url')
    op.drop_column('jira_stories', 'priority')
    op.drop_column('jira_stories', 'assignee')
    op.drop_column('jira_stories', 'epic_key')
    op.drop_column('jira_stories', 'story_type')
