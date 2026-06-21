from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync

from .models import AlignmentResult
from .serializers import AlignmentResultSerializer
from projects.models import Project
from .services import alignment_engine

class AlignmentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='index/(?P<project_id>[^/.]+)')
    def index_project(self, request, project_id=None):
        project = get_object_or_404(Project, id=project_id)
        try:
            counts = alignment_engine.index_project(project_id)
            return Response({"message": "Successfully indexed project artifacts.", "indexed_counts": counts})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='run/(?P<project_id>[^/.]+)')
    def run_alignment(self, request, project_id=None):
        project = get_object_or_404(Project, id=project_id)
        try:
            results = async_to_sync(alignment_engine.run_alignment)(project.id, request.user)
            return Response({
                "message": "Alignment analysis completed successfully",
                "results_generated": len(results)
            })
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='results/(?P<project_id>[^/.]+)')
    def results(self, request, project_id=None):
        results = AlignmentResult.objects.filter(
            project_id=project_id, is_deleted=False
        ).select_related(
            'requirement_version',
            'requirement_version__requirement',
            'jira_story',
            'pull_request',
            'code_artifact',
        ).order_by('requirement_version__requirement__title')
        serializer = AlignmentResultSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='result/(?P<result_id>[^/.]+)')
    def result_detail(self, request, result_id=None):
        result = get_object_or_404(
            AlignmentResult.objects.select_related(
                'requirement_version',
                'requirement_version__requirement',
                'jira_story',
                'pull_request',
                'code_artifact',
            ),
            id=result_id,
            is_deleted=False,
        )
        serializer = AlignmentResultSerializer(result)
        return Response(serializer.data)
