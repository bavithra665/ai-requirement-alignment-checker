from django.urls import path
from .views import AlignmentViewSet

urlpatterns = [
    path('alignment/index/<uuid:project_id>', AlignmentViewSet.as_view({'post': 'index_project'})),
    path('alignment/run/<uuid:project_id>', AlignmentViewSet.as_view({'post': 'run_alignment'})),
    path('alignment/results/<uuid:project_id>', AlignmentViewSet.as_view({'get': 'results'})),
    path('alignment/result/<uuid:result_id>', AlignmentViewSet.as_view({'get': 'result_detail'})),
]
