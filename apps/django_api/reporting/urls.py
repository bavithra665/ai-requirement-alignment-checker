from django.urls import path
from .views import ReportingViewSet

urlpatterns = [
    path('reporting/executive-summary/<uuid:project_id>', ReportingViewSet.as_view({'get': 'executive_summary'})),
    path('reporting/risk-dashboard/<uuid:project_id>', ReportingViewSet.as_view({'get': 'risk_dashboard'})),
    path('reporting/mismatches/<uuid:project_id>', ReportingViewSet.as_view({'get': 'list_mismatches'})),
    path('reporting/mismatches/generate/<uuid:project_id>', ReportingViewSet.as_view({'post': 'generate_mismatches'})),
    path('reporting/mismatch/<uuid:pk>/resolve', ReportingViewSet.as_view({'patch': 'resolve_mismatch'})),
    
    # CSV Exports (as referenced in frontend api-client)
    path('reports/export/mismatches/<uuid:project_id>', ReportingViewSet.as_view({'get': 'export_mismatches_csv'})),
    path('reports/export/executive/<uuid:project_id>', ReportingViewSet.as_view({'get': 'export_executive_csv'})),
]
