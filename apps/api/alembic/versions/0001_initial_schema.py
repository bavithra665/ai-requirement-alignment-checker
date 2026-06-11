"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-06-09 22:36:29.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. users
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('role', sa.Enum('DEVELOPER', 'CLIENT', 'ADMIN', name='userrole'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. projects
    op.create_table('projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('client_name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('repository_url', sa.String(), nullable=True),
        sa.Column('jira_project_key', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='Draft'),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_created_at'), 'projects', ['created_at'], unique=False)
    op.create_index(op.f('ix_projects_created_by_id'), 'projects', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=False)
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)

    # 3. requirements
    op.create_table('requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requirements_created_at'), 'requirements', ['created_at'], unique=False)
    op.create_index(op.f('ix_requirements_created_by_id'), 'requirements', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_requirements_id'), 'requirements', ['id'], unique=False)
    op.create_index(op.f('ix_requirements_project_id'), 'requirements', ['project_id'], unique=False)

    # 4. requirement_versions
    op.create_table('requirement_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('change_summary', sa.String(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='Draft'),
        sa.Column('is_baseline', sa.Boolean(), nullable=False, server_default='false'),
        
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['requirement_id'], ['requirements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requirement_versions_created_at'), 'requirement_versions', ['created_at'], unique=False)
    op.create_index(op.f('ix_requirement_versions_created_by_id'), 'requirement_versions', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_requirement_versions_id'), 'requirement_versions', ['id'], unique=False)
    op.create_index(op.f('ix_requirement_versions_requirement_id'), 'requirement_versions', ['requirement_id'], unique=False)

    # 5. client_approvals
    op.create_table('client_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('requirement_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('comments', sa.String(), nullable=True),
        
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['requirement_version_id'], ['requirement_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_client_approvals_created_at'), 'client_approvals', ['created_at'], unique=False)
    op.create_index(op.f('ix_client_approvals_created_by_id'), 'client_approvals', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_client_approvals_id'), 'client_approvals', ['id'], unique=False)
    op.create_index(op.f('ix_client_approvals_requirement_version_id'), 'client_approvals', ['requirement_version_id'], unique=False)

    # 6. jira_stories
    op.create_table('jira_stories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('jira_issue_key', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jira_stories_created_at'), 'jira_stories', ['created_at'], unique=False)
    op.create_index(op.f('ix_jira_stories_created_by_id'), 'jira_stories', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_jira_stories_id'), 'jira_stories', ['id'], unique=False)
    op.create_index(op.f('ix_jira_stories_project_id'), 'jira_stories', ['project_id'], unique=False)
    op.create_index(op.f('ix_jira_stories_jira_issue_key'), 'jira_stories', ['jira_issue_key'], unique=False)

    # 7. pull_requests
    op.create_table('pull_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('repository_url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('diff_content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pull_requests_created_at'), 'pull_requests', ['created_at'], unique=False)
    op.create_index(op.f('ix_pull_requests_created_by_id'), 'pull_requests', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_pull_requests_id'), 'pull_requests', ['id'], unique=False)
    op.create_index(op.f('ix_pull_requests_project_id'), 'pull_requests', ['project_id'], unique=False)
    op.create_index(op.f('ix_pull_requests_pr_number'), 'pull_requests', ['pr_number'], unique=False)

    # 8. alignment_results
    op.create_table('alignment_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requirement_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('jira_story_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('pull_request_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requirement_version_id'], ['requirement_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['jira_story_id'], ['jira_stories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pull_request_id'], ['pull_requests.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alignment_results_created_at'), 'alignment_results', ['created_at'], unique=False)
    op.create_index(op.f('ix_alignment_results_created_by_id'), 'alignment_results', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_alignment_results_id'), 'alignment_results', ['id'], unique=False)
    op.create_index(op.f('ix_alignment_results_project_id'), 'alignment_results', ['project_id'], unique=False)
    op.create_index(op.f('ix_alignment_results_requirement_version_id'), 'alignment_results', ['requirement_version_id'], unique=False)
    op.create_index(op.f('ix_alignment_results_jira_story_id'), 'alignment_results', ['jira_story_id'], unique=False)
    op.create_index(op.f('ix_alignment_results_pull_request_id'), 'alignment_results', ['pull_request_id'], unique=False)

    # 9. mismatch_reports
    op.create_table('mismatch_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alignment_result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mismatch_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('suggested_fix', sa.Text(), nullable=True),
        
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['alignment_result_id'], ['alignment_results.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mismatch_reports_created_at'), 'mismatch_reports', ['created_at'], unique=False)
    op.create_index(op.f('ix_mismatch_reports_created_by_id'), 'mismatch_reports', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_mismatch_reports_id'), 'mismatch_reports', ['id'], unique=False)
    op.create_index(op.f('ix_mismatch_reports_project_id'), 'mismatch_reports', ['project_id'], unique=False)
    op.create_index(op.f('ix_mismatch_reports_alignment_result_id'), 'mismatch_reports', ['alignment_result_id'], unique=False)

def downgrade() -> None:
    op.drop_table('mismatch_reports')
    op.drop_table('alignment_results')
    op.drop_table('pull_requests')
    op.drop_table('jira_stories')
    op.drop_table('client_approvals')
    op.drop_table('requirement_versions')
    op.drop_table('requirements')
    op.drop_table('projects')
    op.drop_table('users')
    op.execute('DROP TYPE userrole;')
