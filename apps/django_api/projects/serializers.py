from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, Requirement, RequirementVersion, ClientApproval

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    status_reason = serializers.SerializerMethodField()
    client_user_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'client_name', 'client_email', 'client_user_id',
            'description', 'repository_url', 'jira_project_key',
            'owner_id', 'created_at', 'updated_at', 'status', 'status_reason'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_id', 'status', 'status_reason', 'client_user_id']

    def get_status(self, obj):
        reqs = obj.requirements.filter(is_deleted=False)
        if not reqs.exists():
            return "Draft"
            
        has_approved = False
        all_aligned = True
        has_any_alignment = False
        
        try:
            from alignment.models import AlignmentResult
        except ImportError:
            return "Draft"
            
        for req in reqs:
            approved_versions = req.versions.filter(status="Approved", is_deleted=False)
            if approved_versions.exists():
                has_approved = True
                for version in approved_versions:
                    alignments = AlignmentResult.objects.filter(requirement_version=version, is_deleted=False)
                    if not alignments.exists():
                        all_aligned = False
                    else:
                        for alignment in alignments:
                            has_any_alignment = True
                            if alignment.overall_alignment_score < 100:
                                all_aligned = False
                                
        if not has_approved:
            return "Draft"
            
        if has_any_alignment and all_aligned:
            return "Completed"
            
        return "In Progress"

    def get_status_reason(self, obj):
        status = self.get_status(obj)
        if status == "Draft":
            return "Awaiting BRD / requirement baseline"
        elif status == "Completed":
            return "All requirements fully aligned"
        else:
            return "Requirements being implemented"

    def validate(self, data):
        client_email = data.get('client_email')
        if client_email:
            try:
                client_user = User.objects.get(email=client_email)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"client_email": f"No user found with email '{client_email}'."}
                )
            if client_user.role != 'client':
                raise serializers.ValidationError(
                    {"client_email": f"User '{client_email}' is not a CLIENT user."}
                )
            data['client_user'] = client_user
        return data


class RequirementVersionSerializer(serializers.ModelSerializer):
    requirement_title = serializers.SerializerMethodField()

    class Meta:
        model = RequirementVersion
        fields = ['id', 'requirement_id', 'requirement_title', 'version_number', 'content', 'change_summary', 'ai_summary', 'status', 'is_baseline', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'requirement_id']

    def get_requirement_title(self, obj):
        try:
            return obj.requirement.title
        except Exception:
            return None


class RequirementSerializer(serializers.ModelSerializer):
    versions = RequirementVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Requirement
        fields = ['id', 'project_id', 'title', 'description', 'versions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'project_id']


class ClientApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientApproval
        fields = ['id', 'requirement_version_id', 'status', 'comments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'requirement_version_id']
