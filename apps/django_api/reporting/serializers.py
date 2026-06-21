from rest_framework import serializers
from .models import MismatchReport

class MismatchReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MismatchReport
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'project', 'alignment_result']
