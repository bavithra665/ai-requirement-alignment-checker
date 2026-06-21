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
        return "Draft"

    def get_status_reason(self, obj):
        return "No approved baseline requirements exist"

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
    class Meta:
        model = RequirementVersion
        fields = ['id', 'requirement_id', 'version_number', 'content', 'change_summary', 'ai_summary', 'status', 'is_baseline', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'requirement_id']


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
