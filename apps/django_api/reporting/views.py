from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import MismatchReport
from .serializers import MismatchReportSerializer
from .services import reporting_service

class ReportingViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='executive-summary/(?P<project_id>[^/.]+)')
    def executive_summary(self, request, project_id=None):
        try:
            summary = reporting_service.get_executive_summary(project_id)
            return Response(summary)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='risk-dashboard/(?P<project_id>[^/.]+)')
    def risk_dashboard(self, request, project_id=None):
        try:
            dashboard = reporting_service.get_risk_dashboard(project_id)
            return Response(dashboard)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='mismatches/(?P<project_id>[^/.]+)')
    def list_mismatches(self, request, project_id=None):
        mismatches = MismatchReport.objects.filter(project_id=project_id, is_deleted=False).order_by('-created_at')
        
        status_filter = request.query_params.get('status')
        if status_filter:
            mismatches = mismatches.filter(status=status_filter)
            
        severity_filter = request.query_params.get('severity')
        if severity_filter:
            mismatches = mismatches.filter(severity=severity_filter)
            
        serializer = MismatchReportSerializer(mismatches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='mismatches/generate/(?P<project_id>[^/.]+)')
    def generate_mismatches(self, request, project_id=None):
        try:
            count = reporting_service.generate_mismatch_reports(project_id, request.user)
            return Response({"message": f"Generated {count} mismatch reports.", "generated_count": count})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'], url_path='resolve')
    def resolve_mismatch(self, request, pk=None):
        mismatch = get_object_or_404(MismatchReport, id=pk, is_deleted=False)
        
        # Determine if it's being resolved
        new_status = request.data.get('status')
        resolution_notes = request.data.get('resolution_notes')
        
        if new_status:
            mismatch.status = new_status
            if new_status == 'Resolved':
                mismatch.reviewed_by = request.user
                mismatch.reviewed_at = timezone.now()
        
        if resolution_notes:
            mismatch.resolution_notes = resolution_notes
            
        mismatch.save()
        serializer = MismatchReportSerializer(mismatch)
        return Response(serializer.data)
