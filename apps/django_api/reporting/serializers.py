from rest_framework import serializers
from .models import MismatchReport

class MismatchReportSerializer(serializers.ModelSerializer):
    project_id = serializers.UUIDField(source='project.id', read_only=True)
    alignment_result_id = serializers.UUIDField(source='alignment_result.id', read_only=True)
    reviewed_by_id = serializers.UUIDField(source='reviewed_by.id', read_only=True, allow_null=True)
    requirement_title = serializers.SerializerMethodField()
    
    class Meta:
        model = MismatchReport
        fields = [
            'id', 'project_id', 'alignment_result_id', 'requirement_title',
            'mismatch_type', 'description', 'suggested_fix',
            'status', 'severity',
            'reviewed_by_id', 'reviewed_at', 'resolution_notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'project_id', 'alignment_result_id', 'reviewed_by_id']

    def get_requirement_title(self, obj):
        try:
            return obj.alignment_result.requirement_version.requirement.title
        except AttributeError:
            return None
