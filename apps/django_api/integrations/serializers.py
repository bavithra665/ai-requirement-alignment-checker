from rest_framework import serializers
from .models import JiraStory, PullRequest, CodeArtifact

class JiraStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JiraStory
        fields = '__all__'

class PullRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PullRequest
        fields = '__all__'

class CodeArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeArtifact
        fields = '__all__'
