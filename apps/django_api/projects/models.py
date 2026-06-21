import uuid
from django.db import models
from django.conf import settings

class BaseDomainModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated"
    )

    class Meta:
        abstract = True


class Project(BaseDomainModel):
    name = models.CharField(max_length=255, db_index=True)
    client_name = models.CharField(max_length=255, null=True, blank=True)
    client_email = models.EmailField(null=True, blank=True)
    client_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_projects'
    )
    description = models.TextField(null=True, blank=True)
    repository_url = models.CharField(max_length=255, null=True, blank=True)
    jira_project_key = models.CharField(max_length=50, null=True, blank=True)
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.RESTRICT, 
        related_name='projects'
    )

    class Meta:
        db_table = 'projects'

    def __str__(self):
        return self.name


class Requirement(BaseDomainModel):
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='requirements'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'requirements'

    def __str__(self):
        return f"{self.project.name} - {self.title}"


class RequirementVersion(BaseDomainModel):
    requirement = models.ForeignKey(
        Requirement, 
        on_delete=models.CASCADE, 
        related_name='versions'
    )
    version_number = models.IntegerField()
    content = models.TextField()
    change_summary = models.CharField(max_length=500, null=True, blank=True)
    ai_summary = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default="Draft")
    is_baseline = models.BooleanField(default=False)

    class Meta:
        db_table = 'requirement_versions'

    def __str__(self):
        return f"{self.requirement.title} (v{self.version_number})"


class ClientApproval(BaseDomainModel):
    requirement_version = models.ForeignKey(
        RequirementVersion, 
        on_delete=models.CASCADE, 
        related_name='approvals'
    )
    status = models.CharField(max_length=50)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'client_approvals'

    def __str__(self):
        return f"Approval for {self.requirement_version} - {self.status}"
