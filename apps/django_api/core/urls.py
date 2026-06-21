from django.contrib import admin
from django.urls import path, include
from authentication.views import CookieTokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/auth/token/refresh', CookieTokenRefreshView.as_view(), name='token-refresh'),

    # API v1 routing
    # NOTE: Keeping all app URLConfs mounted under the same /api/v1/ prefix.
    path('api/v1/', include('projects.urls')),
    path('api/v1/', include('integrations.urls')),
    path('api/v1/', include('alignment.urls')),
    path('api/v1/', include('reporting.urls')),

    # Safety net: in case a running server instance has a different ROOT_URLCONF,
    # explicitly expose client requirement versions under /api/v1/... as used by the frontend.
    path(
        'api/v1/client/projects/<uuid:pk>/requirement-versions',
        include('projects.urls'),
    ),
]

