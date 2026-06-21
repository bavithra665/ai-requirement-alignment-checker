from rest_framework import serializers
from .models import AlignmentResult


class AlignmentResultSerializer(serializers.ModelSerializer):
    # Human-readable chain labels derived from related objects
    requirement_title = serializers.SerializerMethodField()
    jira_story_title = serializers.SerializerMethodField()
    pull_request_title = serializers.SerializerMethodField()
    code_artifact_name = serializers.SerializerMethodField()
    code_artifact_path = serializers.SerializerMethodField()

    class Meta:
        model = AlignmentResult
        fields = '__all__'

    def get_requirement_title(self, obj):
        """Return the requirement title from the linked RequirementVersion -> Requirement."""
        try:
            if obj.requirement_version and obj.requirement_version.requirement:
                req = obj.requirement_version.requirement
                return req.title
        except Exception:
            pass
        return None

    def get_jira_story_title(self, obj):
        """Return 'HEM-1: Title' format from the linked JiraStory."""
        try:
            if obj.jira_story:
                return f"{obj.jira_story.jira_issue_key}: {obj.jira_story.title}"
        except Exception:
            pass
        return None

    def get_pull_request_title(self, obj):
        """Return 'PR #1: Title' format from the linked PullRequest."""
        try:
            if obj.pull_request:
                return f"PR #{obj.pull_request.pr_number}: {obj.pull_request.title}"
        except Exception:
            pass
        return None

    def get_code_artifact_name(self, obj):
        """Return '[Type] Name in file_path' format from the linked CodeArtifact."""
        try:
            if obj.code_artifact:
                return f"[{obj.code_artifact.artifact_type}] {obj.code_artifact.artifact_name}"
        except Exception:
            pass
        return None

    def get_code_artifact_path(self, obj):
        """Return the file path of the linked CodeArtifact."""
        try:
            if obj.code_artifact:
                return obj.code_artifact.file_path
        except Exception:
            pass
        return None
