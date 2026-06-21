import uuid
from django.db import models
from django.conf import settings
from integrations.models import BaseIntegrationModel

class AlignmentResult(models.Model):
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

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='alignment_results',
        db_column='project_id'
    )
    requirement_version = models.ForeignKey(
        'projects.RequirementVersion',
        on_delete=models.CASCADE,
        related_name='alignment_results',
        db_column='requirement_version_id'
    )
    jira_story = models.ForeignKey(
        'integrations.JiraStory',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alignment_results',
        db_column='jira_story_id'
    )
    pull_request = models.ForeignKey(
        'integrations.PullRequest',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alignment_results',
        db_column='pull_request_id'
    )
    code_artifact = models.ForeignKey(
        'integrations.CodeArtifact',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alignment_results',
        db_column='code_artifact_id'
    )

    # Relationship scores
    requirement_jira_score = models.IntegerField(null=True, blank=True)
    jira_pr_score = models.IntegerField(null=True, blank=True)
    pr_artifact_score = models.IntegerField(null=True, blank=True)
    overall_alignment_score = models.IntegerField()
    
    alignment_status = models.CharField(max_length=50, default="Aligned")
    confidence = models.IntegerField(default=100)
    explanation = models.TextField(null=True, blank=True)
    
    # Legacy compatibility fields mapping to the new naming scheme
    score = models.IntegerField()
    summary = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'alignment_results'

    def __str__(self):
        return f"AlignmentResult {self.id} - {self.alignment_status}"
