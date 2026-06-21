from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Project, Requirement, RequirementVersion, ClientApproval
from .serializers import ProjectSerializer, RequirementSerializer, RequirementVersionSerializer, ClientApprovalSerializer
import uuid

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return Project.objects.filter(client_user=user, is_deleted=False)
        return Project.objects.filter(is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'], url_path='upload-brd')
    def upload_brd(self, request, pk=None):
        import tempfile
        import os
        from django.core.files.storage import default_storage
        from .services import extraction_service, ai_service

        project = self.get_object()
        file = request.FILES.get('file')
        if not file:
            return Response({"detail": "File not provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        filename = file.name.lower()
        if not filename.endswith(('.pdf', '.docx')):
            return Response({"detail": "Only PDF and DOCX files are supported."}, status=status.HTTP_400_BAD_REQUEST)

        # Securely save uploaded file
        file_path = default_storage.save(f'tmp/{file.name}', file)
        full_file_path = default_storage.path(file_path)

        try:
            # 1. Parse File
            if filename.endswith('.pdf'):
                extracted_requirements = extraction_service.parse_pdf(full_file_path)
            else:
                extracted_requirements = extraction_service.parse_docx(full_file_path)

            if not extracted_requirements:
                return Response({"detail": "No extractable requirements found in document."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Generate Single Executive Summary for the entire document
            full_document_text = "\n\n".join(extracted_requirements)
            executive_summary = ai_service.generate_executive_summary(full_document_text)

            # 3. Create Requirements and Versions
            Requirement.objects.filter(project=project).update(is_deleted=True)
            RequirementVersion.objects.filter(requirement__project=project).update(is_deleted=True)
            created_count = 0
            for text in extracted_requirements:
                req = Requirement.objects.create(
                    project=project,
                    title=text[:100] + ("..." if len(text) > 100 else ""),
                    created_by=request.user
                )
                # Store the single executive summary on each RequirementVersion
                RequirementVersion.objects.create(
                    requirement=req,
                    version_number=1,
                    content=text,
                    ai_summary=executive_summary,
                    created_by=request.user
                )
                created_count += 1

            return Response({
                "message": "BRD uploaded and parsed successfully.", 
                "requirements_extracted": created_count
            })
        finally:
            # Cleanup temp file
            if os.path.exists(full_file_path):
                os.remove(full_file_path)

class RequirementViewSet(viewsets.ModelViewSet):
    serializer_class = RequirementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Requirement.objects.filter(is_deleted=False)
    
    @action(detail=False, methods=['get'], url_path='project/(?P<project_id>[^/.]+)')
    def project_requirements(self, request, project_id=None):
        versions = RequirementVersion.objects.filter(requirement__project_id=project_id, is_deleted=False).order_by('requirement__title')
        serializer = RequirementVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='approvals')
    def all_approvals(self, request):
        versions = RequirementVersion.objects.filter(is_deleted=False).order_by('requirement__title')
        
        results = []
        for v in versions:
            # Map Django status to frontend status
            frontend_status = "pending"
            if v.status == "Approved":
                frontend_status = "approved"
            elif v.status == "Changes Requested":
                frontend_status = "requested_changes"
            elif v.status == "Rejected":
                frontend_status = "rejected"
            elif v.status == "Draft":
                frontend_status = "pending"
                
            approval = v.approvals.order_by('-created_at').first()
            comment = approval.comments if approval else ""
            client_name = v.requirement.project.client_name or "Internal"
            
            results.append({
                "id": str(v.id),
                "title": f"{v.requirement.title} (v{v.version_number}.0)",
                "status": frontend_status,
                "clientName": client_name,
                "comment": comment,
                "createdAt": v.created_at.isoformat(),
            })
            
        return Response(results)

class ClientApprovalViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='projects/(?P<project_id>[^/.]+)/requirement-versions/(?P<version_id>[^/.]+)/approve')
    def approve(self, request, project_id=None, version_id=None):
        user = request.user
        if user.role != 'client':
            return Response({"detail": "Only clients can approve."}, status=status.HTTP_403_FORBIDDEN)
            
        version = RequirementVersion.objects.filter(id=version_id, requirement__project_id=project_id).first()
        if not version:
            return Response({"detail": "Requirement version not found."}, status=status.HTTP_404_NOT_FOUND)
            
        approval, created = ClientApproval.objects.get_or_create(
            requirement_version=version,
            defaults={'status': 'approved', 'comments': request.data.get('comment', 'Approved by client')}
        )
        if not created:
            approval.status = 'approved'
            approval.save()
            
        version.status = 'Approved'
        version.save()
        return Response(RequirementVersionSerializer(version).data)

    @action(detail=False, methods=['post'], url_path='projects/(?P<project_id>[^/.]+)/requirement-versions/(?P<version_id>[^/.]+)/reject')
    def reject(self, request, project_id=None, version_id=None):
        user = request.user
        if user.role != 'client':
            return Response({"detail": "Only clients can reject."}, status=status.HTTP_403_FORBIDDEN)
            
        version = RequirementVersion.objects.filter(id=version_id, requirement__project_id=project_id).first()
        if not version:
            return Response({"detail": "Requirement version not found."}, status=status.HTTP_404_NOT_FOUND)
            
        comment = request.data.get('comment', 'Client requested changes')
        approval, created = ClientApproval.objects.get_or_create(
            requirement_version=version,
            defaults={'status': 'rejected', 'comments': comment}
        )
        if not created:
            approval.status = 'rejected'
            approval.comments = comment
            approval.save()
            
        version.status = 'Changes Requested'
        version.save()
        return Response(RequirementVersionSerializer(version).data)


class ClientProjectViewSet(viewsets.ViewSet):
    """Returns projects where the logged-in user is the linked client_user."""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        if request.user.role != 'client':
            return Response(
                {"detail": "Only client users can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN
            )
        projects = Project.objects.filter(client_user=request.user, is_deleted=False)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    def requirement_versions(self, request, pk=None):
        if request.user.role != 'client':
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        project = Project.objects.filter(id=pk, client_user=request.user).first()
        if not project:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
            
        versions = RequirementVersion.objects.filter(requirement__project=project, is_deleted=False).select_related('requirement').order_by('requirement__title')
        serializer = RequirementVersionSerializer(versions, many=True)
        return Response(serializer.data)
