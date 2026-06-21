from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, RequirementViewSet, ClientApprovalViewSet, ClientProjectViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'requirements', RequirementViewSet, basename='requirement')

urlpatterns = [
    path('', include(router.urls)),
    # Client project list (projects where client_user == request.user)
    path('client/projects', ClientProjectViewSet.as_view({'get': 'list'})),
    path('client/projects/<uuid:pk>/requirement-versions', ClientProjectViewSet.as_view({'get': 'requirement_versions'})),
    # Client approval/reject actions
    path('client/projects/<uuid:project_id>/requirement-versions/<uuid:version_id>/approve', ClientApprovalViewSet.as_view({'post': 'approve'})),
    path('client/projects/<uuid:project_id>/requirement-versions/<uuid:version_id>/reject', ClientApprovalViewSet.as_view({'post': 'reject'})),
]
