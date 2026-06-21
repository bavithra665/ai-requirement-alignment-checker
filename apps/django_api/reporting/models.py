import uuid
from django.db import models
from django.conf import settings

class MismatchReport(models.Model):
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
        related_name='mismatch_reports',
        db_column='project_id'
    )
    alignment_result = models.ForeignKey(
        'alignment.AlignmentResult',
        on_delete=models.CASCADE,
        related_name='mismatch_reports',
        db_column='alignment_result_id'
    )
    
    mismatch_type = models.CharField(max_length=100) # missing_implementation, logic_error, etc
    description = models.TextField()
    suggested_fix = models.TextField(null=True, blank=True)
    
    status = models.CharField(max_length=50, default="Open")          # Open / Reviewed / Resolved
    severity = models.CharField(max_length=50, default="Medium")      # Critical / High / Medium / Low
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reviewed_mismatch_reports",
        db_column='reviewed_by_id'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'mismatch_reports'

    def __str__(self):
        return f"MismatchReport {self.id} - {self.mismatch_type}"
