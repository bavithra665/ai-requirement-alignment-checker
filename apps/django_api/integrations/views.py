from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import JiraStory, PullRequest, CodeArtifact
from .serializers import JiraStorySerializer, PullRequestSerializer, CodeArtifactSerializer
from projects.models import Project
from .services import jira_service, github_service, code_extraction_service

class JiraIntegrationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def status(self, request):
        return Response(jira_service.get_status())

    @action(detail=False, methods=['post'], url_path='projects/(?P<project_id>[^/.]+)/sync')
    def sync(self, request, project_id=None):
        if not jira_service.is_configured():
            return Response({"detail": "Jira is not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        project = get_object_or_404(Project, id=project_id)
        if not project.jira_project_key:
            return Response({"detail": "Project does not have a Jira Project Key configured."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = jira_service.sync_project_stories(project, request.user)
            return Response({"message": "Sync completed successfully", **result})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='projects/(?P<project_id>[^/.]+)/stories')
    def stories(self, request, project_id=None):
        stories = JiraStory.objects.filter(project_id=project_id, is_deleted=False).order_by('created_at')
        serializer = JiraStorySerializer(stories, many=True)
        return Response(serializer.data)


class GitHubIntegrationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def status(self, request):
        return Response(github_service.get_status())

    @action(detail=False, methods=['post'], url_path='projects/(?P<project_id>[^/.]+)/sync-prs')
    def sync_prs(self, request, project_id=None):
        state = request.query_params.get('state', 'all')
        if not github_service.is_configured():
            return Response({"detail": "GitHub is not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        project = get_object_or_404(Project, id=project_id)
        if not project.repository_url:
            return Response({"detail": "Project does not have a Repository URL configured."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = github_service.sync_pull_requests(project, request.user, state)
            return Response({"message": "PR sync completed successfully", **result})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='projects/(?P<project_id>[^/.]+)/prs')
    def prs(self, request, project_id=None):
        prs = PullRequest.objects.filter(project_id=project_id, is_deleted=False).order_by('-pr_number')
        serializer = PullRequestSerializer(prs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='prs/(?P<pr_id>[^/.]+)/extract-symbols')
    def extract_symbols(self, request, pr_id=None):
        if not github_service.is_configured():
            return Response({"detail": "GitHub token not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        pr = get_object_or_404(PullRequest, id=pr_id)
        if not pr.changed_files:
            return Response({"message": "No changed files found on this PR.", "processed_files": 0})
        
        try:
            result = code_extraction_service.process_pr_files(pr, request.user)
            return Response({"message": "Extraction completed", **result})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='prs/(?P<pr_id>[^/.]+)/symbols')
    def symbols(self, request, pr_id=None):
        artifact_type = request.query_params.get('artifact_type')
        artifacts = CodeArtifact.objects.filter(pull_request_id=pr_id)
        if artifact_type:
            artifacts = artifacts.filter(artifact_type=artifact_type)
        serializer = CodeArtifactSerializer(artifacts, many=True)
        return Response(serializer.data)
