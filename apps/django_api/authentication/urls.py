from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register_view, name='auth-register'),
    path('login', views.login_view, name='auth-login'),
    path('logout', views.logout_view, name='auth-logout'),
    path('me', views.me_view, name='auth-me'),
    path('debug-users', views.debug_users_view, name='auth-debug-users'),
]
