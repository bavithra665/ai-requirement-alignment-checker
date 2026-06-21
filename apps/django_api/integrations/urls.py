from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JiraIntegrationViewSet, GitHubIntegrationViewSet

router = DefaultRouter()

# We map the viewsets manually to match the FastAPI routes as close as possible
urlpatterns = [
    path('jira/status', JiraIntegrationViewSet.as_view({'get': 'status'})),
    path('jira/projects/<uuid:project_id>/sync', JiraIntegrationViewSet.as_view({'post': 'sync'})),
    path('jira/projects/<uuid:project_id>/stories', JiraIntegrationViewSet.as_view({'get': 'stories'})),

    path('github/status', GitHubIntegrationViewSet.as_view({'get': 'status'})),
    path('github/projects/<uuid:project_id>/sync-prs', GitHubIntegrationViewSet.as_view({'post': 'sync_prs'})),
    path('github/projects/<uuid:project_id>/prs', GitHubIntegrationViewSet.as_view({'get': 'prs'})),
    path('github/prs/<uuid:pr_id>/extract-symbols', GitHubIntegrationViewSet.as_view({'post': 'extract_symbols'})),
    path('github/prs/<uuid:pr_id>/symbols', GitHubIntegrationViewSet.as_view({'get': 'symbols'})),
]
