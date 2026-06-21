import uuid
from django.db import models
from django.conf import settings


class BaseIntegrationModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_updated"
    )

    class Meta:
        abstract = True


class JiraStory(BaseIntegrationModel):
    """Mirrors FastAPI JiraStory model exactly."""
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='jira_stories',
        db_column='project_id'
    )
    jira_issue_key = models.CharField(max_length=50, db_index=True)   # e.g. PROJ-123
    title = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=100)
    story_type = models.CharField(max_length=50, null=True, blank=True)  # Story, Epic, Task, Bug
    epic_key = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    assignee = models.CharField(max_length=255, null=True, blank=True)
    priority = models.CharField(max_length=50, null=True, blank=True)
    external_url = models.CharField(max_length=500, null=True, blank=True)
    labels = models.JSONField(default=list, blank=True)                  # list of string labels

    class Meta:
        db_table = 'jira_stories'
        unique_together = [('project', 'jira_issue_key')]

    def __str__(self):
        return f"{self.jira_issue_key}: {self.title}"


class PullRequest(BaseIntegrationModel):
    """Mirrors FastAPI PullRequest model exactly."""
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='pull_requests',
        db_column='project_id'
    )
    pr_number = models.IntegerField(db_index=True)
    repository_url = models.CharField(max_length=500)
    title = models.CharField(max_length=500)
    pr_description = models.TextField(null=True, blank=True)
    diff_content = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20)             # open, closed, merged

    # Extended metadata
    author = models.CharField(max_length=255, null=True, blank=True)
    branch = models.CharField(max_length=255, null=True, blank=True)      # head branch
    base_branch = models.CharField(max_length=255, null=True, blank=True) # target branch
    head_sha = models.CharField(max_length=100, null=True, blank=True)
    merged_at = models.DateTimeField(null=True, blank=True)
    changed_files = models.JSONField(default=list, blank=True)            # list of file paths

    class Meta:
        db_table = 'pull_requests'
        unique_together = [('project', 'pr_number')]

    def __str__(self):
        return f"PR #{self.pr_number}: {self.title}"


class CodeArtifact(BaseIntegrationModel):
    """
    Normalized store for extracted code symbols from Pull Request file changes.
    Each row = single function, class, or API endpoint from Python AST analysis.
    """
    ARTIFACT_TYPE_CHOICES = [
        ('Function', 'Function'),
        ('Class', 'Class'),
        ('API Endpoint', 'API Endpoint'),
        ('Entity', 'Entity'),
        ('Database Connection', 'Database Connection'),
        ('UI Layout', 'UI Layout'),
    ]

    pull_request = models.ForeignKey(
        PullRequest,
        on_delete=models.CASCADE,
        related_name='code_artifacts',
        db_column='pull_request_id'
    )
    artifact_type = models.CharField(max_length=20, choices=ARTIFACT_TYPE_CHOICES, db_index=True)
    artifact_name = models.CharField(max_length=500, db_index=True)  # e.g. "edit_invoice", "/invoice/edit"
    file_path = models.CharField(max_length=500)                      # e.g. "app/routes/invoice.py"
    artifact_metadata = models.JSONField(null=True, blank=True)       # line_number, http_method, args, decorators

    class Meta:
        db_table = 'code_artifacts'

    def __str__(self):
        return f"[{self.artifact_type}] {self.artifact_name} in {self.file_path}"
